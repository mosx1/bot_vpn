import requests


def get_subscription_link(telegram_id: str | int) -> str:
    """
        Получает ссылку для подписки
    """
    responce = requests.get(
        f'https://kuzmos.ru/sub/get_link?id={telegram_id}'
    )
    
    return responce.text