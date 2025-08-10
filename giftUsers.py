from connect import db
from telebot import types
from managment_user import add_user


def genGiftCode(month: int):

    with db.cursor() as cursor:
        cursor.execute(
            "INSERT INTO gift_codes (code, month) VALUES (md5(random()::text), {}) RETURNING code".format(month)
        )
        hash = cursor.fetchone()[0]

        db.commit()
        
        return hash



def checkGiftCode(message: types.Message):

    with db.cursor() as cursor:
        cursor.execute("SELECT month FROM gift_codes WHERE code = '{}'".format(message.text))
        giftData = cursor.fetchone()
        if giftData:
            month = giftData[0]
            if month:
                add_user(
                    message.from_user.id,
                    month
                )
                cursor.execute("DELETE FROM gift_codes WHERE code = '{}'".format(message.text))

                db.commit

                return True
    return False