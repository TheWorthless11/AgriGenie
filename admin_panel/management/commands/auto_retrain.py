"""
Management command: Automatic retraining pipeline.

Detects new data in the CSV, syncs to MySQL, retrains the VMD-LSTM model
with versioned artifact saving, and updates pipeline metadata.

Usage:
    python manage.py auto_retrain
    python manage.py auto_retrain --force
    python manage.py auto_retrain --ga-pop 12 --ga-gen 8
    python manage.py auto_retrain --csv path/to/custom.csv
"""

import os
import logging

from django.core.management.base import BaseCommand

logger = logging.getLogger("agrigenie.pipeline")


class Command(BaseCommand):
    help = (
        "Detect new monthly data in CSV, sync to MySQL, and retrain "
        "the VMD-LSTM crop price model with versioned artifact saving."
    )

    def add_arguments(self, parser):
        default_csv = os.path.join(
            os.path.dirname(os.path.dirname(os.path.dirname(
                os.path.dirname(os.path.abspath(__file__))
            ))),
            "ai_models", "combined_agriculture_prices.csv",
        )
        parser.add_argument(
            "--csv", type=str, default=default_csv,
            help="Path to the CSV file (default: ai_models/combined_agriculture_prices.csv)",
        )
        parser.add_argument(
            "--ga-pop", type=int, default=8,
            help="GA population size (default 8)",
        )
        parser.add_argument(
            "--ga-gen", type=int, default=5,
            help="GA generations (default 5)",
        )
        parser.add_argument(
            "--force", action="store_true",
            help="Force retrain even if no new data detected",
        )

    def handle(self, *args, **options):
        os.environ["KMP_DUPLICATE_LIB_OK"] = "TRUE"

        csv_path = options["csv"]
        if not os.path.isfile(csv_path):
            self.stderr.write(self.style.ERROR(f"CSV not found: {csv_path}"))
            return

        self.stdout.write(self.style.WARNING("╔══════════════════════════════════════╗"))
        self.stdout.write(self.style.WARNING("║   Auto-Retrain Pipeline Starting     ║"))
        self.stdout.write(self.style.WARNING("╚══════════════════════════════════════╝"))

        from ai_models.price_prediction.pipeline import run_pipeline

        try:
            result = run_pipeline(
                csv_path=csv_path,
                ga_pop=options["ga_pop"],
                ga_gen=options["ga_gen"],
                force=options["force"],
                verbose=True,
            )
        except Exception as e:
            logger.exception("Pipeline failed")
            self.stderr.write(self.style.ERROR(f"Pipeline failed: {e}"))
            return

        if result["status"] == "skipped":
            self.stdout.write(self.style.NOTICE(
                "No new data detected — model is up to date."
            ))
        else:
            m = result["metrics"]
            self.stdout.write(self.style.SUCCESS(
                f"\nModel v{result['model_version']} trained successfully."
            ))
            self.stdout.write(self.style.SUCCESS(
                f"  Rows inserted: {result['rows_inserted']}"
            ))
            self.stdout.write(self.style.SUCCESS(
                f"  RMSE={m['rmse']:.5f}  MAE={m['mae']:.5f}  MAPE={m['mape_pct']:.2f}%"
            ))
            self.stdout.write(self.style.SUCCESS(
                "  Predictor cache invalidated — next API call uses new model."
            ))
