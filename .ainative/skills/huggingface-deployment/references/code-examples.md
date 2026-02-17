# HuggingFace Deployment Code Examples

Complete code examples for deploying HF models using Inference API and creating API endpoints.

## Example 1: Audio TTS Model (Inference API)

### Provider Implementation

```python
# app/providers/audio_model_provider.py
from typing import Optional, Dict, Any
import httpx
from decimal import Decimal
from app.services.ai_providers.base import BaseAIProvider

class AudioModelProvider(BaseAIProvider):
    """Provider for HuggingFace audio/TTS models using Inference API"""

    def __init__(
        self,
        api_key: str,
        model_id: str,
        base_url: Optional[str] = None
    ):
        super().__init__(api_key, base_url)
        self.model_id = model_id
        self.base_url = base_url or "https://api-inference.huggingface.co"

    async def generate_speech(
        self,
        text: str,
        voice: Optional[str] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Generate speech from text using HF TTS model

        Args:
            text: Input text to synthesize
            voice: Optional voice ID
            **kwargs: Additional model parameters

        Returns:
            Dict with audio_data (bytes), duration_seconds, cost_usd
        """
        url = f"{self.base_url}/models/{self.model_id}"
        headers = {"Authorization": f"Bearer {self.api_key}"}

        payload = {"inputs": text}
        if voice:
            payload["parameters"] = {"speaker": voice}

        async with httpx.AsyncClient() as client:
            response = await client.post(
                url,
                headers=headers,
                json=payload,
                timeout=60.0
            )
            response.raise_for_status()

            audio_data = response.content

            # Calculate cost (example: $0.001 per request)
            base_cost_usd = Decimal("0.001")

            # Estimate duration from audio data
            # For actual implementation, parse audio headers
            estimated_duration = len(text) / 10  # ~10 chars per second

            return {
                "audio_data": audio_data,
                "duration_seconds": estimated_duration,
                "cost_usd": base_cost_usd,
                "model_id": self.model_id,
                "format": "wav"
            }
```

### API Endpoint

```python
# app/api/api_v1/endpoints/audio.py
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional
import base64

from app.api.deps import get_db, get_current_user
from app.models.user import User
from app.providers.audio_model_provider import AudioModelProvider
from app.services.billing_service import BillingService
from app.models.audio_models import AudioModel, AudioModelUsage
import os

router = APIRouter()

class TTSRequest(BaseModel):
    text: str
    model_id: str = "facebook/mms-tts-eng"
    voice: Optional[str] = None

class TTSResponse(BaseModel):
    audio_base64: str
    duration_seconds: float
    cost_credits: int
    format: str

@router.post("/tts", response_model=TTSResponse)
async def generate_tts(
    request: TTSRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Generate text-to-speech audio

    Refs #1179
    """
    # Get model from database
    audio_model = db.query(AudioModel).filter(
        AudioModel.model_id == request.model_id
    ).first()

    if not audio_model:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Audio model '{request.model_id}' not found"
        )

    # Initialize provider
    provider = AudioModelProvider(
        api_key=os.getenv("HUGGINGFACE_API_KEY"),
        model_id=request.model_id
    )

    # Generate speech
    result = await provider.generate_speech(
        text=request.text,
        voice=request.voice
    )

    # Calculate cost in credits (1 credit = $0.04)
    base_cost_usd = result["cost_usd"]
    base_cost_credits = int(base_cost_usd / Decimal("0.04"))
    base_cost_credits = max(1, base_cost_credits)  # Minimum 1 credit

    # Apply markup (100% markup = 2x cost)
    billing_service = BillingService(db)
    final_cost_credits = await billing_service.calculate_cost_with_markup(
        user_id=current_user.id,
        base_cost=base_cost_credits,
        developer_markup=current_user.developer_markup
    )

    # Check user has sufficient credits
    if current_user.credits < final_cost_credits:
        raise HTTPException(
            status_code=status.HTTP_402_PAYMENT_REQUIRED,
            detail=f"Insufficient credits. Required: {final_cost_credits}, Available: {current_user.credits}"
        )

    # Deduct credits
    await billing_service.create_transaction(
        user_id=current_user.id,
        amount=-final_cost_credits,
        transaction_type="usage",
        description=f"TTS: {request.model_id}",
        metadata={
            "model_id": request.model_id,
            "duration_seconds": result["duration_seconds"],
            "text_length": len(request.text)
        }
    )

    # Log usage
    usage = AudioModelUsage(
        audio_model_id=audio_model.id,
        user_id=current_user.id,
        duration_seconds=result["duration_seconds"],
        requests_count=1,
        base_cost_usd=base_cost_usd,
        cost_credits=final_cost_credits
    )
    db.add(usage)
    await db.commit()

    # Return audio as base64
    audio_base64 = base64.b64encode(result["audio_data"]).decode("utf-8")

    return TTSResponse(
        audio_base64=audio_base64,
        duration_seconds=result["duration_seconds"],
        cost_credits=final_cost_credits,
        format=result["format"]
    )
```

