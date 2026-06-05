class PriceFormatter:
    def format(self, prop) -> str:
        if not prop.price:
            return ""
        symbol = prop.currency_id.symbol or ""
        position = prop.currency_id.position or "after"
        amount = f"{prop.price:,.0f}".replace(",", " ")
        if position == "before":
            return f"{symbol} {amount}".strip()
        return f"{amount} {symbol}".strip()
