import logging
import os
import time
import urllib.request

import ffmpeg
import redis
from flask import Flask, request, send_file

log = logging.getLogger(__name__)
logging.basicConfig(level=logging.DEBUG)

app = Flask(__name__)
cache = redis.Redis(host="redis", port=6379)


DEFAULT_OUTPUT_EXTENSION = "mp4"
DEFAULT_OUTPUT_PATH = f"video.{DEFAULT_OUTPUT_EXTENSION}"


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


def download_video(url: str, output_path: str = DEFAULT_OUTPUT_PATH) -> str:
    """Download a video from a given URL and save it to the specified path"""
    try:
        urllib.request.urlretrieve(url, output_path)
    except Exception as e:
        log.debug(f"Failed to download video from {url}: {e}")
        raise
    return output_path


def trim_video(
    video_path: str,
    trimmed_video_path: str,
    start_time: str = "00:00:00",
    end_time: str = "00:00:00",
):
    try:
        log.debug(f"Trimming video: {video_path} from {start_time} to {end_time}")
        ffmpeg.input(video_path, ss=start_time, to=end_time).output(
            trimmed_video_path
        ).overwrite_output().run()
    except ffmpeg.Error as e:
        log.debug(f"ffmpeg error: {e}")
        raise
    except Exception as e:
        log.debug(f"Error trimming video: {e}")
        raise

    return trimmed_video_path


@app.route("/")
def hello():
    count = get_hit_count()
    return f"Hello World! I have been seen {count} times.\n"


@app.post("/trim")
def trim():
    # Accept JSON and form data
    if request.is_json:
        data = request.get_json()
        url = data.get("url")
        start_time = data.get("start_time")
        end_time = data.get("end_time")
    else:
        url = request.form.get("url")
        start_time = request.form.get("start_time")
        end_time = request.form.get("end_time")

    if not url or not start_time or not end_time:
        return "Missing required parameters (url/start_time/end_time)", 400

    # Download the video
    try:
        video_path = download_video(url)
    except Exception as e:
        return f"Failed to download video. {e}", 500

    if not video_path or not os.path.exists(video_path):
        return "Video not found", 404

    # Trim the video
    trimmed_video_path = f"trimmed_{video_path}"
    try:
        trimmed_video_path = trim_video(video_path, trimmed_video_path, start_time, end_time)
    except Exception as e:
        return f"Failed to trim video. {e}", 500
    finally:
        # Clean up the downloaded video file
        try:
            if video_path and os.path.exists(video_path):
                os.remove(video_path)
        except OSError as e:
            log.debug(f"Error deleting video file: {e}")

    log.debug((f"Video trimmed successfully: {video_path} to {trimmed_video_path}"))
    return send_file(f"{trimmed_video_path}")
