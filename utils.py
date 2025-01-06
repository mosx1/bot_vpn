from connect import db


def replaceMonthOnRuText(datetime_exit) -> str:
    
    """принимает дату в формате как в БД
    и отдает строку с понятной человеку датой
    без времени"""

    arr = ['янв.',
                'фев.',
                'март.',
                'апр.',
                'мая',
                'июн.',
                'июл.',
                'авг.',
                'сен.',
                'окт.',
                'ноя.',
                'дек.'
                ]
    arrDate = str(datetime_exit).split("-")
    moth = arr[int(arrDate[1]) - 1]
    return form_text_markdownv2(str(arrDate[2]).split(" ")[0] + " " + str(moth) + " " + str(arrDate[0]))


def form_text_markdownv2(message_text: str, delete=None):

    """Преобразование строки в формат MarkdownV2"""
    
    temp = message_text
    try:
        for escaped_characters in ['_', '*', '[', ']', '(', ')', '~', '`', '>', '#', '+', '-', '=', '|', '{', '}', '.', '!']:
            if escaped_characters in message_text:
                if delete == True:
                    message_text = str(message_text).replace(escaped_characters, " ")
                else:
                    message_text = str(message_text).replace(escaped_characters, "\\" + escaped_characters)
    except TypeError:
        return temp
    return message_text


#получает адрес сервера по ид
def getUrlByIdServer(serverId: str) -> str:
    with db.cursor() as cursor:
        cursor.execute("SELECT links FROM servers WHERE id = " + str(serverId))
        curData = cursor.fetchone()
        if curData:
            return curData[0]