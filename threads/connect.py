import logging
import requests, time

from connect import token

def update_connect() -> None:
    while True:
        try:
            requests.post(f"https://api.telegram.org/bot{token}/getUpdates")
        except Exception as e:
            logging.error(str(e))
        time.sleep(5)
