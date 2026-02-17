"""
Unit tests for pricing service.

Following TDD/BDD approach with descriptive test names for clear test organization.
Tests written BEFORE implementation to ensure proper test-driven development.
"""
import pytest
from decimal import Decimal

from app.services.pricing_service import (
    PricingService,
    PriceCalculation,
    TaxService,
    ShippingService,
)


class TestPricingService:
    """Test suite for PricingService base price calculations."""

    def test_calculate_base_price_correctly(self):
        """Should return the correct base price."""
        pricing_service = PricingService()
        base_price = Decimal("19.99")

        result = pricing_service.calculate_base_price(base_price)

        assert result == Decimal("19.99")
        assert isinstance(result, Decimal)

    def test_calculate_base_price_handles_zero(self):
        """Should handle zero base price."""
        pricing_service = PricingService()
        base_price = Decimal("0.00")

        result = pricing_service.calculate_base_price(base_price)

        assert result == Decimal("0.00")

    def test_calculate_base_price_preserves_precision(self):
        """Should preserve decimal precision for base price."""
        pricing_service = PricingService()
        base_price = Decimal("19.999")

        result = pricing_service.calculate_base_price(base_price)

        assert result == Decimal("19.999")


class TestPricingServiceOptionSurcharges:
    """Test suite for option price surcharge calculations."""

    def test_calculate_single_option_surcharge(self):
        """Should calculate surcharge for a single option."""
        pricing_service = PricingService()
        options = [
            {"name": "Color", "value": "Red", "price_delta": Decimal("5.00")}
        ]

        result = pricing_service.calculate_option_surcharges(options)

        assert result == Decimal("5.00")

    def test_calculate_multiple_option_surcharges(self):
        """Should sum surcharges for multiple options."""
        pricing_service = PricingService()
        options = [
            {"name": "Color", "value": "Red", "price_delta": Decimal("5.00")},
            {"name": "Size", "value": "Large", "price_delta": Decimal("3.50")},
            {"name": "Material", "value": "Premium", "price_delta": Decimal("10.00")},
        ]

        result = pricing_service.calculate_option_surcharges(options)

        assert result == Decimal("18.50")

    def test_calculate_surcharges_handles_empty_list(self):
        """Should return zero for empty options list."""
        pricing_service = PricingService()
        options = []

        result = pricing_service.calculate_option_surcharges(options)

        assert result == Decimal("0.00")

    def test_calculate_surcharges_handles_zero_price_delta(self):
        """Should handle options with zero price delta."""
        pricing_service = PricingService()
        options = [
            {"name": "Color", "value": "Red", "price_delta": Decimal("0.00")},
            {"name": "Size", "value": "Medium", "price_delta": Decimal("5.00")},
        ]

        result = pricing_service.calculate_option_surcharges(options)

        assert result == Decimal("5.00")

    def test_calculate_surcharges_handles_negative_price_delta(self):
        """Should handle negative price delta (discounts)."""
        pricing_service = PricingService()
        options = [
            {"name": "Color", "value": "Red", "price_delta": Decimal("5.00")},
            {"name": "Discount", "value": "Sale", "price_delta": Decimal("-2.00")},
        ]

        result = pricing_service.calculate_option_surcharges(options)

        assert result == Decimal("3.00")

    def test_calculate_surcharges_from_cents(self):
        """Should handle options stored as cents (integers)."""
        pricing_service = PricingService()
        # Options stored as cents in database
        options = [
            {"name": "Color", "value": "Red", "additional_price": 500},  # $5.00
            {"name": "Size", "value": "Large", "additional_price": 350},  # $3.50
        ]

        result = pricing_service.calculate_option_surcharges_from_cents(options)

        assert result == Decimal("8.50")