### Database Migration

```python
# alembic/versions/xxxxx_add_audio_models.py
"""Add audio models and usage tables

Refs #1179
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql
import uuid

def upgrade():
    # Audio models table
    op.create_table(
        'audio_models',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, default=uuid.uuid4),
        sa.Column('model_id', sa.String(200), unique=True, nullable=False),
        sa.Column('model_name', sa.String(100), nullable=False),
        sa.Column('provider', sa.String(50), nullable=False),
        sa.Column('deployment_type', sa.String(50)),
        sa.Column('category', sa.String(50)),
        sa.Column('base_cost_usd', sa.Numeric(10, 6)),
        sa.Column('cost_unit', sa.String(20)),
        sa.Column('hf_endpoint_url', sa.Text),
        sa.Column('hardware_type', sa.String(50)),
        sa.Column('api_endpoint', sa.Text),
        sa.Column('api_method', sa.String(10)),
        sa.Column('status', sa.String(20), default='active'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now())
    )

    # Audio model usage table
    op.create_table(
        'audio_model_usage',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, default=uuid.uuid4),
        sa.Column('audio_model_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('audio_models.id')),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id')),
        sa.Column('duration_seconds', sa.Numeric(10, 2)),
        sa.Column('requests_count', sa.Integer, default=1),
        sa.Column('base_cost_usd', sa.Numeric(10, 6)),
        sa.Column('cost_credits', sa.Integer),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now())
    )

    # Add indexes
    op.create_index('idx_audio_models_model_id', 'audio_models', ['model_id'])
    op.create_index('idx_audio_models_category', 'audio_models', ['category'])
    op.create_index('idx_audio_model_usage_user', 'audio_model_usage', ['user_id'])
    op.create_index('idx_audio_model_usage_model', 'audio_model_usage', ['audio_model_id'])

def downgrade():
    op.drop_table('audio_model_usage')
    op.drop_table('audio_models')
```

### Seed Data Script

