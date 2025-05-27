import config

from connect import db, bot
from managment_user import add_user



def writeInvited(userId: str, userInvitedId: str):
    """
        Записывает отношение приглашенного к пригласившему
    """
    with db.cursor() as cursor:
        cursor.execute(
            "UPDATE users_subscription SET invited = {} WHERE telegram_id = {}".format(userInvitedId, userId)
        )
        db.commit()
    


def addInvitedBonus(userId):
    """
        Добавляет бонус-подписку за инвайт пользователя
    """
    add_user(userId, 1)
    bot.send_photo(
        userId,
        photo=open(config.FILE_URL + "image/referalYes.png", "rb"),
        caption="Дата окончания подписки изменена"
    )



def incrementBalance(userId: str, month=None, summ=None):
    """
        Добавляет сумму к балансу пользователя либо на основании кол-ва месяцев оплаченных пользователем, либо на основании кол-ва денег
        В метод передается id пользователя который оплатил, а начисляется тому, кто пригласил
    """
    if month:
        summ = config.PRICE * month
    
    with db.cursor() as cursor:
        cursor.execute(
            "UPDATE users_subscription SET balance = balance + {} WHERE telegram_id = (SELECT invited FROM users_subscription WHERE telegram_id = {})".format(
                summ,
                userId
            )
        )
        db.commit()



def resetToZeroBalance(userId: str):
    """
        Обнуляет бонусный баланс клиента
    """
    with db.cursor() as cursor:
        cursor.execute(
            "UPDATE users_subscription SET balance = 0 WHERE telegram_id = {}".format(userId)
        )
        db.commit()