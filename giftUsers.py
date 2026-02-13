from managment_user import add_user

from database import gen_gift_code, check_and_consume_gift_code


def genGiftCode(month: int) -> str:
    """Создаёт подарочный код. Обёртка для обратной совместимости."""
    return gen_gift_code(month)


def checkGiftCode(message) -> bool:
    """Проверяет подарочный код, при успехе активирует и возвращает True."""
    month = check_and_consume_gift_code(message.text)
    if month:
        add_user(message.from_user.id, month)
        return True
    return False
