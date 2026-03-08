"""
Management command: Append new monthly actual data to CropPriceData.

Accepts data via a CSV file containing ONLY the new month(s) to add.
Validates against duplicates. Never inserts predicted data.

Usage:
    python manage.py append_monthly_data --csv path/to/jan_2026.csv
"""

import os
import pandas as pd
from django.core.management.base import BaseCommand

# Same column mapping as load_csv_to_db
COL_MAP = {
    "Year": "year",
    "Month": "month",
    "Market": "market",
    "Commodity": "commodity",
    "Variety": "variety",
    "Price_per_KG": "price_per_kg",
    "Avg_Temp_C": "avg_temp_c",
    "Max_Temp_C": "max_temp_c",
    "Min_Temp_C": "min_temp_c",
    "Rainfall_mm": "rainfall_mm",
    "Cumulative_Rainfall_mm": "cumulative_rainfall_mm",
    "Flood": "flood",
    "Drought": "drought",
    "Yield_per_Hectare": "yield_per_hectare",
    "Production_tonnes": "production_tonnes",
    "Area_Hectares": "area_hectares",
    "Import_tonnes": "import_tonnes",
    "Export_tonnes": "export_tonnes",
    "Fertilizer_Cost": "fertilizer_cost",
    "Seed_Cost": "seed_cost",
    "Labor_Cost": "labor_cost",
    "Fuel_Cost": "fuel_cost",
    "Inflation": "inflation",
    "CPI": "cpi",
    "Lag1_Price": "lag1_price",
    "Lag2_Price": "lag2_price",
}

REQUIRED_CSV_COLS = list(COL_MAP.keys())


class Command(BaseCommand):
    help = "Append new monthly actual crop-price data to MySQL (no predicted rows)."

    def add_arguments(self, parser):
        parser.add_argument(
            "--csv", type=str, required=True,
            help="Path to a CSV containing new monthly data to insert.",
        )

    def handle(self, *args, **options):
        from farmer.models import CropPriceData

        csv_path = options["csv"]
        if not os.path.isfile(csv_path):
            self.stderr.write(self.style.ERROR(f"File not found: {csv_path}"))
            return

        df = pd.read_csv(csv_path)

        # ---------- validate columns ----------
        missing = [c for c in REQUIRED_CSV_COLS if c not in df.columns]
        if missing:
            self.stderr.write(self.style.ERROR(
                f"CSV is missing required columns: {missing}"
            ))
            return

        # Normalise Variety casing
        df["Variety"] = df["Variety"].str.strip().str.title().str.replace(" ", "_")
        df = df.fillna(0)

        inserted = 0
        skipped = 0

        for _, row in df.iterrows():
            fields = {model_field: row[csv_col] for csv_col, model_field in COL_MAP.items()}
            for k, v in fields.items():
                if hasattr(v, "item"):
                    fields[k] = v.item()

            lookup = {
                "year": fields["year"],
                "month": fields["month"],
                "market": fields["market"],
                "commodity": fields["commodity"],
                "variety": fields["variety"],
            }

            if CropPriceData.objects.filter(**lookup).exists():
                skipped += 1
                continue

            CropPriceData.objects.create(**fields)
            inserted += 1

        self.stdout.write(self.style.SUCCESS(
            f"Done — inserted: {inserted}, skipped (duplicates): {skipped}"
        ))
        if inserted > 0:
            self.stdout.write(self.style.NOTICE(
                "Run 'python manage.py retrain_price_model' to retrain on the updated dataset."
            ))
