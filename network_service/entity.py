from dataclasses import dataclass


@dataclass(frozen=True)
class NetworkServiceError:
    caption: str
    response: str | None = None