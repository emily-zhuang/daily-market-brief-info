from __future__ import annotations


def format_usd(value: float | int | None) -> str:
    if value is None:
        return "N/A"
    value = float(value)
    for divisor, suffix in ((1_000_000_000_000, "T"), (1_000_000_000, "B"), (1_000_000, "M")):
        if abs(value) >= divisor:
            return f"${value / divisor:.2f}{suffix}"
    return f"${value:,.2f}"


def format_percent(value: float | int | None) -> str:
    return "N/A" if value is None else f"{float(value):.2f}%"


def format_supply(value: float | int | None) -> str:
    return "N/A" if value is None else f"{float(value):,.0f}"


def extract_snapshot(listings_payload: dict, global_payload: dict) -> dict:
    assets = []
    for asset in listings_payload.get("data", []):
        quote = asset.get("quote", {}).get("USD", {})
        assets.append({
            "rank": asset.get("cmc_rank", "N/A"),
            "name": asset.get("name", "N/A"),
            "symbol": asset.get("symbol", "N/A"),
            "price": format_usd(quote.get("price")),
            "change_1h": format_percent(quote.get("percent_change_1h")),
            "change_24h": format_percent(quote.get("percent_change_24h")),
            "change_7d": format_percent(quote.get("percent_change_7d")),
            "market_cap": format_usd(quote.get("market_cap")),
            "volume_24h": format_usd(quote.get("volume_24h")),
            "supply": format_supply(asset.get("circulating_supply")),
        })
    data = global_payload.get("data", {})
    quote = data.get("quote", {}).get("USD", {})
    return {
        "assets": assets,
        "global": {
            "total_market_cap": format_usd(quote.get("total_market_cap")),
            "total_volume_24h": format_usd(quote.get("total_volume_24h")),
            "btc_dominance": format_percent(data.get("btc_dominance")),
            "eth_dominance": format_percent(data.get("eth_dominance")),
            "active_cryptocurrencies": str(data.get("active_cryptocurrencies", "N/A")),
        },
    }
