"""
Management command: Retrain the VMD-LSTM model using data from MySQL.

Fetches all CropPriceData rows from the database, preprocesses,
runs GA hyper-parameter search, trains the LSTM, and saves artefacts.

Usage:
    python manage.py retrain_price_model
    python manage.py retrain_price_model --ga-pop 12 --ga-gen 8
"""

from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = "Retrain the VMD-LSTM crop price model using data from MySQL."

    def add_arguments(self, parser):
        parser.add_argument("--ga-pop", type=int, default=8,
                            help="GA population size (default 8)")
        parser.add_argument("--ga-gen", type=int, default=5,
                            help="GA generations (default 5)")

    def handle(self, *args, **options):
        import os
        os.environ["KMP_DUPLICATE_LIB_OK"] = "TRUE"

        from farmer.models import CropPriceData
        row_count = CropPriceData.objects.count()
        if row_count == 0:
            self.stderr.write(self.style.ERROR(
                "No data in CropPriceData. Run 'python manage.py load_csv_to_db' first."
            ))
            return

        self.stdout.write(self.style.WARNING(
            f"Retraining on {row_count} rows from MySQL …"
        ))

        from ai_models.price_prediction.train import train_all
        _, meta = train_all(
            source="db",
            ga_pop=options["ga_pop"],
            ga_gen=options["ga_gen"],
            verbose=True,
        )

        m = meta["metrics"]
        self.stdout.write(self.style.SUCCESS(
            f"Retraining complete.  RMSE={m['rmse']:.5f}  "
            f"MAE={m['mae']:.5f}  MAPE={m['mape_pct']:.2f}%"
        ))
