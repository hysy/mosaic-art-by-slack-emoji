import argparse
import concurrent.futures
import os
import warnings

# Suppress specific warnings from PIL
warnings.filterwarnings("ignore", category=UserWarning, module="PIL.Image")

import numpy as np
from PIL import Image
from scipy.spatial import cKDTree

OUTPUT_IMAGE_SIZE = 4096
TILE_SIZE = 16
CHUNK_SIZE = 256  # Process larger chunks at once for better efficiency


class ElementDetail:
    def __init__(self, path, average_color, image_array=None):
        self.path = path
        self.average_color = average_color
        self.image_array = image_array


def get_element_image_array(path):
    """Cache the resized element images as numpy arrays"""
    return np.array(Image.open(path).convert("RGB").resize((TILE_SIZE, TILE_SIZE)))


def process_chunk(start_x, start_y, input_array, element_details, color_tree):
    chunk_size = min(CHUNK_SIZE, OUTPUT_IMAGE_SIZE - start_x)
    height = min(CHUNK_SIZE, OUTPUT_IMAGE_SIZE - start_y)

    # Create output array for the chunk
    output_array = np.zeros((height, chunk_size, 3), dtype=np.uint8)

    # Process each tile in the chunk
    for y in range(0, height, TILE_SIZE):
        for x in range(0, chunk_size, TILE_SIZE):
            # Extract tile
            tile = input_array[
                start_y + y : start_y + y + TILE_SIZE,
                start_x + x : start_x + x + TILE_SIZE,
            ]

            # Calculate average color
            average_color = np.mean(tile, axis=(0, 1)).astype(int)

            # Find closest element
            _, index = color_tree.query(average_color)
            element = element_details[index]

            # Place the element in the output array
            output_array[y : y + TILE_SIZE, x : x + TILE_SIZE] = element.image_array

    return output_array, start_x, start_y


def get_element_details(elements_folder):
    elements_detail = []
    elements_dir = os.path.join(os.path.dirname(__file__), elements_folder)

    # Preload and cache all element images
    for ep in os.listdir(elements_dir):
        element_path = os.path.join(elements_dir, ep)
        element_array = get_element_image_array(element_path)
        element_average_color = tuple(np.mean(element_array, axis=(0, 1)).astype(int))
        elements_detail.append(
            ElementDetail(element_path, element_average_color, element_array)
        )

    return elements_detail


def create_mosaic(input_image_path, output_image_path, elements_folder):
    # Load, resize and convert input image to numpy array using PIL
    input_image = Image.open(input_image_path).convert("RGB")
    input_image = input_image.resize(
        (OUTPUT_IMAGE_SIZE, OUTPUT_IMAGE_SIZE), Image.Resampling.LANCZOS
    )
    input_array = np.array(input_image)

    # Initialize output array
    output_array = np.zeros((OUTPUT_IMAGE_SIZE, OUTPUT_IMAGE_SIZE, 3), dtype=np.uint8)

    # Prepare element details and KD-tree
    element_details = get_element_details(elements_folder)
    color_tree = cKDTree([ed.average_color for ed in element_details])

    # Process chunks in parallel
    with concurrent.futures.ProcessPoolExecutor() as executor:
        futures = []
        for y in range(0, OUTPUT_IMAGE_SIZE, CHUNK_SIZE):
            for x in range(0, OUTPUT_IMAGE_SIZE, CHUNK_SIZE):
                futures.append(
                    executor.submit(
                        process_chunk,
                        x,
                        y,
                        input_array,
                        element_details,
                        color_tree,
                    )
                )

        # Collect results and update output array
        for future in concurrent.futures.as_completed(futures):
            chunk_array, start_x, start_y = future.result()
            chunk_height, chunk_width = chunk_array.shape[:2]
            output_array[
                start_y : start_y + chunk_height, start_x : start_x + chunk_width
            ] = chunk_array

    # Save the final image
    Image.fromarray(output_array).save(output_image_path)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Create a mosaic image")
    parser.add_argument("--input", required=True, type=str, help="Input image path")
    parser.add_argument("--output", required=True, type=str, help="Output image path")
    parser.add_argument(
        "--elements", required=True, type=str, help="Elements folder path"
    )
    args = parser.parse_args()
    create_mosaic(args.input, args.output, args.elements)
