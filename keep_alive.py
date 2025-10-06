"""
Keep Render free tier backend alive by pinging it every 10 minutes.
Run this script on a free service like GitHub Actions, Render Cron, or your local machine.
"""

import requests
import time

BACKEND_URL = "https://tutoria-ia-backend.onrender.com/health"

def ping_backend():
    try:
        response = requests.get(BACKEND_URL, timeout=30)
        if response.status_code == 200:
            print(f"✅ Backend is alive! Status: {response.json()}")
        else:
            print(f"⚠️ Backend responded with status: {response.status_code}")
    except Exception as e:
        print(f"❌ Error pinging backend: {e}")

if __name__ == "__main__":
    while True:
        ping_backend()
        time.sleep(600)  # Wait 10 minutes
