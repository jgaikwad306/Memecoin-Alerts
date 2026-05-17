from __future__ import annotations

import json
from typing import Any
from urllib.error import HTTPError
from urllib.request import Request, urlopen


class HttpRequestError(RuntimeError):
    pass


def _request_json(
    method: str,
    url: str,
    timeout: int,
    payload: dict[str, Any] | None = None,
) -> Any:
    data = None
    headers = {"Accept": "application/json"}
    if payload is not None:
        data = json.dumps(payload).encode("utf-8")
        headers["Content-Type"] = "application/json"

    request = Request(url, data=data, headers=headers, method=method)
    try:
        with urlopen(request, timeout=timeout) as response:
            body = response.read().decode("utf-8")
    except HTTPError as exc:
        error_body = exc.read().decode("utf-8", errors="replace")
        raise HttpRequestError(f"{method} {url} failed: {exc.code} {error_body}") from exc

    if not body:
        return None
    return json.loads(body)


def get_json(url: str, timeout: int) -> Any:
    return _request_json("GET", url, timeout)


def post_json(url: str, timeout: int, payload: dict[str, Any]) -> Any:
    return _request_json("POST", url, timeout, payload)
