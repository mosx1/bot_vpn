import requests, time

from connect import token

def update_connect() -> None:
    while True:
        requests.post(f"https://api.telegram.org/bot{token}/getUpdates")
        time.sleep(5)