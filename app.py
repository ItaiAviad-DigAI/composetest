import logging
import os
import time
import urllib.request

import redis
from flask import Flask, request

log = logging.getLogger(__name__)
logging.basicConfig(level=logging.DEBUG)

app = Flask(__name__)
cache = redis.Redis(host="redis", port=6379)


def get_hit_count():
    retries = 5
    while True:
        try:
            return cache.incr("hits")
        except redis.exceptions.ConnectionError as exc:
            if retries == 0:
                raise exc
            retries -= 1
            time.sleep(0.5)


def download_video(url: str, output_path: str = "video"):
    """Download a video from a given URL and save it to the specified path"""
    try:
        urllib.request.urlretrieve(url, output_path)
    except Exception as e:
        log.debug(f"Failed to download video from {url}: {e}")
        raise
    return output_path


def trim_video(video_path, start, end):
    pass


@app.route("/")
def hello():
    count = get_hit_count()
    return f"Hello World! I have been seen {count} times.\n"


@app.post("/trim")
def trim():
    url = request.form.get("url")
    start = request.form.get("start")
    end = request.form.get("end")

    # Download the video
    try:
        video_path = download_video(url)
    except Exception as e:
        log.debug(f"Error downloading video: {e}")
        return "Failed to download video", 500

    if not video_path:
        return "Video not found", 404

    # Trim the video
    try:
        trim_video(video_path, start, end)
    except Exception as e:
        log.debug(f"Error trimming video: {e}")
        return "Failed to trim video", 500
    finally:
        # Clean up the downloaded video file
        try:
            os.remove(video_path)
        except OSError as e:
            log.debug(f"Error deleting video file: {e}")

    return "OK", 200
