
import numpy as np
import cv2
import os
import matplotlib.pyplot as plt
from scipy.sparse import csr_matrix, diags
from scipy.sparse.linalg import eigsh

class KMeansFromScratch:
    def __init__(self, n_clusters, max_iter=300, random_state=42):
        self.n_clusters = n_clusters
        self.max_iter = max_iter
        self.random_state = random_state
        self.centers = None

    def initialize_centers(self, X):
        np.random.seed(self.random_state)
        random_idx = np.random.permutation(X.shape[0])
        self.centers = X[random_idx[:self.n_clusters]]

    def compute_distance(self, X, center):
        return np.linalg.norm(X - center, axis=1)

    def assign_labels(self, X):
        distances = np.array([self.compute_distance(X, center) for center in self.centers]).T
        return np.argmin(distances, axis=1)

    def update_centers(self, X, labels):
        new_centers = np.array([X[labels == i].mean(axis=0) for i in range(self.n_clusters)])
        return new_centers

    def fit(self, X):
        self.initialize_centers(X)
        for i in range(self.max_iter):
            labels = self.assign_labels(X)
            new_centers = self.update_centers(X, labels)
            if np.allclose(self.centers, new_centers, atol=1e-4):
                break
            self.centers = new_centers
        self.labels_ = labels

def load_images_from_folder(folder):
    images = []
    try:
        file_list = os.listdir(folder)
    except FileNotFoundError:
        print(f"Error: The directory {folder} does not exist.")
        return images
    for filename in file_list:
        img = cv2.imread(os.path.join(folder, filename))
        if img is not None:
            images.append(img)
        else:
            print(f"Warning: {filename} could not be read as an image.")
    return images

def display_images(images, titles, colormaps):
    assert len(images) == len(titles) == len(colormaps), "Each image must have a corresponding title and colormap."
    n = len(images)
    plt.figure(figsize=(15, 5 * n))
    for i in range(len(images)):
        plt.subplot(1, len(images), i+1)
        plt.imshow(images[i], cmap=colormaps[i])
        plt.title(titles[i])
        plt.axis('off')
    plt.tight_layout()
    plt.show()

def segment_image(image, n_clusters):
    kmeans = KMeansFromScratch(n_clusters=n_clusters, max_iter=300)
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    data = gray.reshape((-1, 1))
    kmeans.fit(data)
    segmented_image = kmeans.labels_.reshape(gray.shape)
    return segmented_image

def ratio_cut_clustering(image, num_clusters):
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    rows, cols = gray.shape
    size = rows * cols
    data = []
    row_ind = []
    col_ind = []

    for i in range(rows):
        for j in range(cols):
            index = i * cols + j
            if i > 0:
                up_index = index - cols
                weight = np.exp(-abs(int(gray[i, j]) - int(gray[i-1, j])) / 10.0)
                data.append(weight)
                row_ind.append(index)
                col_ind.append(up_index)
            if j > 0:
                left_index = index - 1
                weight = np.exp(-abs(int(gray[i, j]) - int(gray[i, j-1])) / 10.0)
                data.append(weight)
                row_ind.append(index)
                col_ind.append(left_index)

    graph = csr_matrix((data, (row_ind, col_ind)), shape=(size, size))
    degrees = np.array(graph.sum(axis=0)).flatten()
    degree_matrix = diags(degrees)
    laplacian = degree_matrix - graph
    eigenvalues, eigenvectors = eigsh(laplacian, k=2, which='SM')
    vec = eigenvectors[:, 1]
    median_value = np.median(vec)
    labels = (vec > median_value).astype(int).reshape(rows, cols)
    return labels

def main():
    folder_path = '/home/planck/NIDHI_SONI/cv_project/cv_assignment_2_data/img'  # Ensure this is the correct path
    images = load_images_from_folder(folder_path)
    num_clusters_list = [3, 6]

    for image in images:
        original = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        gray_flat = gray.flatten()  # Flatten the gray image for silhouette calculation
        titles = ['Original']
        segmented_results = [original]
        colormaps = ['viridis']  # Default colormap for the original image
        scores = []

        for num_clusters in num_clusters_list:
            # K-Means segmentation
            kmeans_segmented = segment_image(image, num_clusters, method='kmeans')
            segmented_results.append(kmeans_segmented)
            titles.append(f'K-Means {num_clusters} Clusters')
            colormaps.append('plasma')
            # Calculate silhouette score for K-Means
            kmeans_labels = kmeans_segmented.flatten()
            score_kmeans = silhouette_score(gray_flat.reshape(-1, 1), kmeans_labels)
            scores.append(f"Silhouette Score K-Means {num_clusters}: {score_kmeans:.2f}")

            # Ratio Cut segmentation
            ratio_cut_segmented = ratio_cut_clustering(image, num_clusters)
            segmented_results.append(ratio_cut_segmented)
            titles.append(f'Ratio Cut {num_clusters} Clusters')
            colormaps.append('cividis')
            # Calculate silhouette score for Ratio Cut
            ratio_cut_labels = ratio_cut_segmented.flatten()
            score_ratio_cut = silhouette_score(gray_flat.reshape(-1, 1), ratio_cut_labels)
            scores.append(f"Silhouette Score Ratio Cut {num_clusters}: {score_ratio_cut:.2f}")

        display_images(segmented_results, titles, colormaps)

        # Print silhouette scores for each clustering
        for score in scores:
            print(score)

if __name__ == "__main__":
    main()
