import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from analytics_engine.checklist_engine import generate_daily_checklist
from analytics_engine.csv_normalizer import normalize_order_row
from analytics_engine.margin_calculator import break_even_price, compute_order_profit
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

    def test_margin_and_checklist_ordering(self):
        rto_res = compute_order_profit(999, 400, 65, 50, is_rto=True, reverse_shipping_fee=55)
        self.assertEqual(rto_res["net_profit"], -120.0)
        self.assertGreater(break_even_price(400, 65, 50), 515.0)
        items = generate_daily_checklist([
            {"sku": "SKU-A", "rto_rate": 0.48, "margin_pct": 12.0, "monthly_revenue": 50000},
            {"sku": "SKU-B", "rto_rate": 0.10, "margin_pct": 4.0, "monthly_revenue": 20000},
        ])
        self.assertEqual(items[0]["sku"], "SKU-A")
        self.assertEqual(items[0]["priority"], "critical")

if __name__ == "__main__":
    unittest.main()
