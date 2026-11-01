"""HTTP-клиент к эндпоинтам vpn-webapp (/sub/*)."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any
from urllib.parse import urlencode

import requests
from configparser import ConfigParser

from connect import logging
from users.methods import get_jwt_by_id


class VpnWebappApiError(Exception):
    def __init__(self, message: str, status_code: int | None = None) -> None:
        super().__init__(message)
        self.status_code = status_code


@dataclass(frozen=True)
class SubscriptionActionResult:
    ok: bool
    message: str


def _webapp_base_url() -> str:
    config = ConfigParser()
    config.read("config.ini")
    base_url = config["WebApp"].get("base_url", fallback="https://kuzmos.ru").strip()
    return base_url.rstrip("/")


def _subscription_token(telegram_id: int) -> str:
    token = get_jwt_by_id(telegram_id)
    if isinstance(token, bytes):
        return token.decode("utf-8")
    return str(token)


def _get(
    path: str,
    telegram_id: int,
    *,
    timeout: tuple[float, float] = (5, 120),
) -> requests.Response:
    base_url = _webapp_base_url()
    query = urlencode({"token": _subscription_token(telegram_id)})
    url = f"{base_url}{path}?{query}"
    try:
        return requests.get(url, allow_redirects=False, timeout=timeout)
    except requests.RequestException as error:
        logging.error("vpn-webapp GET %s failed: %s", path, error)
        raise VpnWebappApiError(
            "Не удалось связаться с сервером подписок. Попробуйте позже."
        ) from error


def _action_result_from_redirect(
    response: requests.Response,
    success_message: str,
) -> SubscriptionActionResult:
    if response.status_code in (302, 303, 307, 308):
        return SubscriptionActionResult(ok=True, message=success_message)
    if response.status_code == 503:
        body = (response.text or "").strip()
        return SubscriptionActionResult(
            ok=False,
            message=body or "Сервис временно недоступен. Попробуйте позже.",
        )
    if 200 <= response.status_code < 300:
        return SubscriptionActionResult(ok=True, message=success_message)
    raise VpnWebappApiError(
        f"Неожиданный ответ сервера ({response.status_code}).",
        status_code=response.status_code,
    )


def get_subscription_info(telegram_id: int) -> dict[str, Any]:
    """
    GET /sub/ — заголовки подписки (срок действия и ссылка на ЛК).
    """
    response = _get("/sub/", telegram_id, timeout=(5, 30))
    if response.status_code >= 400:
        raise VpnWebappApiError(
            f"Не удалось получить данные подписки ({response.status_code}).",
            status_code=response.status_code,
        )
    userinfo = response.headers.get("subscription-userinfo", "")
    web_page = response.headers.get("profile-web-page-url", "")
    expire_ts: int | None = None
    for part in userinfo.split(";"):
        part = part.strip()
        if part.startswith("expire="):
            raw = part.removeprefix("expire=").strip()
            if raw.isdigit():
                expire_ts = int(raw)
    return {
        "expire_timestamp": expire_ts,
        "profile_web_page_url": web_page,
        "has_subscription_body": bool(response.text and response.text.strip()),
    }


def transfer_other_server(telegram_id: int) -> SubscriptionActionResult:
    """GET /sub/transfer_other_server — перенос на другой сервер."""
    response = _get("/sub/transfer_other_server", telegram_id)
    return _action_result_from_redirect(
        response,
        "Сервер подписки обновлён. Откройте приложение VPN и обновите подписку "
        "(или заново импортируйте конфигурацию).",
    )


def resume_subscription(telegram_id: int) -> SubscriptionActionResult:
    """GET /sub/resume — возобновление приостановленной подписки."""
    response = _get("/sub/resume", telegram_id)
    return _action_result_from_redirect(
        response,
        "Подписка возобновлена. Настройте приложение по инструкции из личного кабинета.",
    )


def transfer_protocol(telegram_id: int) -> SubscriptionActionResult:
    """GET /sub/transfer_protocol — смена протокола Xray ↔ AmneziaWG."""
    response = _get("/sub/transfer_protocol", telegram_id)
    return _action_result_from_redirect(
        response,
        "Протокол изменён. Установите нужное приложение и настройте доступ заново.",
    )
