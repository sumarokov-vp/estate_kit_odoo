from .protocols import IApiClient


class ApiActionCaller:
    def __init__(self, api_client: IApiClient) -> None:
        self._api_client = api_client

    def call_action(self, records, action: str) -> None:
        for record in records:
            if record.external_id and self._api_client.is_configured:
                self._api_client.post(f"/properties/{record.external_id}/{action}", {})
