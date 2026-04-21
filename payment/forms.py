from django import forms
from .models import Payment


class PaymentMethodForm(forms.Form):
    """Form for buyer to choose payment method"""
    
    PAYMENT_METHOD_CHOICES = (
        ('cod', 'Cash on Delivery - Pay 20% now, 80% at delivery'),
        ('sslcommerz', 'Online Payment - Pay full amount now via SSLCommerz'),
    )
    
    payment_method = forms.ChoiceField(
        choices=PAYMENT_METHOD_CHOICES,
        widget=forms.RadioSelect,
        label='Select Payment Method'
    )
