import requests
import os
import mimetypes

SERVER_URL = "http://127.0.0.1:8000"


def upload_image(image_path):
    url = f"{SERVER_URL}/upload/"
    
    # Check if file exists before trying to open it
    if not os.path.exists(image_path):
        print(f"File not found: {image_path}")
        return None
    
    # Determine the correct MIME type from file extension
    mime_type, _ = mimetypes.guess_type(image_path)
    # Default to image/jpeg if MIME type cannot be determined
    if not mime_type:
        mime_type = "image/jpeg"
    
    with open(image_path, "rb") as image_file:
        # Extract just the filename from the path
        filename = os.path.basename(image_path)
        files = {"file": (filename, image_file, mime_type)}
        response = requests.post(url, files=files)
    if response.status_code == 200:
        print(f"Image uploaded successfully: {response.json()}")
        return response.json().get("filename")
    else:
        print(f"Failed to upload image. Status code: {response.status_code}")
        return None


def list_images(simple: bool = True):
    """Get list of all images from the server
    
    Args:
        simple: If True, returns simple list of filenames (backward compatible)
                If False, returns list of dicts with full metadata
    """
    url = f"{SERVER_URL}/images/"
    params = {"simple": "true" if simple else "false"}
    response = requests.get(url, params=params)
    
    if response.status_code == 200:
        images = response.json().get("images", [])
        return images
    else:
        print(f"Failed to list images. Status code: {response.status_code}")
        if response.status_code == 404:
            print("No images found on server")
        return []


def get_image_by_filename(filename, save_path=None):
    """Download a specific image by filename"""
    url = f"{SERVER_URL}/images/{filename}"
    response = requests.get(url)
    
    if response.status_code == 200:
        if save_path is None:
            save_path = f"downloaded_{filename}"
        
        with open(save_path, "wb") as file:
            file.write(response.content)
        print(f"Image downloaded successfully as '{save_path}'")
        return save_path
    else:
        print(f"Failed to retrieve image. Status code: {response.status_code}")
        if response.status_code == 404:
            print(f"Image '{filename}' not found on server")
        return None


def get_image_by_index(index):
    """Get an image by its index in the list of images"""
    # First, get the list of images (simple format for backward compatibility)
    images = list_images(simple=True)
    
    if not images:
        print("No images available on server")
        return None
    
    # Check if index is valid
    if index < 0 or index >= len(images):
        print(f"Index {index} is out of range. Available images: {len(images)}")
        return None
    
    # Get the filename at the specified index
    # Handle both string (simple format) and dict (full format) responses
    if isinstance(images[index], dict):
        filename = images[index]["filename"]
    else:
        filename = images[index]
    
    print(f"Downloading image at index {index}: {filename}")
    
    # Download the image
    return get_image_by_filename(filename)


if __name__ == "__main__":
    # First, upload an image
    image_path = "path_to_your_image.jpg"  # Provide the path to the image you want to upload
    filename = upload_image(image_path)
