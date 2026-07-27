import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from analytics_engine.csv_normalizer import normalize_order_row
from analytics_engine.rto_risk import predict_rto_probability, risk_band
from analytics_engine.sku_scoring import classify_sku_tier, compute_sku_score

class TestAnalyticsEngine(unittest.TestCase):
    def test_csv_normalizer_aliases_and_currency(self):
        row = {
            "Sub Order No": "ORD-901",
            "Product SKU": "kurt-01",
            "Order Status": "Delivered",
            "Supplier Listed Price": "₹1,299.50",
            "Payment Type": "Cash on Delivery",
        }
        norm = normalize_order_row(row)
        self.assertEqual(norm["sku"], "KURT-01")
        self.assertEqual(norm["amount"], 1299.5)
        self.assertEqual(norm["payment_mode"], "cod")

    def test_sku_scoring_and_rto_risk(self):
        self.assertEqual(compute_sku_score(0, 0, 15.0), 0.0)
        score = compute_sku_score(80, 5, 22.0)
        self.assertEqual(classify_sku_tier(score, 5 / 80), "star")
        prob = predict_rto_probability("cod", 2000, 0.20, prior_buyer_rtos=1)
        self.assertEqual(risk_band(prob), "high")

if __name__ == "__main__":
    unittest.main()
