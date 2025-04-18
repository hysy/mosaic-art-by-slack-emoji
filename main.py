"""
Description: 
    Create a mosaic image
Usage: 
    python3 main.py --input <input_image_path> --output <output_image_path> --elements <elements_folder>
Output: 
    <output_image_path>
"""

import argparse
import concurrent.futures
import math
import os
import subprocess

from PIL import Image

OUTPUT_IMAGE_SIZE = 4096
TILE_SIZE = 16


class ElementDetail:
    def __init__(self, path, average_color):
        self.path = path
        self.average_color = average_color


def color_distance(c1, c2):
    return math.sqrt(sum([(c1[i] - c2[i]) ** 2 for i in range(3)]))


def get_closest_element_path(average_color, element_details):
    # TODO: rewrite by numpy
    closest_element_path = None
    closest_distance = float("inf")
    for elements_detail in element_details:
        distance = color_distance(average_color, elements_detail.average_color)
        if distance < closest_distance:
            closest_distance = distance
            closest_element_path = elements_detail.path
    return closest_element_path


def process_tile(x, y, input_image, mosaic_image, element_details):
    left, top, right, bottom = x, y, x + TILE_SIZE, y + TILE_SIZE
    # print(f"Processing tile at ({left}, {top}, {right}, {bottom})")

    tile = input_image.crop((left, top, right, bottom))
    tile_pixels = tile.load()
    tile_colors = []
    for i in range(TILE_SIZE):
        for j in range(TILE_SIZE):
            tile_color = tile_pixels[i, j]
            tile_colors.append(tile_color)

    average_color = tuple([sum(col) // len(tile_colors) for col in zip(*tile_colors)])
    closest_element_path = get_closest_element_path(average_color, element_details)
    element_image = Image.open(closest_element_path).convert("RGB")
    element_image = element_image.resize((TILE_SIZE, TILE_SIZE))

    mosaic_image.paste(element_image, (left, top))


def get_element_details(elements_folder):
    """elementsフォルダの画像の平均色を計算する関数"""
    elements_detail = []
    elements_dir = os.path.join(os.path.dirname(__file__), elements_folder)
    for ep in os.listdir(elements_dir):
        element_path = os.path.join(elements_dir, ep)
        element_image = Image.open(element_path).convert("RGB")
        element_image = element_image.resize((TILE_SIZE, TILE_SIZE))

        element_pixels = element_image.load()
        element_colors = []
        for i in range(TILE_SIZE):
            for j in range(TILE_SIZE):
                element_color = element_pixels[i, j]
                element_colors.append(element_color)
        element_average_color = tuple(
            [sum(col) // len(element_colors) for col in zip(*element_colors)]
        )
        elements_detail.append(ElementDetail(element_path, element_average_color))

    elements_detail.sort(key=lambda x: x.average_color)
    return elements_detail


def create_mosaic(input_image_path, extended_image_path, elements_folder):
    subprocess.run(
        f"convert {input_image_path} -colorspace sRGB -resize {OUTPUT_IMAGE_SIZE}x {extended_image_path}",
        shell=True,
    )
    extended_image = Image.open(extended_image_path).convert("RGB")
    # extended_image = Image.new("RGB", (OUTPUT_IMAGE_SIZE, OUTPUT_IMAGE_SIZE))

    mosaic_image = Image.new("RGB", (OUTPUT_IMAGE_SIZE, OUTPUT_IMAGE_SIZE))

    element_details = get_element_details(elements_folder)

    with concurrent.futures.ThreadPoolExecutor() as executor:
        futures = []
        for x in range(0, OUTPUT_IMAGE_SIZE, TILE_SIZE):
            for y in range(0, OUTPUT_IMAGE_SIZE, TILE_SIZE):
                futures.append(
                    executor.submit(
                        process_tile,
                        x,
                        y,
                        extended_image,
                        mosaic_image,
                        element_details,
                    )
                )
        for future in concurrent.futures.as_completed(futures):
            future.result()
    mosaic_image.save(extended_image_path)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Create a mosaic image")
    parser.add_argument("--input", required=True, type=str, help="Input image path")
    parser.add_argument("--output", required=True, type=str, help="Output image path")
    parser.add_argument(
        "--elements", required=True, type=str, help="Elements folder path"
    )
    args = parser.parse_args()
    create_mosaic(args.input, args.output, args.elements)
