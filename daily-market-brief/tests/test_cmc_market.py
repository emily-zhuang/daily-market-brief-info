import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parents[1]))
from cmc_market import extract_snapshot, format_usd, format_percent


class CmcMarketTests(unittest.TestCase):
    def test_formats_market_values(self):
        self.assertEqual(format_usd(1234567890), "$1.23B")
        self.assertEqual(format_percent(-1.234), "-1.23%")

    def test_extracts_top_assets_and_global_metrics(self):
        listings = {"data": [{
            "name": "Bitcoin", "symbol": "BTC", "cmc_rank": 1,
            "circulating_supply": 19000000,
            "quote": {"USD": {
                "price": 60000, "percent_change_1h": 0.1,
                "percent_change_24h": -1.2, "percent_change_7d": 3.4,
                "volume_24h": 1234567890, "market_cap": 1140000000000,
            }},
        }]}
        global_metrics = {"data": {"btc_dominance": 52.5, "eth_dominance": 18.1,
            "quote": {"USD": {"total_market_cap": 2200000000000,
                                "total_volume_24h": 90000000000}}}}

        snapshot = extract_snapshot(listings, global_metrics)
        self.assertEqual(snapshot["assets"][0]["symbol"], "BTC")
        self.assertEqual(snapshot["assets"][0]["change_24h"], "-1.20%")
        self.assertEqual(snapshot["global"]["btc_dominance"], "52.50%")
        self.assertEqual(snapshot["global"]["total_market_cap"], "$2.20T")


if __name__ == "__main__":
    unittest.main()
