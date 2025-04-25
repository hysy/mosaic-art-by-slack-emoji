# Slack Emoji Mosaic Art Generator

A tool to create mosaic art using custom emojis from your Slack workspace.

## Features

0. Download custom emojis from your Slack workspace
1. Generate mosaic art using the downloaded emojis

## Prerequisites

- Python 3.x
- Slack API Token
- ImageMagick (for image processing)

## Setup

1. Install packages from lock file

```bash
pipenv sync
```

2. Activate the virtual environment

```bash
pipenv shell
```

### Environment Setup

If you need download custom emojis from Slack, set up the following environment.

```bash
export SLACK_TOKEN="xoxb-your-token"
```

## Usage

### 1. Download Custom Emojis

```bash
python emoji-downloader.py
```

This will download all custom emojis to the `emoji_list` directory.

### 2. Generate Mosaic Art

```bash
python main.py --input <input_image_path> --output <output_image_path> --elements <elements_folder>
```

#### Parameters

- `--input`: Path to the source image you want to convert
- `--output`: Path where the generated mosaic art will be saved
- `--elements`: Path to the folder containing emoji images (typically `emoji_list`)

## Technical Details

- Output image size: 4096x4096 pixels
- Tile size: 16x16 pixels
- Optimal emoji selection based on color similarity

## License

[MIT](https://opensource.org/licenses/MIT)

Copyright (c) 2023-present, hysy