```python
# scripts/seed_audio_models.py
"""
Seed audio models into database

Usage:
    python scripts/seed_audio_models.py

Refs #1179
"""
from sqlalchemy.orm import Session
from app.db.session import SessionLocal
from app.models.audio_models import AudioModel
from decimal import Decimal

def seed_audio_models():
    db = SessionLocal()

    models = [
        # HuggingFace TTS Models (Inference API)
        {
            "model_id": "facebook/mms-tts-eng",
            "model_name": "MMS TTS (English)",
            "provider": "huggingface",
            "deployment_type": "inference_api",
            "category": "tts",
            "base_cost_usd": Decimal("0.001"),
            "cost_unit": "per_request",
            "status": "active"
        },
        {
            "model_id": "suno/bark",
            "model_name": "Bark (Multimodal Audio)",
            "provider": "huggingface",
            "deployment_type": "inference_api",
            "category": "tts",
            "base_cost_usd": Decimal("0.002"),
            "cost_unit": "per_request",
            "status": "active"
        },
        {
            "model_id": "myshell-ai/MeloTTS",
            "model_name": "MeloTTS (Multilingual)",
            "provider": "huggingface",
            "deployment_type": "inference_api",
            "category": "tts",
            "base_cost_usd": Decimal("0.0015"),
            "cost_unit": "per_request",
            "status": "active"
        },

        # MiniMax API Services
        {
            "model_id": "minimax-tts-sync",
            "model_name": "MiniMax TTS (Sync)",
            "provider": "minimax",
            "deployment_type": "api_proxy",
            "category": "tts",
            "base_cost_usd": Decimal("0.003"),
            "cost_unit": "per_second",
            "api_endpoint": "https://api.minimaxi.chat/v1/audio/speech",
            "api_method": "POST",
            "status": "active"
        },
        {
            "model_id": "minimax-music-v2",
            "model_name": "MiniMax Music Generation 2.0",
            "provider": "minimax",
            "deployment_type": "api_proxy",
            "category": "music",
            "base_cost_usd": Decimal("0.01"),
            "cost_unit": "per_request",
            "api_endpoint": "https://api.minimaxi.chat/v1/music/generate",
            "api_method": "POST",
            "status": "active"
        }
    ]

    for model_data in models:
        # Check if model already exists
        existing = db.query(AudioModel).filter(
            AudioModel.model_id == model_data["model_id"]
        ).first()

        if not existing:
            model = AudioModel(**model_data)
            db.add(model)
            print(f"✓ Added {model_data['model_name']}")
        else:
            print(f"⊘ Skipped {model_data['model_name']} (already exists)")

    db.commit()
    db.close()
    print(f"\n✓ Seeded {len(models)} audio models")

if __name__ == "__main__":
    seed_audio_models()
```

## Example 2: Music Generation Model

### Provider Method

```python
# app/providers/audio_model_provider.py (additional method)
async def generate_music(
    self,
    prompt: str,
    duration: int = 10,
    **kwargs
) -> Dict[str, Any]:
    """
    Generate music from text prompt

    Args:
        prompt: Text description of desired music
        duration: Duration in seconds (default: 10)
        **kwargs: Additional parameters

    Returns:
        Dict with audio_data, duration, cost_usd
    """
    url = f"{self.base_url}/models/{self.model_id}"
    headers = {"Authorization": f"Bearer {self.api_key}"}

    payload = {
        "inputs": prompt,
        "parameters": {
            "duration": duration,
            "temperature": kwargs.get("temperature", 1.0)
        }
    }

    async with httpx.AsyncClient(timeout=120.0) as client:
        response = await client.post(url, headers=headers, json=payload)
        response.raise_for_status()

        audio_data = response.content

        # Music models typically cost more
        base_cost_usd = Decimal("0.01")  # $0.01 per request

        return {
            "audio_data": audio_data,
            "duration_seconds": duration,
            "cost_usd": base_cost_usd,
            "model_id": self.model_id,
            "format": "wav",
            "prompt": prompt
        }
```

## Example 3: Register Provider in Factory

```python
# app/services/ai_providers/factory.py
from app.providers.audio_model_provider import AudioModelProvider
from app.schemas.ai import AIProviderSchema

class AIProviderFactory:
    _providers: Dict[str, Type[BaseAIProvider]] = {
        AIProviderSchema.OPENAI: OpenAIProvider,
        AIProviderSchema.ANTHROPIC: AnthropicProvider,
        AIProviderSchema.TOGETHER_AI: TogetherAIProvider,
        AIProviderSchema.HUGGINGFACE: NousCoderProvider,
        AIProviderSchema.MINIMAX: MiniMaxProvider,
        AIProviderSchema.AUDIO_MODEL: AudioModelProvider,  # NEW
    }

    @classmethod
    def get_audio_provider(
        cls,
        model_id: str,
        api_key: Optional[str] = None
    ) -> AudioModelProvider:
        """
        Get audio model provider for specific model

        Args:
            model_id: HuggingFace model ID (e.g. 'facebook/mms-tts-eng')
            api_key: Optional API key (uses env var if not provided)

        Returns:
            AudioModelProvider instance
        """
        if api_key is None:
            api_key = os.environ.get("HUGGINGFACE_API_KEY")
            if not api_key:
                raise ValueError("HUGGINGFACE_API_KEY not found in environment")

        return AudioModelProvider(api_key=api_key, model_id=model_id)
```

