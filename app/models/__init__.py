from app.models.product import Product
from app.models.template import Template, CustomizationZone
from app.models.option_set import OptionSet, Option
from app.models.cart import Cart, CartItem, CustomizationSession

# Import all models to ensure they are registered with SQLAlchemy
__all__ = [
    'Product',
    'Template',
    'CustomizationZone',
    'OptionSet',
    'Option',
    'Cart',
    'CartItem',
    'CustomizationSession'
]
