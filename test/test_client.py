import os
import requests
import time

# Server details
SERVER_URL = "http://172.31.100.101:8000"
IMAGE_DIR = "downloaded_images"

# Ensure local directory exists
if not os.path.exists(IMAGE_DIR):
    os.makedirs(IMAGE_DIR)

def get_image_list():
    response = requests.post(f"{SERVER_URL}/images/", json={})  # Send an empty JSON body
    if response.status_code == 200:
        return response.json()["images"]
    else:
        print("Failed to fetch image list.")
        return []

# Get the list of images from the server
def get_image_list():
    response = requests.get(f"{SERVER_URL}/images/")
    if response.status_code == 200:
        return response.json()["images"]
    else:
        print("Failed to fetch image list.")
        return []

# Download images and measure transfer time
def download_images():
    image_list = get_image_list()
    if not image_list:
        print("No images to download.")
        return

    print(f"Found {len(image_list)} images. Downloading...")

    transfer_times = []

    for image_name in image_list:
        start_time = time.time()
        response = requests.get(f"{SERVER_URL}/images/{image_name}")

        if response.status_code == 200:
            image_path = os.path.join(IMAGE_DIR, image_name)
            with open(image_path, "wb") as img_file:
                img_file.write(response.content)

            end_time = time.time()
            transfer_time = end_time - start_time
            transfer_times.append((image_name, transfer_time))

            print(f"Downloaded {image_name} in {transfer_time:.4f} seconds")
        else:
            print(f"Failed to download {image_name}")

    # Log the transfer times
    with open("transfer_times.txt", "w") as log_file:
        for image_name, time_taken in transfer_times:
            log_file.write(f"{image_name}: {time_taken:.4f} seconds\n")

    print("Download complete. Transfer times logged in 'transfer_times.txt'.")

if __name__ == "__main__":
    download_images()