## Example 4: Frontend Integration

```typescript
// AINative-website-nextjs/lib/model-aggregator.ts
async fetchAudioModels(): Promise<UnifiedAIModel[]> {
  // Fetch from backend API (models stored in database)
  const response = await apiClient.get<{ models: AudioModel[] }>('/v1/audio/models');

  return response.data.models.map(model => ({
    id: model.model_id,
    slug: model.model_id.replace('/', '-'),
    name: model.model_name,
    provider: model.provider,
    category: 'Audio',
    endpoint: `/v1/audio/${model.category}`,
    method: 'POST',
    pricing: {
      input: {
        amount: parseFloat(model.base_cost_usd) * 2,  // With 100% markup
        unit: model.cost_unit
      }
    },
    metadata: {
      deployment_type: model.deployment_type,
      hardware_type: model.hardware_type
    }
  }));
}
```

## Example 5: Cost Calculation Helper

```python
# app/services/billing_service.py (additional method)
from decimal import Decimal

class BillingService:
    """Billing service with cost calculation"""

    CREDIT_VALUE_USD = Decimal("0.04")  # 1 credit = $0.04

    @staticmethod
    def usd_to_credits(amount_usd: Decimal) -> int:
        """
        Convert USD to credits

        Args:
            amount_usd: Amount in USD

        Returns:
            Number of credits (minimum 1)

        Example:
            >>> BillingService.usd_to_credits(Decimal("0.001"))
            1  # ($0.001 / $0.04 = 0.025 → rounds to 1)
            >>> BillingService.usd_to_credits(Decimal("0.08"))
            2  # ($0.08 / $0.04 = 2)
        """
        credits = int(amount_usd / BillingService.CREDIT_VALUE_USD)
        return max(1, credits)  # Minimum 1 credit

    @staticmethod
    def credits_to_usd(credits: int) -> Decimal:
        """
        Convert credits to USD

        Args:
            credits: Number of credits

        Returns:
            Amount in USD

        Example:
            >>> BillingService.credits_to_usd(10)
            Decimal('0.40')  # 10 * $0.04
        """
        return credits * BillingService.CREDIT_VALUE_USD
```

## Example 6: Testing Pattern

```python
# tests/test_audio_models.py
import pytest
from decimal import Decimal
from app.providers.audio_model_provider import AudioModelProvider
from app.services.billing_service import BillingService

@pytest.mark.asyncio
async def test_tts_generation():
    """Test TTS generation and cost calculation"""
    provider = AudioModelProvider(
        api_key="test_key",
        model_id="facebook/mms-tts-eng"
    )

    # Mock the API call
    with patch('httpx.AsyncClient.post') as mock_post:
        mock_post.return_value.content = b"fake_audio_data"
        mock_post.return_value.status_code = 200

        result = await provider.generate_speech(text="Hello world")

        # Verify result structure
        assert "audio_data" in result
        assert "cost_usd" in result
        assert result["duration_seconds"] > 0

        # Verify cost calculation
        credits = BillingService.usd_to_credits(result["cost_usd"])
        assert credits >= 1  # Minimum 1 credit

@pytest.mark.asyncio
async def test_cost_with_markup():
    """Test markup calculation"""
    base_cost = 1  # 1 credit
    markup = Decimal("100.0")  # 100%

    # 100% markup = 2x cost = 50% profit margin
    final_cost = base_cost * (1 + markup / 100)
    assert final_cost == 2  # 1 * (1 + 100/100) = 1 * 2 = 2
```

Refs #1179
