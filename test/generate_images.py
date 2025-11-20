import numpy as np
import argparse
import os
from PIL import Image
from concurrent.futures import ThreadPoolExecutor

# Define resolution for 12 MP image (4000x3000)
WIDTH, HEIGHT = 4000, 3000
OUTPUT_DIR = "images"

def generate_image(index):
    """Generate and save a 12 MP image with random colors."""
    # Ensure the output directory exists
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    # Generate random RGB values for each pixel
    image_array = np.random.randint(0, 256, (HEIGHT, WIDTH, 3), dtype=np.uint8)

    # Create an image using PIL
    image = Image.fromarray(image_array)

    # Save the image inside the images/ directory
    filename = os.path.join(OUTPUT_DIR, f"generated_12MP_image_{index}.png")
    image.save(filename)
    print(f"Saved {filename}")

def main():
    # Parse the command-line argument
    parser = argparse.ArgumentParser(description="Generate multiple 12 MP images using threading.")
    parser.add_argument("num_images", type=int, help="Number of images to generate.")
    args = parser.parse_args()

    # Run with a thread pool
    with ThreadPoolExecutor(max_workers=4) as executor:
        executor.map(generate_image, range(args.num_images))

    print("All images generated successfully in the 'images/' directory!")

if __name__ == "__main__":
    main()