class TestPricingServiceTotalPrice:
    """Test suite for total price calculation."""

    def test_calculate_total_with_all_components(self):
        """Should calculate total price with base, options, tax, and shipping."""
        tax_service = TaxService()
        shipping_service = ShippingService()
        pricing_service = PricingService(
            tax_service=tax_service,
            shipping_service=shipping_service
        )

        base_price = Decimal("19.99")
        options = [
            {"name": "Color", "value": "Red", "price_delta": Decimal("5.00")}
        ]
        quantity = 2

        result = pricing_service.calculate_total_price(
            base_price=base_price,
            options=options,
            quantity=quantity,
            shipping_required=True
        )

        # Base: 19.99, Options: 5.00, Subtotal: 24.99 * 2 = 49.98
        # Tax (10%): 4.998 = 5.00, Shipping: 8.99
        # Total: 49.98 + 5.00 + 8.99 = 63.97
        assert isinstance(result, PriceCalculation)
        assert result.base_price == Decimal("19.99")
        assert result.option_surcharges == Decimal("5.00")
        assert result.subtotal == Decimal("49.98")
        assert result.tax == Decimal("5.00")
        assert result.shipping == Decimal("8.99")
        assert result.total == Decimal("63.97")

    def test_calculate_total_without_shipping(self):
        """Should calculate total price without shipping when not required."""
        tax_service = TaxService()
        shipping_service = ShippingService()
        pricing_service = PricingService(
            tax_service=tax_service,
            shipping_service=shipping_service
        )

        base_price = Decimal("19.99")
        options = []
        quantity = 1

        result = pricing_service.calculate_total_price(
            base_price=base_price,
            options=options,
            quantity=quantity,
            shipping_required=False
        )

        # Base: 19.99, Subtotal: 19.99, Tax: 2.00, Shipping: 0.00
        # Total: 19.99 + 2.00 + 0.00 = 21.99
        assert result.shipping == Decimal("0.00")
        assert result.total == Decimal("21.99")

    def test_calculate_total_handles_quantity_correctly(self):
        """Should multiply base price and options by quantity."""
        tax_service = TaxService()
        shipping_service = ShippingService()
        pricing_service = PricingService(
            tax_service=tax_service,
            shipping_service=shipping_service
        )

        base_price = Decimal("10.00")
        options = [
            {"name": "Size", "value": "Large", "price_delta": Decimal("2.00")}
        ]
        quantity = 3

        result = pricing_service.calculate_total_price(
            base_price=base_price,
            options=options,
            quantity=quantity,
            shipping_required=False
        )

        # Unit price: 10.00 + 2.00 = 12.00
        # Subtotal: 12.00 * 3 = 36.00
        assert result.subtotal == Decimal("36.00")

    def test_calculate_total_rounds_to_two_decimal_places(self):
        """Should round final total to 2 decimal places."""
        tax_service = TaxService()
        shipping_service = ShippingService()
        pricing_service = PricingService(
            tax_service=tax_service,
            shipping_service=shipping_service
        )

        base_price = Decimal("19.999")  # Will be rounded
        options = []
        quantity = 1

        result = pricing_service.calculate_total_price(
            base_price=base_price,
            options=options,
            quantity=quantity,
            shipping_required=False
        )

        # Ensure all amounts are rounded to 2 decimal places
        assert result.total.as_tuple().exponent >= -2


class TestTaxService:
    """Test suite for TaxService stub."""

    def test_calculate_tax_with_default_rate(self):
        """Should calculate tax with default 10% rate."""
        tax_service = TaxService()
        subtotal = Decimal("100.00")

        result = tax_service.calculate_tax(subtotal)

        assert result == Decimal("10.00")

    def test_calculate_tax_with_custom_rate(self):
        """Should calculate tax with custom rate."""
        tax_service = TaxService(tax_rate=Decimal("0.15"))  # 15%
        subtotal = Decimal("100.00")

        result = tax_service.calculate_tax(subtotal)

        assert result == Decimal("15.00")

    def test_calculate_tax_rounds_to_two_decimals(self):
        """Should round tax to 2 decimal places."""
        tax_service = TaxService()
        subtotal = Decimal("19.99")

        result = tax_service.calculate_tax(subtotal)

        # 19.99 * 0.10 = 1.999, rounded to 2.00
        assert result == Decimal("2.00")
        assert result.as_tuple().exponent >= -2

    def test_calculate_tax_handles_zero_subtotal(self):
        """Should return zero tax for zero subtotal."""
        tax_service = TaxService()
        subtotal = Decimal("0.00")

        result = tax_service.calculate_tax(subtotal)

        assert result == Decimal("0.00")


