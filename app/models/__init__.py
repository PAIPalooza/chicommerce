from app.models.product import Product
from app.models.template import Template, CustomizationZone
from app.models.option_set import OptionSet, Option
from app.models.cart import Cart, CartItem, CustomizationSession
from app.models.order import Order, OrderItem, PaymentEvent, OrderStatus, PaymentProvider
from app.models.webhook_log import WebhookLog, WebhookStatus
from app.models.preview import PreviewJob, PreviewStatus

# Import all models to ensure they are registered with SQLAlchemy
__all__ = [
    'Product',
    'Template',
    'CustomizationZone',
    'OptionSet',
    'Option',
    'Cart',
    'CartItem',
    'CustomizationSession',
    'Order',
    'OrderItem',
    'PaymentEvent',
    'OrderStatus',
    'PaymentProvider',
    'WebhookLog',
    'WebhookStatus',
    'PreviewJob',
    'PreviewStatus'
]
