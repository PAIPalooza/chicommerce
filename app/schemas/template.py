"""
Template schema module for request/response validation.
"""
from typing import List, Optional, Dict, Any, Union
from uuid import UUID
from datetime import datetime

from pydantic import BaseModel, Field, field_validator, model_validator, ConfigDict
from typing import Dict, Any, Optional, List


class CustomizationZoneBase(BaseModel):
    """Base schema for CustomizationZone data."""
    key: str = Field(..., min_length=1, max_length=100, description="Zone identifier (e.g., 'text_line1')")
    type: str = Field(..., description="Zone type (text, image, color, shape)")
    config: Optional[Dict[str, Any]] = Field(None, description="Zone-specific settings (maxLength, formats)")
    order_index: int = Field(..., ge=0, description="Determines rendering order")
    
    model_config = ConfigDict(from_attributes=True)


class CustomizationZoneCreate(CustomizationZoneBase):
    """Schema for creating a new CustomizationZone."""
    pass


class CustomizationZone(CustomizationZoneBase):
    """Schema for CustomizationZone response."""
    id: UUID
    template_id: UUID


class TemplateBase(BaseModel):
    """Base schema for Template data."""
    product_id: UUID = Field(..., description="ID of the product this template belongs to")
    version: int = Field(..., gt=0, description="Template version (incremental)")
    definition: Dict[str, Any] = Field(..., description="JSON schema for zones (text, image, color, etc.)")
    is_default: bool = Field(False, description="Flag for default template per product")
    
    model_config = ConfigDict(from_attributes=True)
    
    @field_validator('definition')
    @classmethod
    def validate_definition(cls, v: Dict[str, Any]) -> Dict[str, Any]:
        """Validate the template definition schema."""
        if not v:
            raise ValueError("Template definition cannot be empty")
            
        # Check for required top-level fields
        if 'zones' not in v:
            raise ValueError("Template definition must contain 'zones' field")
            
        if not isinstance(v['zones'], dict):
            raise ValueError("Template zones must be a dictionary")
            
        # Validate each zone
        for zone_key, zone_def in v['zones'].items():
            if not isinstance(zone_def, dict):
                raise ValueError(f"Zone '{zone_key}' definition must be a dictionary")
                
            if 'type' not in zone_def:
                raise ValueError(f"Zone '{zone_key}' must have a 'type' field")
                
            # Validate zone types
            zone_type = zone_def['type']
            if zone_type not in ['text', 'image', 'color', 'shape']:
                raise ValueError(f"Invalid zone type '{zone_type}'. Must be one of: text, image, color, shape")
                
            # Type-specific validations
            if zone_type == 'text':
                if 'max_length' in zone_def and not isinstance(zone_def['max_length'], int):
                    raise ValueError(f"Text zone '{zone_key}' max_length must be an integer")
                    
            elif zone_type == 'image':
                if 'formats' in zone_def:
                    if not isinstance(zone_def['formats'], list) or not all(isinstance(f, str) for f in zone_def['formats']):
                        raise ValueError(f"Image zone '{zone_key}' formats must be a list of strings")
        
        return v
    
    @model_validator(mode='after')
    def validate_customization_zones(self) -> 'TemplateBase':
        """
        Validate that customization_zones match the definition if both are provided.
        
        This ensures that the zones defined in the template definition match the
        customization_zones array in the request.
        """
        if not hasattr(self, 'customization_zones') or not self.customization_zones:
            return self
            
        # Check that all zones in definition have corresponding customization_zones
        defined_zones = set(self.definition.get('zones', {}).keys())
        provided_zones = {zone.key for zone in self.customization_zones if hasattr(zone, 'key')}
        
        if defined_zones != provided_zones:
            missing = defined_zones - provided_zones
            extra = provided_zones - defined_zones
            errors = []
            
            if missing:
                errors.append(f"Missing customization zones for defined zones: {', '.join(sorted(missing))}")
            if extra:
                errors.append(f"Extra customization zones not in definition: {', '.join(sorted(extra))}")
                
            raise ValueError("; ".join(errors))
            
        return self


class TemplateCreate(TemplateBase):
    """Schema for creating a new Template."""
    customization_zones: Optional[List[CustomizationZoneCreate]] = Field(None, description="Customization zones within the template")
    
    model_config = ConfigDict(from_attributes=True)


class TemplateUpdate(BaseModel):
    """Schema for updating a Template."""
    version: Optional[int] = Field(None, gt=0, description="Template version (incremental)")
    definition: Optional[Dict[str, Any]] = Field(None, description="JSON schema for zones")
    is_default: Optional[bool] = Field(None, description="Flag for default template per product")
    
    model_config = ConfigDict(from_attributes=True)
    
    @field_validator('definition')
    @classmethod
    def validate_definition(cls, v: Optional[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
        """Validate the template definition schema if provided."""
        if v is None:
            return v
            
        # Check for required top-level fields
        if 'zones' not in v:
            raise ValueError("Template definition must contain 'zones' field")
            
        if not isinstance(v['zones'], dict):
            raise ValueError("Template zones must be a dictionary")
            
        # Validate each zone
        for zone_key, zone_def in v['zones'].items():
            if not isinstance(zone_def, dict):
                raise ValueError(f"Zone '{zone_key}' definition must be a dictionary")
                
            if 'type' not in zone_def:
                raise ValueError(f"Zone '{zone_key}' must have a 'type' field")
                
            # Validate zone types
            zone_type = zone_def['type']
            if zone_type not in ['text', 'image', 'color', 'shape']:
                raise ValueError(f"Invalid zone type '{zone_type}'. Must be one of: text, image, color, shape")
                
            # Type-specific validations
            if zone_type == 'text':
                if 'max_length' in zone_def and not isinstance(zone_def['max_length'], int):
                    raise ValueError(f"Text zone '{zone_key}' max_length must be an integer")
                    
            elif zone_type == 'image':
                if 'formats' in zone_def:
                    if not isinstance(zone_def['formats'], list) or not all(isinstance(f, str) for f in zone_def['formats']):
                        raise ValueError(f"Image zone '{zone_key}' formats must be a list of strings")
        
        return v


class TemplateInDBBase(TemplateBase):
    """Base schema for Template already in the database."""
    id: UUID
    created_at: datetime
    updated_at: datetime
    
    model_config = ConfigDict(from_attributes=True)


class Template(TemplateInDBBase):
    """Schema for Template response."""
    customization_zones: List[CustomizationZone] = Field([], description="Customization zones within the template")
    
    model_config = ConfigDict(from_attributes=True)
