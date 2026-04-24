import requests
import json
import logging
from decimal import Decimal
from django.conf import settings
from .models import Payment, PaymentGatewayConfig, PaymentLog

logger = logging.getLogger(__name__)


class SSLCommerzGateway:
    """Handle all SSLCommerz payment gateway operations"""
    
    def __init__(self):
        try:
            self.config = PaymentGatewayConfig.objects.filter(is_active=True).first()
            if not self.config:
                raise Exception("SSLCommerz configuration not found")
        except Exception as e:
            logger.error(f"SSLCommerz Config Error: {str(e)}")
            self.config = None
    
    def get_store_id(self):
        return self.config.store_id if self.config else None
    
    def get_store_password(self):
        return self.config.store_password if self.config else None
    
    def get_session_api_url(self):
        return self.config.session_api_url if self.config else None
    
    def get_validation_api_url(self):
        return self.config.validation_api_url if self.config else None
    
    def initiate_payment(self, payment_obj, request):
        """Initiate payment request with SSLCommerz"""
        try:
            order = payment_obj.order
            buyer = order.buyer
            
            # Prepare request payload
            payload = {
                'store_id': self.get_store_id(),
                'store_passwd': self.get_store_password(),
                'total_amount': str(payment_obj.total_amount),
                'currency': 'BDT',
                'tran_id': str(payment_obj.id),  # Unique transaction ID
                'success_url': request.build_absolute_uri('/payment/success/'),
                'fail_url': request.build_absolute_uri('/payment/failed/'),
                'cancel_url': request.build_absolute_uri('/payment/cancelled/'),
                'cus_name': buyer.get_full_name() or buyer.username,
                'cus_email': buyer.email,
                'cus_phone': buyer.phone_number if hasattr(buyer, 'phone_number') else '',
                'ship_name': buyer.get_full_name() or buyer.username,
                'ship_email': buyer.email,
                'product_name': order.crop.crop_name,
                'product_quantity': str(int(order.quantity)),
                'product_category': 'Agricultural Product',
                'value_a': str(order.delivery_date) if order.delivery_date else '',
            }
            
            # Add optional fields
            if hasattr(buyer, 'phone_number'):
                payload['cus_phone'] = buyer.phone_number
            
            # Send request to SSLCommerz
            response = requests.post(
                self.get_session_api_url(),
                data=payload,
                timeout=10
            )
            
            # Log the request and response
            self._log_transaction(payment_obj, 'request', payload, response.json() if response.text else {})
            
            response_data = response.json() if response.text else {}
            
            if response.status_code == 200 and response_data.get('status') == 'success':
                # Store session information
                payment_obj.ssl_session_id = response_data.get('sessionkey')
                payment_obj.status = 'initiating'
                payment_obj.initiated_at = __import__('django.utils.timezone', fromlist=['now']).now()
                payment_obj.save()
                
                return {
                    'success': True,
                    'gateway_url': response_data.get('GatewayPageURL'),
                    'session_id': response_data.get('sessionkey'),
                }
            else:
                error_msg = response_data.get('failedreason', 'Unknown error')
                payment_obj.ssl_error_message = error_msg
                payment_obj.status = 'failed'
                payment_obj.save()
                
                return {
                    'success': False,
                    'error': error_msg
                }
        
        except requests.exceptions.RequestException as e:
            logger.error(f"SSLCommerz Request Error: {str(e)}")
            payment_obj.status = 'failed'
            payment_obj.ssl_error_message = f"Connection error: {str(e)}"
            payment_obj.save()
            return {'success': False, 'error': str(e)}
        
        except Exception as e:
            logger.error(f"SSLCommerz Payment Initiation Error: {str(e)}")
            return {'success': False, 'error': str(e)}
    
    def validate_payment(self, payment_obj, validation_id):
        """Validate payment after SSLCommerz response"""
        try:
            payload = {
                'store_id': self.get_store_id(),
                'store_passwd': self.get_store_password(),
                'val_id': validation_id,
            }
            
            # Send validation request
            response = requests.post(
                self.get_validation_api_url(),
                data=payload,
                timeout=10
            )
            
            response_data = response.json() if response.text else {}
            
            # Log the validation
            self._log_transaction(payment_obj, 'validation', payload, response_data)
            
            if response.status_code == 200 and response_data.get('status') == 'valid':
                # Payment is valid and completed
                payment_obj.ssl_validation_id = validation_id
                payment_obj.transaction_id = response_data.get('tran_id')
                payment_obj.status = 'completed'
                payment_obj.paid_amount = float(response_data.get('amount', payment_obj.total_amount))
                payment_obj.completed_at = __import__('django.utils.timezone', fromlist=['now']).now()
                payment_obj.save()
                
                return {
                    'success': True,
                    'tran_id': response_data.get('tran_id'),
                    'amount': response_data.get('amount'),
                }
            else:
                payment_obj.status = 'failed'
                payment_obj.ssl_error_message = response_data.get('status', 'Invalid validation')
                payment_obj.save()
                
                return {
                    'success': False,
                    'error': 'Payment validation failed'
                }
        
        except Exception as e:
            logger.error(f"SSLCommerz Validation Error: {str(e)}")
            payment_obj.status = 'failed'
            payment_obj.ssl_error_message = str(e)
            payment_obj.save()
            return {'success': False, 'error': str(e)}
    
    def _log_transaction(self, payment_obj, log_type, request_data, response_data):
        """Log transaction details"""
        try:
            PaymentLog.objects.create(
                payment=payment_obj,
                log_type=log_type,
                message=f"SSLCommerz {log_type}",
                request_data=request_data,
                response_data=response_data
            )
        except Exception as e:
            logger.error(f"Error logging payment transaction: {str(e)}")


def calculate_cod_amounts(total_amount):
    """Calculate COD amounts: 20% upfront, 80% at delivery"""
    upfront = float(total_amount) * 0.20
    remaining = float(total_amount) * 0.80
    return {
        'upfront': round(upfront, 2),
        'remaining': round(remaining, 2),
    }
