"""
Unit tests for CustomizationValidator service.

Following TDD/BDD principles with pure unit tests that don't require database.
"""
import pytest
from uuid import uuid4
from unittest.mock import Mock, MagicMock

from app.services.customization_validator import (
    CustomizationValidator,
    ValidationError
)
from app.models.template import Template, CustomizationZone


class TestCustomizationValidator:
    """
    Unit test suite for CustomizationValidator.

    These tests use mocks to avoid database dependencies.
    """

    def test_validate_text_zone_within_max_length_succeeds(self):
        """
        GIVEN a text zone with max_length constraint
        WHEN validating text within the limit
        THEN validation should pass
        """
        # Arrange
        validator = CustomizationValidator(Mock())
        config = {"type": "text", "max_length": 50}

        # Act
        error = validator._validate_text_zone("test_zone", "Valid text", config)

        # Assert
        assert error is None

    def test_validate_text_zone_exceeding_max_length_fails(self):
        """
        GIVEN a text zone with max_length constraint
        WHEN validating text exceeding the limit
        THEN validation should fail with descriptive error
        """
        # Arrange
        validator = CustomizationValidator(Mock())
        config = {"type": "text", "max_length": 10}
        long_text = "x" * 11

        # Act
        error = validator._validate_text_zone("test_zone", long_text, config)

        # Assert
        assert error is not None
        assert "maximum length" in error.lower()
        assert "10" in error

    def test_validate_text_zone_with_min_length_succeeds(self):
        """
        GIVEN a text zone with min_length constraint
        WHEN validating text meeting the minimum
        THEN validation should pass
        """
        # Arrange
        validator = CustomizationValidator(Mock())
        config = {"type": "text", "min_length": 5}

        # Act
        error = validator._validate_text_zone("test_zone", "Valid text", config)

        # Assert
        assert error is None

    def test_validate_text_zone_below_min_length_fails(self):
        """
        GIVEN a text zone with min_length constraint
        WHEN validating text below the minimum
        THEN validation should fail
        """
        # Arrange
        validator = CustomizationValidator(Mock())
        config = {"type": "text", "min_length": 10}
        short_text = "short"

        # Act
        error = validator._validate_text_zone("test_zone", short_text, config)

        # Assert
        assert error is not None
        assert "minimum length" in error.lower()
        assert "10" in error

    def test_validate_text_zone_non_string_fails(self):
        """
        GIVEN a text zone
        WHEN validating non-string value
        THEN validation should fail
        """
        # Arrange
        validator = CustomizationValidator(Mock())
        config = {"type": "text"}

        # Act
        error = validator._validate_text_zone("test_zone", 123, config)

        # Assert
        assert error is not None
        assert "string" in error.lower()

    def test_validate_image_zone_with_valid_format_succeeds(self):
        """
        GIVEN an image zone with format constraints
        WHEN validating image with allowed format
        THEN validation should pass
        """
        # Arrange
        validator = CustomizationValidator(Mock())
        config = {"type": "image", "formats": ["png", "jpg"]}
        image_data = {"url": "https://example.com/image.png", "format": "png"}

        # Act
        error = validator._validate_image_zone("image_zone", image_data, config)

        # Assert
        assert error is None

    def test_validate_image_zone_with_invalid_format_fails(self):
        """
        GIVEN an image zone with format constraints
        WHEN validating image with disallowed format
        THEN validation should fail
        """
        # Arrange
        validator = CustomizationValidator(Mock())
        config = {"type": "image", "formats": ["png", "jpg"]}
        image_data = {"url": "https://example.com/image.gif", "format": "gif"}

        # Act
        error = validator._validate_image_zone("image_zone", image_data, config)

        # Assert
        assert error is not None
        assert "format" in error.lower()
        assert "gif" in error.lower()

    def test_validate_image_zone_missing_format_fails(self):
        """
        GIVEN an image zone
        WHEN validating image without format field
        THEN validation should fail
        """
        # Arrange
        validator = CustomizationValidator(Mock())
        config = {"type": "image", "formats": ["png", "jpg"]}
        image_data = {"url": "https://example.com/image.png"}

        # Act
        error = validator._validate_image_zone("image_zone", image_data, config)

        # Assert
        assert error is not None
        assert "format" in error.lower()

    def test_validate_image_zone_non_dict_fails(self):
        """
        GIVEN an image zone
        WHEN validating non-dictionary value
        THEN validation should fail
        """
        # Arrange
        validator = CustomizationValidator(Mock())
        config = {"type": "image"}

        # Act
        error = validator._validate_image_zone("image_zone", "not a dict", config)

        # Assert
        assert error is not None
        assert "object" in error.lower()

    def test_validate_color_zone_with_valid_hex_succeeds(self):
        """
        GIVEN a color zone
        WHEN validating valid hex color
        THEN validation should pass
        """
        # Arrange
        validator = CustomizationValidator(Mock())
        config = {"type": "color"}

        # Act
        error = validator._validate_color_zone("color_zone", "#FF0000", config)

        # Assert
        assert error is None

    def test_validate_color_zone_with_valid_short_hex_succeeds(self):
        """
        GIVEN a color zone
        WHEN validating valid short hex color (#RGB)
        THEN validation should pass
        """
        # Arrange
        validator = CustomizationValidator(Mock())
        config = {"type": "color"}

        # Act
        error = validator._validate_color_zone("color_zone", "#F00", config)

        # Assert
        assert error is None

    def test_validate_color_zone_without_hash_fails(self):
        """
        GIVEN a color zone
        WHEN validating color without # prefix
        THEN validation should fail
        """
        # Arrange
        validator = CustomizationValidator(Mock())
        config = {"type": "color"}

        # Act
        error = validator._validate_color_zone("color_zone", "FF0000", config)

        # Assert
        assert error is not None
        assert "hex format" in error.lower()

    def test_validate_color_zone_with_invalid_length_fails(self):
        """
        GIVEN a color zone
        WHEN validating color with invalid length
        THEN validation should fail
        """
        # Arrange
        validator = CustomizationValidator(Mock())
        config = {"type": "color"}

        # Act
        error = validator._validate_color_zone("color_zone", "#FF00", config)

        # Assert
        assert error is not None
        assert "#RGB" in error or "#RRGGBB" in error

    def test_validate_color_zone_with_invalid_hex_chars_fails(self):
        """
        GIVEN a color zone
        WHEN validating color with invalid hex characters
        THEN validation should fail
        """
        # Arrange
        validator = CustomizationValidator(Mock())
        config = {"type": "color"}

        # Act
        error = validator._validate_color_zone("color_zone", "#GGGGGG", config)

        # Assert
        assert error is not None
        assert "hex" in error.lower()

    def test_validate_color_zone_with_palette_constraint_succeeds(self):
        """
        GIVEN a color zone with palette constraint
        WHEN validating color in the palette
        THEN validation should pass
        """
        # Arrange
        validator = CustomizationValidator(Mock())
        config = {"type": "color", "palette": ["#FF0000", "#00FF00", "#0000FF"]}

        # Act
        error = validator._validate_color_zone("color_zone", "#FF0000", config)

        # Assert
        assert error is None

    def test_validate_color_zone_with_palette_constraint_case_insensitive(self):
        """
        GIVEN a color zone with palette constraint
        WHEN validating color with different case
        THEN validation should pass (case-insensitive)
        """
        # Arrange
        validator = CustomizationValidator(Mock())
        config = {"type": "color", "palette": ["#FF0000", "#00FF00", "#0000FF"]}

        # Act
        error = validator._validate_color_zone("color_zone", "#ff0000", config)

        # Assert
        assert error is None

    def test_validate_color_zone_not_in_palette_fails(self):
        """
        GIVEN a color zone with palette constraint
        WHEN validating color not in the palette
        THEN validation should fail
        """
        # Arrange
        validator = CustomizationValidator(Mock())
        config = {"type": "color", "palette": ["#FF0000", "#00FF00", "#0000FF"]}

        # Act
        error = validator._validate_color_zone("color_zone", "#FFFFFF", config)

        # Assert
        assert error is not None
        assert "palette" in error.lower()

    def test_validate_shape_zone_with_valid_dict_succeeds(self):
        """
        GIVEN a shape zone
        WHEN validating valid shape dictionary
        THEN validation should pass
        """
        # Arrange
        validator = CustomizationValidator(Mock())
        config = {"type": "shape"}
        shape_data = {"type": "circle", "radius": 10}

        # Act
        error = validator._validate_shape_zone("shape_zone", shape_data, config)

        # Assert
        assert error is None

    def test_validate_shape_zone_with_allowed_shapes_succeeds(self):
        """
        GIVEN a shape zone with allowed_shapes constraint
        WHEN validating allowed shape type
        THEN validation should pass
        """
        # Arrange
        validator = CustomizationValidator(Mock())
        config = {"type": "shape", "allowed_shapes": ["circle", "square"]}
        shape_data = {"type": "circle", "radius": 10}

        # Act
        error = validator._validate_shape_zone("shape_zone", shape_data, config)

        # Assert
        assert error is None

    def test_validate_shape_zone_with_disallowed_shape_fails(self):
        """
        GIVEN a shape zone with allowed_shapes constraint
        WHEN validating disallowed shape type
        THEN validation should fail
        """
        # Arrange
        validator = CustomizationValidator(Mock())
        config = {"type": "shape", "allowed_shapes": ["circle", "square"]}
        shape_data = {"type": "triangle", "sides": 3}

        # Act
        error = validator._validate_shape_zone("shape_zone", shape_data, config)

        # Assert
        assert error is not None
        assert "triangle" in error.lower()
        assert "allowed" in error.lower()

    def test_validate_shape_zone_non_dict_fails(self):
        """
        GIVEN a shape zone
        WHEN validating non-dictionary value
        THEN validation should fail
        """
        # Arrange
        validator = CustomizationValidator(Mock())
        config = {"type": "shape"}

        # Act
        error = validator._validate_shape_zone("shape_zone", "not a dict", config)

        # Assert
        assert error is not None
        assert "object" in error.lower()

    def test_build_zone_config_map_from_definition(self):
        """
        GIVEN a template with zone definitions
        WHEN building zone config map
        THEN all zones should be included with their configs
        """
        # Arrange
        validator = CustomizationValidator(Mock())
        template = Mock(spec=Template)
        template.definition = {
            "zones": {
                "text_1": {"type": "text", "max_length": 100},
                "image_1": {"type": "image", "formats": ["png", "jpg"]}
            }
        }
        template.customization_zones = []

        # Act
        zone_configs = validator._build_zone_config_map(template)

        # Assert
        assert "text_1" in zone_configs
        assert "image_1" in zone_configs
        assert zone_configs["text_1"]["type"] == "text"
        assert zone_configs["text_1"]["max_length"] == 100
        assert zone_configs["image_1"]["type"] == "image"

    def test_validation_error_formatting(self):
        """
        GIVEN validation errors
        WHEN creating ValidationError
        THEN error message should be properly formatted
        """
        # Arrange
        errors = {
            "text_1": "Text exceeds maximum length",
            "image_1": "Invalid image format"
        }

        # Act
        error = ValidationError(errors)

        # Assert
        assert "text_1" in str(error)
        assert "image_1" in str(error)
        assert "Text exceeds maximum length" in str(error)
        assert "Invalid image format" in str(error)

    def test_validation_error_to_dict(self):
        """
        GIVEN validation errors
        WHEN converting to dictionary
        THEN dict should contain detail and errors fields
        """
        # Arrange
        errors = {
            "text_1": "Text exceeds maximum length",
            "image_1": "Invalid image format"
        }
        error = ValidationError(errors)

        # Act
        error_dict = error.to_dict()

        # Assert
        assert "detail" in error_dict
        assert "errors" in error_dict
        assert error_dict["errors"] == errors

    def test_validate_customization_data_with_template_not_found_fails(self):
        """
        GIVEN a product without a template
        WHEN validating customization data
        THEN ValidationError should be raised
        """
        # Arrange
        mock_db = Mock()
        validator = CustomizationValidator(mock_db)
        product_id = uuid4()
        customization_data = {"text_1": "some text"}

        # Mock get_default_template to return None
        from app.services import customization_validator
        original_get_default_template = customization_validator.get_default_template
        customization_validator.get_default_template = Mock(return_value=None)

        # Act & Assert
        try:
            with pytest.raises(ValidationError) as exc_info:
                validator.validate_customization_data(product_id, customization_data)

            assert "template" in str(exc_info.value).lower()
        finally:
            # Restore original function
            customization_validator.get_default_template = original_get_default_template

    def test_validate_customization_data_with_valid_data_succeeds(self):
        """
        GIVEN valid customization data matching template
        WHEN validating customization data
        THEN validation should pass
        """
        # Arrange
        mock_db = Mock()
        validator = CustomizationValidator(mock_db)
        product_id = uuid4()
        customization_data = {
            "text_1": "Valid text",
            "image_1": {"url": "https://example.com/image.png", "format": "png"}
        }

        # Mock template
        mock_template = Mock(spec=Template)
        mock_template.definition = {
            "zones": {
                "text_1": {"type": "text", "max_length": 100},
                "image_1": {"type": "image", "formats": ["png", "jpg"]}
            }
        }
        mock_template.customization_zones = []

        # Mock get_default_template
        from app.services import customization_validator
        original_get_default_template = customization_validator.get_default_template
        customization_validator.get_default_template = Mock(return_value=mock_template)

        # Act
        try:
            is_valid, errors = validator.validate_customization_data(product_id, customization_data)

            # Assert
            assert is_valid is True
            assert errors is None
        finally:
            # Restore original function
            customization_validator.get_default_template = original_get_default_template

    def test_validate_customization_data_with_invalid_data_fails(self):
        """
        GIVEN invalid customization data not matching template
        WHEN validating customization data
        THEN validation should fail with errors
        """
        # Arrange
        mock_db = Mock()
        validator = CustomizationValidator(mock_db)
        product_id = uuid4()
        customization_data = {
            "text_1": "x" * 101,  # Exceeds max_length
            "unknown_zone": "some data"  # Unknown zone
        }

        # Mock template
        mock_template = Mock(spec=Template)
        mock_template.definition = {
            "zones": {
                "text_1": {"type": "text", "max_length": 100}
            }
        }
        mock_template.customization_zones = []

        # Mock get_default_template
        from app.services import customization_validator
        original_get_default_template = customization_validator.get_default_template
        customization_validator.get_default_template = Mock(return_value=mock_template)

        # Act
        try:
            is_valid, errors = validator.validate_customization_data(product_id, customization_data)

            # Assert
            assert is_valid is False
            assert errors is not None
            assert "text_1" in errors
            assert "unknown_zone" in errors
        finally:
            # Restore original function
            customization_validator.get_default_template = original_get_default_template

    def test_build_zone_config_map_merges_customization_zones(self):
        """
        GIVEN a template with both definition and customization_zones
        WHEN building zone config map
        THEN configs should be merged properly
        """
        # Arrange
        validator = CustomizationValidator(Mock())
        mock_zone = Mock()
        mock_zone.key = "text_1"
        mock_zone.type = "text"
        mock_zone.config = {"min_length": 5}

        template = Mock(spec=Template)
        template.definition = {
            "zones": {
                "text_1": {"type": "text", "max_length": 100}
            }
        }
        template.customization_zones = [mock_zone]

        # Act
        zone_configs = validator._build_zone_config_map(template)

        # Assert
        assert "text_1" in zone_configs
        assert zone_configs["text_1"]["type"] == "text"
        assert zone_configs["text_1"]["max_length"] == 100
        assert zone_configs["text_1"]["min_length"] == 5  # Merged from customization_zones

    def test_validate_shape_zone_missing_type_fails(self):
        """
        GIVEN a shape zone with allowed_shapes constraint
        WHEN validating shape without type field
        THEN validation should fail
        """
        # Arrange
        validator = CustomizationValidator(Mock())
        config = {"type": "shape", "allowed_shapes": ["circle", "square"]}
        shape_data = {"radius": 10}  # Missing type

        # Act
        error = validator._validate_shape_zone("shape_zone", shape_data, config)

        # Assert
        assert error is not None
        assert "type" in error.lower()
