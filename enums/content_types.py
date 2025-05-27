from enum import Enum


class ContentTypes(Enum):
    photo: str = 'photo'
    document: str = 'document'
    sticker: str = 'sticker'
    text: str = 'text'
    video: str = 'video'