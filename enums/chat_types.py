from enum import Enum


class ChatTypes(Enum):

    private: str = 'private'
    group: str = 'group'
    supergroup: str = 'supergroup'
    channel: str = 'channel'