"""
Main API router for API v1.
"""
from fastapi import APIRouter

from app.api.v1.endpoints import products, templates, option_sets, cart

api_router = APIRouter()

# Include all endpoint routers
api_router.include_router(products.router, prefix="/products", tags=["products"])
api_router.include_router(templates.router, prefix="/templates", tags=["templates"])
api_router.include_router(option_sets.router, prefix="/option-sets", tags=["option-sets"])
api_router.include_router(cart.router, tags=["cart"])