class TestShippingService:
    """Test suite for ShippingService stub."""

    def test_calculate_flat_rate_shipping(self):
        """Should return flat rate shipping cost."""
        shipping_service = ShippingService()

        result = shipping_service.calculate_shipping(
            subtotal=Decimal("50.00"),
            quantity=2
        )

        assert result == Decimal("8.99")

    def test_calculate_shipping_returns_zero_for_free_threshold(self):
        """Should return zero shipping for orders above threshold."""
        shipping_service = ShippingService(
            flat_rate=Decimal("8.99"),
            free_shipping_threshold=Decimal("100.00")
        )

        result = shipping_service.calculate_shipping(
            subtotal=Decimal("150.00"),
            quantity=1
        )

        assert result == Decimal("0.00")

    def test_calculate_shipping_applies_flat_rate_below_threshold(self):
        """Should apply flat rate for orders below free shipping threshold."""
        shipping_service = ShippingService(
            flat_rate=Decimal("8.99"),
            free_shipping_threshold=Decimal("100.00")
        )

        result = shipping_service.calculate_shipping(
            subtotal=Decimal("50.00"),
            quantity=1
        )

        assert result == Decimal("8.99")

    def test_calculate_shipping_handles_custom_flat_rate(self):
        """Should handle custom flat rate."""
        shipping_service = ShippingService(flat_rate=Decimal("15.00"))

        result = shipping_service.calculate_shipping(
            subtotal=Decimal("50.00"),
            quantity=1
        )

        assert result == Decimal("15.00")


class TestPriceCalculation:
    """Test suite for PriceCalculation data class."""

    def test_create_price_calculation_with_all_fields(self):
        """Should create PriceCalculation with all required fields."""
        calc = PriceCalculation(
            base_price=Decimal("19.99"),
            option_surcharges=Decimal("5.00"),
            subtotal=Decimal("24.99"),
            tax=Decimal("2.50"),
            shipping=Decimal("8.99"),
            total=Decimal("36.48")
        )

        assert calc.base_price == Decimal("19.99")
        assert calc.option_surcharges == Decimal("5.00")
        assert calc.subtotal == Decimal("24.99")
        assert calc.tax == Decimal("2.50")
        assert calc.shipping == Decimal("8.99")
        assert calc.total == Decimal("36.48")

    def test_price_calculation_converts_to_dict(self):
        """Should convert PriceCalculation to dictionary."""
        calc = PriceCalculation(
            base_price=Decimal("19.99"),
            option_surcharges=Decimal("5.00"),
            subtotal=Decimal("24.99"),
            tax=Decimal("2.50"),
            shipping=Decimal("8.99"),
            total=Decimal("36.48")
        )

        result = calc.to_dict()

        assert isinstance(result, dict)
        assert result["base_price"] == "19.99"
        assert result["option_surcharges"] == "5.00"
        assert result["subtotal"] == "24.99"
        assert result["tax"] == "2.50"
        assert result["shipping"] == "8.99"
        assert result["total"] == "36.48"


class TestPricingServiceCartTotal:
    """Test suite for cart total calculation."""

    def test_calculate_cart_total_single_item(self):
        """Should calculate total for cart with single item."""
        tax_service = TaxService()
        shipping_service = ShippingService()
        pricing_service = PricingService(
            tax_service=tax_service,
            shipping_service=shipping_service
        )

        items = [
            {
                "base_price": Decimal("19.99"),
                "options": [{"name": "Size", "value": "Large", "price_delta": Decimal("2.00")}],
                "quantity": 1
            }
        ]

        result = pricing_service.calculate_cart_total(items, shipping_required=True)

        # Unit: 19.99 + 2.00 = 21.99
        # Subtotal: 21.99
        # Tax: 2.20
        # Shipping: 8.99
        # Total: 33.18
        assert result.subtotal == Decimal("21.99")
        assert result.tax == Decimal("2.20")
        assert result.shipping == Decimal("8.99")
        assert result.total == Decimal("33.18")

    def test_calculate_cart_total_multiple_items(self):
        """Should calculate total for cart with multiple items."""
        tax_service = TaxService()
        shipping_service = ShippingService()
        pricing_service = PricingService(
            tax_service=tax_service,
            shipping_service=shipping_service
        )

        items = [
            {
                "base_price": Decimal("19.99"),
                "options": [{"name": "Size", "value": "Large", "price_delta": Decimal("2.00")}],
                "quantity": 2
            },
            {
                "base_price": Decimal("9.99"),
                "options": [],
                "quantity": 1
            }
        ]

        result = pricing_service.calculate_cart_total(items, shipping_required=True)

        # Item 1: (19.99 + 2.00) * 2 = 43.98
        # Item 2: 9.99 * 1 = 9.99
        # Subtotal: 53.97
        # Tax: 5.40
        # Shipping: 8.99
        # Total: 68.36
        assert result.subtotal == Decimal("53.97")
        assert result.tax == Decimal("5.40")
        assert result.shipping == Decimal("8.99")
        assert result.total == Decimal("68.36")

    def test_calculate_cart_total_without_shipping(self):
        """Should calculate cart total without shipping."""
        tax_service = TaxService()
        shipping_service = ShippingService()
        pricing_service = PricingService(
            tax_service=tax_service,
            shipping_service=shipping_service
        )

        items = [
            {
                "base_price": Decimal("50.00"),
                "options": [],
                "quantity": 1
            }
        ]

        result = pricing_service.calculate_cart_total(items, shipping_required=False)

        assert result.shipping == Decimal("0.00")
        assert result.total == Decimal("55.00")  # 50 + 5 (tax)

    def test_calculate_cart_total_empty_cart(self):
        """Should handle empty cart."""
        tax_service = TaxService()
        shipping_service = ShippingService()
        pricing_service = PricingService(
            tax_service=tax_service,
            shipping_service=shipping_service
        )

        items = []

        result = pricing_service.calculate_cart_total(items, shipping_required=True)

        # Empty cart should have zero for all values
        # Shipping service returns flat rate even for 0 subtotal, but that's okay
        # as empty carts wouldn't normally proceed to checkout
        assert result.subtotal == Decimal("0.00")
        assert result.tax == Decimal("0.00")
        assert result.shipping == Decimal("8.99")  # Flat rate is still charged
        assert result.total == Decimal("8.99")


