import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from analytics_engine.anomaly_detector import detect_spikes
from analytics_engine.checklist_engine import generate_daily_checklist
from analytics_engine.cohort_metrics import aggregate_weekly_series
from analytics_engine.csv_normalizer import normalize_order_row
from analytics_engine.inventory_alerts import days_of_cover, is_dead_stock, needs_reorder
from analytics_engine.margin_calculator import break_even_price, compute_order_profit
from analytics_engine.pincode_profiler import flagged_cod_pincodes, profile_pincodes
from analytics_engine.report_formatter import build_dashboard_summary
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
            {"sku": "SKU-A", "rto_rate": 0.48, "margin_pct": 12.0, "monthly_revenue": 50000, "stock_on_hand": 10, "avg_daily_units": 3.0},
            {"sku": "SKU-B", "rto_rate": 0.10, "margin_pct": 4.0, "monthly_revenue": 20000},
        ], high_rto_pincodes=["835215"])
        self.assertEqual(items[0]["sku"], "SKU-A")
        self.assertEqual(items[0]["priority"], "critical")
        self.assertTrue(any(i["category"] == "inventory" for i in items))

    def test_inventory_and_pincode_profiler(self):
        self.assertIsNone(days_of_cover(25, 0))
        self.assertTrue(needs_reorder(18, 2.0))
        self.assertTrue(is_dead_stock(15, 1))
        orders = [{"pincode": "835215", "status": "rto"}] * 3 + [{"pincode": "835215", "status": "delivered"}] * 3
        profiles = profile_pincodes(orders, min_orders=5)
        self.assertEqual(profiles["835215"]["rto_rate"], 0.5)
        self.assertEqual(flagged_cod_pincodes(orders, min_orders=5), ["835215"])

    def test_cohorts_anomalies_and_summary(self):
        series = aggregate_weekly_series([
            {"week": "2026-W28", "orders": 100, "rtos": 12},
            {"week": "2026-W29", "orders": 120, "rtos": 15},
            {"week": "2026-W30", "orders": 150, "rtos": 18},
        ])
        self.assertEqual(series[1]["orders_wow_pct"], 20.0)
        self.assertEqual(detect_spikes([10, 10, 10, 10]), [])
        self.assertEqual(detect_spikes([10, 11, 10, 9, 10, 45]), [5])
        summary = build_dashboard_summary(100, 15, float("nan"), [])
        self.assertEqual(summary["net_profit_inr"], 0.0)

if __name__ == "__main__":
    unittest.main()
