"""
Management command to train the VMD-LSTM crop-price prediction model.

Usage:
    python manage.py train_price_model
    python manage.py train_price_model --ga-pop 12 --ga-gen 8
"""

from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = "Train the VMD-LSTM crop price prediction model (GA hyper-parameter search)."

    def add_arguments(self, parser):
        parser.add_argument("--ga-pop", type=int, default=8,
                            help="GA population size (default 8)")
        parser.add_argument("--ga-gen", type=int, default=5,
                            help="GA generations (default 5)")

    def handle(self, *args, **options):
        # Lazy import so Django boot is not slowed down
        import os
        os.environ["KMP_DUPLICATE_LIB_OK"] = "TRUE"
        from ai_models.price_prediction.train import train_all

        self.stdout.write(self.style.WARNING("Starting price-model training …"))
        _, meta = train_all(
            ga_pop=options["ga_pop"],
            ga_gen=options["ga_gen"],
            verbose=True,
        )
        self.stdout.write(self.style.SUCCESS(
            f"Training complete.  RMSE={meta['metrics']['rmse']:.5f}  "
            f"MAE={meta['metrics']['mae']:.5f}  MAPE={meta['metrics']['mape_pct']:.2f}%"
        ))
