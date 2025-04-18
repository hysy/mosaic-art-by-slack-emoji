"""
Description: 
    Download all custum emoji from slack

Output: 
    emoji_list/emoji_name.extension
"""
import concurrent.futures
import os
import sys
import urllib.error
import urllib.request

import requests

TOKEN = os.environ["SLACK_TOKEN"]
HEADERS = {"Authorization": f"Bearer {TOKEN}"}
DL_DIR = "emoji_list"


def download_file(url, dst_path):
    try:
        with urllib.request.urlopen(url) as web_file:
            data = web_file.read()
            with open(dst_path, mode="wb") as local_file:
                local_file.write(data)
    except urllib.error.URLError as e:
        print(e)


def get_emoji_dict():
    r = requests.get("https://slack.com/api/emoji.list", headers=HEADERS)
    jn = r.json()
    with open("test.json", "w") as f:
        f.write(str(jn))
    return jn["emoji"]


if __name__ == "__main__":
    """
    download all emoji
    DL_DIR/emoji_name.extension
    """
    emoji_dict = get_emoji_dict()
    os.makedirs(DL_DIR, exist_ok=True)

    with concurrent.futures.ThreadPoolExecutor() as executor:
        futures = []
        # Skip alias
        # API response format
        # emoji;  {emoji_name}: 'https://emoji.slack-edge.com/{TEAM_ID}/{emoji_name}/{RANDOMIZED_EMOJI_NAME}.{EXTENSION}'
        # alias;  {emoji_name}: 'alias:{emoji_alias_name}'
        for name, url in filter(
            lambda x: not x[1].startswith("alias"), emoji_dict.items()
        ):
            file_format = url.split(".")[-1]
            dst_path = os.path.join(DL_DIR, os.path.basename(name + "." + file_format))
            futures.append(executor.submit(download_file, url, dst_path))

        for future in concurrent.futures.as_completed(futures):
            try:
                future.result()
            except Exception as e:
                print(e, file=sys.stderr)
