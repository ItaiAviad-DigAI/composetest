import logging
import os
import sys
import time
import urllib.request

import ffmpeg
import redis
from flask import Flask, request, send_file


DEBUG = False
if sys.argv and "DEBUG" in sys.argv:
    DEBUG = True
log = logging.getLogger(__name__)
logging.basicConfig(level=logging.DEBUG if DEBUG else logging.INFO)

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
    """Download a video from a given URL and save it to the specified path
    Args:
        url (str): The URL of the video to download
        output_path (str): Output path for downloaded video
    Returns:
        str: downloaded video file path
    """
    if not url or ".mp4" not in url:
        raise ValueError("Invalid URL or unsupported video format (not .mp4)")
    try:
        urllib.request.urlretrieve(url, output_path)
    except Exception as e:
        log.debug(f"Failed to download video from {url}: {e}")
        raise
    return output_path


def check_time_format(time_str: str) -> bool:
    """Check if the time string is in HH:MM:SS format or seconds"""
    if type(time_str) == int or type(time_str) == float:
        return True
    if type(time_str) != str:
        return False
    if ":" in time_str:
        parts = time_str.split(":")
        # Check if 3 parts
        if len(parts) != 3:
            return False
        # Checks if ints
        for part in parts:
            if not part.isdigit():
                return False
    else:
        if not time_str.isdigit():
            return False
    return True


def trim_video(
    video_path: str,
    trimmed_video_path: str,
    start_time: str = "00:00:00",
    end_time: str = "00:00:00",
):
    """Trim a local video using ffmpeg from start_time to end_time"""
    try:
        log.debug(f"Trimming video: {video_path} from {start_time} to {end_time}")
        ffmpeg.input(video_path, ss=start_time, to=end_time).output(
            trimmed_video_path
        ).overwrite_output().run(quiet=not DEBUG)
    except ffmpeg.Error as e:
        log.debug(f"ffmpeg error: {e}")
        raise
    except Exception as e:
        log.debug(f"Error trimming video: {e}")
        raise

    return trimmed_video_path


def extract_audio_from_video(
    video_path: str,
    audio_path: str,
):
    """Extract audio from a local video using ffmpeg"""
    try:
        log.debug(f"Extracting audio from video: {video_path}")
        ffmpeg.input(video_path).output(audio_path).overwrite_output().run(quiet=not DEBUG)
    except ffmpeg.Error as e:
        log.debug(f"ffmpeg error: {e}")
        raise
    except Exception as e:
        log.debug(f"Error extracting audio: {e}")
        raise

    return audio_path


@app.route("/")
def hello():
    count = get_hit_count()
    return f"Hello World! I have been seen {count} times.\n"


@app.post("/trim")
def trim():
    """API endpoint to trim a video from a given URL

    Returns:
        - 200 OK: The trimmed video file (if successful)
    """
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

    if not url:
        return "Missing required parameters (url)", 400
    if not check_time_format(start_time) or not check_time_format(end_time):
        return "Invalid start/end time format. Use HH:MM:SS or seconds", 400

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
        trimmed_video_path = trim_video(
            video_path, trimmed_video_path, start_time, end_time
        )
    except Exception as e:
        return f"Failed to trim video. {e}", 500
    finally:
        # Clean up the downloaded video file
        try:
            if video_path and os.path.exists(video_path):
                os.remove(video_path)
        except OSError as e:
            log.debug(f"Error deleting video file: {e}")

    if not trimmed_video_path or not os.path.exists(trimmed_video_path):
        return "Trimmed video not found", 404

    log.debug((f"Video trimmed successfully: {video_path} to {trimmed_video_path}"))
    return send_file(f"{trimmed_video_path}")


@app.post("/extract_audio")
def extract_audio():
    # Accept JSON and form data
    if request.is_json:
        data = request.get_json()
        url = data.get("url")
    else:
        url = request.form.get("url")

    if not url:
        return "Missing required parameters (url)", 400

    # Download the video
    try:
        video_path = download_video(url)
    except Exception as e:
        return f"Failed to download video. {e}", 500

    if not video_path or not os.path.exists(video_path):
        return "Video not found", 404

    # Extract the audio
    audio_path = f"audio_{video_path}".replace(".mp4", ".mp3")
    try:
        audio_path = extract_audio_from_video(video_path, audio_path)
    except Exception as e:
        return f"Failed to extract audio. {e}", 500
    finally:
        # Clean up the downloaded video file
        try:
            if video_path and os.path.exists(video_path):
                os.remove(video_path)
        except OSError as e:
            log.debug(f"Error deleting video file: {e}")

    if not audio_path or not os.path.exists(audio_path):
        return "Audio file not found", 404

    log.debug((f"Audio extracted successfully: {video_path} to {audio_path}"))
    return send_file(f"{audio_path}")
