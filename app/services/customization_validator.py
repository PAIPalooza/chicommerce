"""
Customization validation service for enforcing template constraints.

This module provides robust validation logic for user customization inputs
against product template definitions, ensuring data integrity and constraint
compliance.
"""
from typing import Dict, Any, List, Optional, Tuple
from uuid import UUID

from sqlalchemy.orm import Session

from app.models.template import Template, CustomizationZone
from app.crud.template import get_default_template


class ValidationError(Exception):
    """Custom exception for validation errors with detailed messages."""

    def __init__(self, errors: Dict[str, str]):
        """
        Initialize validation error with detailed error messages.

        Args:
            errors: Dictionary mapping field names to error messages
        """
        self.errors = errors
        super().__init__(self._format_error_message(errors))

    def _format_error_message(self, errors: Dict[str, str]) -> str:
        """Format errors into a single message string."""
        error_messages = [f"{key}: {msg}" for key, msg in errors.items()]
        return "; ".join(error_messages)

    def to_dict(self) -> Dict[str, Any]:
        """Convert validation error to dictionary for API response."""
        return {
            "detail": self._format_error_message(self.errors),
            "errors": self.errors
        }


class CustomizationValidator:
    """
    Service for validating customization data against template constraints.

    This validator enforces all template-defined constraints including:
    - Text length limits
    - Image format restrictions
    - Color palette constraints
    - Unknown zone detection
    - Type-specific validations
    """

    def __init__(self, db: Session):
        """
        Initialize the validator with database session.

        Args:
            db: SQLAlchemy database session
        """
        self.db = db

    def validate_customization_data(
        self,
        product_id: UUID,
        customization_data: Dict[str, Any]
    ) -> Tuple[bool, Optional[Dict[str, str]]]:
        """
        Validate customization data against product's default template constraints.

        Args:
            product_id: UUID of the product
            customization_data: User-provided customization data to validate

        Returns:
            Tuple of (is_valid, errors_dict)
            - is_valid: True if all validations pass, False otherwise
            - errors_dict: Dictionary of field-level errors if invalid, None if valid

        Raises:
            ValidationError: If template is not found or validation fails
        """
        # Get the default template for the product
        template = get_default_template(self.db, product_id)

        if not template:
            raise ValidationError({
                "template": f"No default template found for product {product_id}"
            })

        # Build zone configuration map from template
        zone_configs = self._build_zone_config_map(template)

        # Validate all customization data
        errors = {}

        for zone_key, zone_value in customization_data.items():
            # Check if zone exists in template
            if zone_key not in zone_configs:
                errors[zone_key] = f"Unknown customization zone '{zone_key}'"
                continue

            zone_config = zone_configs[zone_key]
            zone_type = zone_config.get("type")

            # Validate based on zone type
            if zone_type == "text":
                text_error = self._validate_text_zone(zone_key, zone_value, zone_config)
                if text_error:
                    errors[zone_key] = text_error

            elif zone_type == "image":
                image_error = self._validate_image_zone(zone_key, zone_value, zone_config)
                if image_error:
                    errors[zone_key] = image_error

            elif zone_type == "color":
                color_error = self._validate_color_zone(zone_key, zone_value, zone_config)
                if color_error:
                    errors[zone_key] = color_error

            elif zone_type == "shape":
                shape_error = self._validate_shape_zone(zone_key, zone_value, zone_config)
                if shape_error:
                    errors[zone_key] = shape_error

        if errors:
            return False, errors

        return True, None

    def _build_zone_config_map(self, template: Template) -> Dict[str, Dict[str, Any]]:
        """
        Build a map of zone keys to their configurations.

        Args:
            template: Template object with definition and customization zones

        Returns:
            Dictionary mapping zone keys to their configuration
        """
        zone_configs = {}

        # Extract from template definition
        if template.definition and "zones" in template.definition:
            for zone_key, zone_def in template.definition["zones"].items():
                zone_configs[zone_key] = zone_def.copy()

        # Merge with customization zones for additional config
        if template.customization_zones:
            for zone in template.customization_zones:
                if zone.key in zone_configs:
                    # Merge config from customization zone
                    if zone.config:
                        zone_configs[zone.key].update(zone.config)
                else:
                    # Add zone from customization_zones
                    zone_configs[zone.key] = {
                        "type": zone.type,
                        **(zone.config or {})
                    }

        return zone_configs

    def _validate_text_zone(
        self,
        zone_key: str,
        value: Any,
        config: Dict[str, Any]
    ) -> Optional[str]:
        """
        Validate text zone input.

        Args:
            zone_key: Key of the zone being validated
            value: The text value to validate
            config: Zone configuration with constraints

        Returns:
            Error message if invalid, None if valid
        """
        # Check if value is a string
        if not isinstance(value, str):
            return f"Text value must be a string, got {type(value).__name__}"

        # Check max_length constraint
        max_length = config.get("max_length")
        if max_length is not None:
            if len(value) > max_length:
                return f"Text exceeds maximum length of {max_length} characters (got {len(value)})"

        # Check min_length constraint
        min_length = config.get("min_length")
        if min_length is not None:
            if len(value) < min_length:
                return f"Text is below minimum length of {min_length} characters (got {len(value)})"

        return None

    def _validate_image_zone(
        self,
        zone_key: str,
        value: Any,
        config: Dict[str, Any]
    ) -> Optional[str]:
        """
        Validate image zone input.

        Args:
            zone_key: Key of the zone being validated
            value: The image value to validate (should be a dict with url and format)
            config: Zone configuration with constraints

        Returns:
            Error message if invalid, None if valid
        """
        # Check if value is a dictionary
        if not isinstance(value, dict):
            return f"Image value must be an object with 'url' and 'format' fields"

        # Check for required fields
        if "format" not in value:
            return "Image must specify a 'format' field"

        # Validate format against allowed formats
        allowed_formats = config.get("formats", [])
        if allowed_formats:
            image_format = value.get("format", "").lower()
            allowed_formats_lower = [f.lower() for f in allowed_formats]

            if image_format not in allowed_formats_lower:
                return f"Image format '{image_format}' not allowed. Allowed formats: {', '.join(allowed_formats)}"

        # Optional: validate URL if present
        if "url" in value:
            url = value.get("url")
            if not isinstance(url, str) or not url:
                return "Image URL must be a non-empty string"

        return None

    def _validate_color_zone(
        self,
        zone_key: str,
        value: Any,
        config: Dict[str, Any]
    ) -> Optional[str]:
        """
        Validate color zone input.

        Args:
            zone_key: Key of the zone being validated
            value: The color value to validate (should be a hex color string)
            config: Zone configuration with constraints

        Returns:
            Error message if invalid, None if valid
        """
        # Check if value is a string
        if not isinstance(value, str):
            return f"Color value must be a string, got {type(value).__name__}"

        # Validate hex color format
        if not value.startswith("#"):
            return "Color must be in hex format (e.g., #FF0000)"

        if len(value) not in [4, 7]:  # #RGB or #RRGGBB
            return "Color must be in #RGB or #RRGGBB format"

        # Validate hex characters
        try:
            int(value[1:], 16)
        except ValueError:
            return "Color contains invalid hex characters"

        # Validate against palette if specified
        palette = config.get("palette")
        if palette:
            # Normalize colors for comparison
            normalized_value = value.upper()
            normalized_palette = [c.upper() for c in palette]

            if normalized_value not in normalized_palette:
                return f"Color '{value}' not in allowed palette: {', '.join(palette)}"

        return None

    def _validate_shape_zone(
        self,
        zone_key: str,
        value: Any,
        config: Dict[str, Any]
    ) -> Optional[str]:
        """
        Validate shape zone input.

        Args:
            zone_key: Key of the zone being validated
            value: The shape value to validate
            config: Zone configuration with constraints

        Returns:
            Error message if invalid, None if valid
        """
        # For now, accept any shape data as dict
        if not isinstance(value, dict):
            return f"Shape value must be an object"

        # Validate allowed shapes if specified
        allowed_shapes = config.get("allowed_shapes")
        if allowed_shapes:
            shape_type = value.get("type")
            if not shape_type:
                return "Shape must specify a 'type' field"

            if shape_type not in allowed_shapes:
                return f"Shape type '{shape_type}' not allowed. Allowed types: {', '.join(allowed_shapes)}"

        return None
