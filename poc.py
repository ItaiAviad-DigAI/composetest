import requests


OUTPUT_PATH = "received_trimmed.mp4"

url = "http://127.0.0.1:8000/trim"
payload = {
    "url": "https://samplelib.com/lib/preview/mp4/sample-5s.mp4",
    "start_time": 1,
    "end_time": 3,
}

try:
    response = requests.post(url, json=payload)

    if response.status_code == 200:
        with open(OUTPUT_PATH, "wb") as f:
            f.write(response.content)
        print(f"✅ Video saved as {OUTPUT_PATH}")
    else:
        print(f"❌ Error: {response.status_code} - {response.text}")
except Exception as e:
    print(f"❌ Exception: {e}")
