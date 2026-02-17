"""Pricing service for calculating product and cart prices."""
from decimal import Decimal
from typing import List, Dict, Any


class TaxService:
    """Stub tax calculation service with fixed rate."""

    def __init__(self, tax_rate: Decimal = Decimal("0.10")):
        """
        Initialize tax service.

        Args:
            tax_rate: Tax rate as decimal (default 0.10 = 10%)
        """
        self.tax_rate = tax_rate

    def calculate_tax(self, subtotal: Decimal) -> Decimal:
        """
        Calculate tax for given subtotal.

        Args:
            subtotal: Amount to calculate tax on

        Returns:
            Tax amount rounded to 2 decimal places
        """
        tax = subtotal * self.tax_rate
        return tax.quantize(Decimal("0.01"))


class ShippingService:
    """Stub shipping calculation service with flat rate."""

    def __init__(self, flat_rate: Decimal = Decimal("8.99")):
        """
        Initialize shipping service.

        Args:
            flat_rate: Flat shipping rate (default $8.99)
        """
        self.flat_rate = flat_rate

    def calculate_shipping(self, subtotal: Decimal, shipping_required: bool = True) -> Decimal:
        """
        Calculate shipping cost.

        Args:
            subtotal: Order subtotal
            shipping_required: Whether shipping is required

        Returns:
            Shipping cost (0 if not required)
        """
        if not shipping_required:
            return Decimal("0.00")

        # Free shipping for orders over $100
        if subtotal >= Decimal("100.00"):
            return Decimal("0.00")

        return self.flat_rate


class PriceCalculation:
    """Result of price calculation."""

    def __init__(
        self,
        base_price: Decimal,
        option_surcharges: Decimal,
        subtotal: Decimal,
        tax: Decimal,
        shipping: Decimal,
        total: Decimal
    ):
        self.base_price = base_price
        self.option_surcharges = option_surcharges
        self.subtotal = subtotal
        self.tax = tax
        self.shipping = shipping
        self.total = total


class PricingService:
    """Service for calculating product and cart pricing."""

    def __init__(self, tax_service: TaxService, shipping_service: ShippingService):
        """
        Initialize pricing service with dependencies.

        Args:
            tax_service: Service for tax calculation
            shipping_service: Service for shipping calculation
        """
        self.tax_service = tax_service
        self.shipping_service = shipping_service

    def calculate_item_price(
        self,
        base_price: Decimal,
        options: List[Dict[str, Any]]
    ) -> Decimal:
        """
        Calculate price for a single item with options.

        Args:
            base_price: Base product price
            options: List of selected options with price_delta

        Returns:
            Total item price (base + option surcharges)
        """
        option_surcharges = sum(
            Decimal(str(opt.get("price_delta", 0)))
            for opt in options
        )
        return base_price + option_surcharges

    def calculate_cart_total(
        self,
        items: List[Dict[str, Any]],
        shipping_required: bool = True
    ) -> PriceCalculation:
        """
        Calculate total price for cart with all items.

        Formula: Price = base_price + sum(option.price_delta) + tax + shipping

        Args:
            items: List of cart items with base_price, options, quantity
            shipping_required: Whether shipping is required

        Returns:
            PriceCalculation with complete breakdown
        """
        # Calculate base prices and option surcharges
        total_base_price = Decimal("0.00")
        total_option_surcharges = Decimal("0.00")

        for item in items:
            base_price = item["base_price"]
            quantity = item["quantity"]
            options = item.get("options", [])

            # Calculate option surcharges for this item
            item_option_surcharges = sum(
                Decimal(str(opt.get("price_delta", 0)))
                for opt in options
            )

            # Add to totals (multiply by quantity)
            total_base_price += base_price * quantity
            total_option_surcharges += item_option_surcharges * quantity

        # Calculate subtotal
        subtotal = total_base_price + total_option_surcharges

        # Calculate tax
        tax = self.tax_service.calculate_tax(subtotal)

        # Calculate shipping
        shipping = self.shipping_service.calculate_shipping(
            subtotal=subtotal,
            shipping_required=shipping_required
        )

        # Calculate total
        total = subtotal + tax + shipping

        return PriceCalculation(
            base_price=total_base_price,
            option_surcharges=total_option_surcharges,
            subtotal=subtotal,
            tax=tax,
            shipping=shipping,
            total=total
        )
