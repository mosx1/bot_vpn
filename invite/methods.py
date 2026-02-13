from connect import bot

from managment_user import add_user

from database import User, get_user_by_id, write_invited, increment_balance, reset_to_zero_balance

from utils import replaceMonthOnRuText

from configparser import ConfigParser

from enums.parse_mode import ParseMode


def writeInvited(userId: str, userInvitedId: str):
    """Записывает отношение приглашенного к пригласившему."""
    write_invited(userId, userInvitedId)
    


def addInvitedBonus(userId):
    """Добавляет бонус-подписку за инвайт пользователя."""
    add_user(userId, 1)
    user: User = get_user_by_id(userId)
    bot.send_photo(
        userId,
        photo=open("image/referalYes.png", "rb"),
        caption=f"Дата окончания подписки изменена\: {replaceMonthOnRuText(user.exit_date)}",
        parse_mode=ParseMode.mdv2.value
    )



def incrementBalance(userId: str, month=None, summ=None):
    """
    Добавляет сумму к балансу пользователя.
    Начисляется тому, кто пригласил.
    """
    increment_balance(userId, month=month, summ=summ)



def resetToZeroBalance(userId: str):
    """Обнуляет бонусный баланс клиента."""
    reset_to_zero_balance(userId)