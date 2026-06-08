from __future__ import annotations

import unittest

import pandas as pd

from app.services.csv_cleaner import clean_csv_upload
from app.services.ml_models import _rto_training_rows


class OrderingTests(unittest.TestCase):
    def test_clean_csv_upload_sorts_rows_by_order_date(self):
        csv_bytes = b"""order date,sku,product name,customer state,status,order source,listed price,discounted price,quantity
2024-01-03,SKU-3,Item 3,KA,DELIVERED,natural,100,90,1
2024-01-01,SKU-1,Item 1,KA,RTO,ad,100,90,1
2024-01-02,SKU-2,Item 2,KA,DELIVERED,natural,100,90,1
"""

        cleaned, warnings = clean_csv_upload(csv_bytes)

        self.assertEqual(warnings, [])
        self.assertEqual(cleaned["order_date"].tolist(), ["2024-01-01", "2024-01-02", "2024-01-03"])

    def test_rto_training_rows_use_only_prior_rows_for_history(self):
        df = pd.DataFrame(
            [
                {
                    "order_date": "2024-01-02",
                    "sku": "SKU-1",
                    "customer_state": "KA",
                    "order_source": "natural",
                    "discounted_price": 90,
                    "quantity": 1,
                    "status": "DELIVERED",
                },
                {
                    "order_date": "2024-01-01",
                    "sku": "SKU-1",
                    "customer_state": "KA",
                    "order_source": "natural",
                    "discounted_price": 90,
                    "quantity": 1,
                    "status": "RTO",
                },
            ]
        )

        rows = _rto_training_rows(df)

        self.assertEqual(rows["order_date"].dt.strftime("%Y-%m-%d").tolist(), ["2024-01-01", "2024-01-02"])
        self.assertEqual(rows.loc[0, "sku_order_count"], 0)
        self.assertEqual(rows.loc[0, "sku_historical_rto_rate"], 0.0)
        self.assertEqual(rows.loc[1, "sku_order_count"], 1)
        self.assertEqual(rows.loc[1, "sku_historical_rto_rate"], 1.0)
