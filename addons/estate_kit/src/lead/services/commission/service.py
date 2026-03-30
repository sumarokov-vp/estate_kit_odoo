from .protocols import IMlsRateProvider, IRateProvider


class CommissionService:
    def __init__(
        self,
        rate_provider: IRateProvider,
        mls_rate_provider: IMlsRateProvider,
    ) -> None:
        self._rate_provider = rate_provider
        self._mls_rate_provider = mls_rate_provider

    def get_rate(self, lead) -> float:
        mls_rate = self._mls_rate_provider.get_rate(lead)
        if mls_rate is not None:
            return mls_rate
        return self._rate_provider.get_rate(lead)
