from typing import Any

class Controller:
    pass

class Request:
    env: Any
    session: Any
    httprequest: Any
    params: dict[str, Any]
    cr: Any
    uid: int
    context: dict[str, Any]
    def render(self, template: str, qcontext: dict[str, Any] | None = None, **kwargs: Any) -> Response: ...
    def make_response(self, data: Any, headers: list[tuple[str, str]] | None = None, cookies: dict[str, str] | None = None) -> Response: ...
    def make_json_response(self, data: Any, headers: list[tuple[str, str]] | None = None, cookies: dict[str, str] | None = None, status: int = 200) -> Response: ...
    def redirect(self, url: str, code: int = 303) -> Response: ...
    def not_found(self) -> Response: ...

class Response:
    status_code: int
    headers: Any
    data: Any
    def __init__(self, response: Any = None, status: int | str = ..., headers: Any = None, mimetype: str | None = None, content_type: str | None = None) -> None: ...

request: Request

def route(route: str | list[str] = ..., *, type: str = "http", auth: str = "user", methods: list[str] | None = None, cors: str | None = None, csrf: bool = True, website: bool = False, sitemap: bool = True, readonly: bool = False, **kwargs: Any) -> Any: ...
