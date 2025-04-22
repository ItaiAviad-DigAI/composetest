import requests

TRIMMED_OUTPUT_PATH = "trimmed.mp4"
AUDIO_OUPUT_PATH = "audio.mp3"
DEFAULT_VIDEO_URL = "https://samplelib.com/lib/preview/mp4/sample-5s.mp4"

SERVER_URL = "http://127.0.0.1:8000/"
SERVER_TRIM_ENDPOINT = "trim"
SERVER_EXTRACT_AUDIO_ENDPOINT = "extract_audio"


def trim_video_request(payload):
    """Send a request to the server to trim a video"""
    try:
        response = requests.post(f"{SERVER_URL}/{SERVER_TRIM_ENDPOINT}", json=payload)

        if response.status_code == 200:
            with open(TRIMMED_OUTPUT_PATH, "wb") as f:
                f.write(response.content)
            print(f"✅ Video saved as {TRIMMED_OUTPUT_PATH}")
        else:
            print(f"❌ Error: {response.status_code} - {response.text}")
    except Exception as e:
        print(f"❌ Exception: {e}")


def extract_audio_request(payload):
    """Extract audio from a video URL and save it to a file"""
    try:
        response = requests.post(
            f"{SERVER_URL}/{SERVER_EXTRACT_AUDIO_ENDPOINT}", json=payload
        )

        if response.status_code == 200:
            with open(AUDIO_OUPUT_PATH, "wb") as f:
                f.write(response.content)
            print(f"✅ Audio saved as {AUDIO_OUPUT_PATH}")
        else:
            print(f"❌ Error: {response.status_code} - {response.text}")
    except Exception as e:
        print(f"❌ Exception: {e}")


def main():
    print("Trim/Extract Audio from Video URL")
    payload = {}
    url = input(f"URL (default: {DEFAULT_VIDEO_URL}): ").strip()
    if not url:
        url = f"{DEFAULT_VIDEO_URL}"
    payload["url"] = url

    choice = input("Trim or Extract Audio? (t/e): ").strip().lower()
    if choice == "t":
        start_time = input(
            "Start Time (in seconds or HH:MM:SS format, default: 0): "
        ).strip()
        end_time = input(
            "End Time (in seconds or HH:MM:SS format, default: 0): "
        ).strip()
        if not start_time:
            start_time = "0"
        if not end_time:
            end_time = "0"
        # Check if int
        try:
            start_time = int(start_time)
            end_time = int(end_time)
        except ValueError:
            pass

        payload["start_time"] = start_time
        payload["end_time"] = end_time
        trim_video_request(payload)
    elif choice == "e":
        extract_audio_request(payload)
    else:
        print("Invalid choice. Exiting.")
        return


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt as e:
        pass