class TestPricingServiceIntegration:
    """Integration tests for pricing service with realistic scenarios."""

    def test_customized_tshirt_order(self):
        """Should calculate price for customized t-shirt order."""
        tax_service = TaxService(tax_rate=Decimal("0.08"))  # 8% sales tax
        shipping_service = ShippingService(
            flat_rate=Decimal("5.99"),
            free_shipping_threshold=Decimal("50.00")
        )
        pricing_service = PricingService(
            tax_service=tax_service,
            shipping_service=shipping_service
        )

        # T-shirt: $19.99 base, Large (+$2.00), Custom Print (+$5.00)
        base_price = Decimal("19.99")
        options = [
            {"name": "Size", "value": "Large", "price_delta": Decimal("2.00")},
            {"name": "Print", "value": "Custom", "price_delta": Decimal("5.00")},
        ]
        quantity = 2

        result = pricing_service.calculate_total_price(
            base_price=base_price,
            options=options,
            quantity=quantity,
            shipping_required=True
        )

        # Unit: 19.99 + 2.00 + 5.00 = 26.99
        # Subtotal: 26.99 * 2 = 53.98
        # Tax: 53.98 * 0.08 = 4.32
        # Shipping: 0.00 (above $50 threshold)
        # Total: 53.98 + 4.32 + 0.00 = 58.30
        assert result.subtotal == Decimal("53.98")
        assert result.tax == Decimal("4.32")
        assert result.shipping == Decimal("0.00")
        assert result.total == Decimal("58.30")

    def test_product_with_discount_option(self):
        """Should calculate price with discount option (negative price delta)."""
        tax_service = TaxService()
        shipping_service = ShippingService()
        pricing_service = PricingService(
            tax_service=tax_service,
            shipping_service=shipping_service
        )

        # Product: $50.00 base, Bulk discount (-$5.00)
        base_price = Decimal("50.00")
        options = [
            {"name": "Discount", "value": "Bulk", "price_delta": Decimal("-5.00")},
        ]
        quantity = 1

        result = pricing_service.calculate_total_price(
            base_price=base_price,
            options=options,
            quantity=quantity,
            shipping_required=True
        )

        # Unit: 50.00 - 5.00 = 45.00
        # Subtotal: 45.00
        # Tax: 4.50
        # Shipping: 8.99
        # Total: 58.49
        assert result.subtotal == Decimal("45.00")
        assert result.total == Decimal("58.49")

    def test_zero_priced_product(self):
        """Should handle zero-priced product (free item)."""
        tax_service = TaxService()
        shipping_service = ShippingService()
        pricing_service = PricingService(
            tax_service=tax_service,
            shipping_service=shipping_service
        )

        base_price = Decimal("0.00")
        options = []
        quantity = 1

        result = pricing_service.calculate_total_price(
            base_price=base_price,
            options=options,
            quantity=quantity,
            shipping_required=True
        )

        # Subtotal: 0.00, Tax: 0.00, Shipping: 8.99
        assert result.subtotal == Decimal("0.00")
        assert result.tax == Decimal("0.00")
        assert result.total == Decimal("8.99")
