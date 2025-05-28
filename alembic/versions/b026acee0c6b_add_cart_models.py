"""add_cart_models

Revision ID: b026acee0c6b
Revises: 39f36f1d5491
Create Date: 2025-05-28 00:45:06.328360

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision: str = 'b026acee0c6b'
down_revision: Union[str, None] = '39f36f1d5491'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create carts table
    op.create_table(
        'carts',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=True, index=True),
        sa.Column('session_id', sa.String(255), nullable=False, index=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.text('now()'), onupdate=sa.text('now()'), nullable=False),
    )
    
    # Create cart_items table
    op.create_table(
        'cart_items',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('cart_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('carts.id', ondelete='CASCADE'), nullable=False, index=True),
        sa.Column('product_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('products.id'), nullable=False, index=True),
        sa.Column('quantity', sa.Integer(), nullable=False, default=1),
        sa.Column('unit_price', sa.Numeric(10, 2), nullable=False),
        sa.Column('customization_data', postgresql.JSONB, nullable=False, server_default='{}'),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.text('now()'), onupdate=sa.text('now()'), nullable=False),
    )
    
    # Create customization_sessions table
    op.create_table(
        'customization_sessions',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('session_id', sa.String(255), nullable=False, index=True),
        sa.Column('product_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('products.id'), nullable=False, index=True),
        sa.Column('customization_data', postgresql.JSONB, nullable=False, server_default='{}'),
        sa.Column('is_active', sa.Boolean(), nullable=False, default=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.text('now()'), onupdate=sa.text('now()'), nullable=False),
    )
    
    # Create indexes
    op.create_index('idx_cart_session_id', 'carts', ['session_id'], unique=False)
    op.create_index('idx_cart_user_id', 'carts', ['user_id'], unique=False)
    op.create_index('idx_cart_item_cart_id', 'cart_items', ['cart_id'], unique=False)
    op.create_index('idx_customization_session_id', 'customization_sessions', ['session_id'], unique=False)


def downgrade() -> None:
    op.drop_index('idx_customization_session_id', table_name='customization_sessions')
    op.drop_index('idx_cart_item_cart_id', table_name='cart_items')
    op.drop_index('idx_cart_user_id', table_name='carts')
    op.drop_index('idx_cart_session_id', table_name='carts')
    op.drop_table('customization_sessions')
    op.drop_table('cart_items')
    op.drop_table('carts')
