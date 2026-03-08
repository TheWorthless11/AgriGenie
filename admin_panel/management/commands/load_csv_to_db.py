"""
Management command: Load the master CSV into the CropPriceData MySQL table.

Usage:
    python manage.py load_csv_to_db
    python manage.py load_csv_to_db --csv path/to/custom.csv
    python manage.py load_csv_to_db --clear   # wipe table first
"""

import os
import pandas as pd
from django.core.management.base import BaseCommand
from django.db import IntegrityError


# CSV column → model field mapping
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


class Command(BaseCommand):
    help = "Load historical crop-price CSV into the CropPriceData MySQL table."

    def add_arguments(self, parser):
        default_csv = os.path.join(
            os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))),
            "ai_models", "combined_agriculture_prices.csv",
        )
        parser.add_argument(
            "--csv", type=str, default=default_csv,
            help="Path to the CSV file (default: ai_models/combined_agriculture_prices.csv)",
        )
        parser.add_argument(
            "--clear", action="store_true",
            help="Delete all existing rows before loading",
        )

    def handle(self, *args, **options):
        from farmer.models import CropPriceData

        csv_path = options["csv"]
        if not os.path.isfile(csv_path):
            self.stderr.write(self.style.ERROR(f"CSV not found: {csv_path}"))
            return

        if options["clear"]:
            deleted, _ = CropPriceData.objects.all().delete()
            self.stdout.write(self.style.WARNING(f"Cleared {deleted} existing rows."))

        df = pd.read_csv(csv_path)
        # Normalise Variety casing (same logic as preprocessing)
        df["Variety"] = df["Variety"].str.strip().str.title().str.replace(" ", "_")
        # Fill sparse NaNs with 0 to avoid DB issues
        df = df.fillna(0)

        inserted = 0
        skipped = 0

        for _, row in df.iterrows():
            fields = {model_field: row[csv_col] for csv_col, model_field in COL_MAP.items()}
            # Convert numpy types to native Python types
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
            _, created = CropPriceData.objects.get_or_create(
                **lookup, defaults=fields,
            )
            if created:
                inserted += 1
            else:
                skipped += 1

        self.stdout.write(self.style.SUCCESS(
            f"Done — inserted: {inserted}, skipped (duplicates): {skipped}"
        ))
