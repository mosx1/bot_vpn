from enum import Enum



class MessageTextRu(Enum):

    spam: str = "Рассылка на всех запущена"
    spamDe: str = "Рассылка на немецкий сервер напущена"
    spamNid: str = "Рассылка на нидерландский сервер запущена"
    spamAction: str = "Рассылка на активных пользователей запущена"
    spamNotAction: str = "Рассылка на неактивных пользоателей запущена"