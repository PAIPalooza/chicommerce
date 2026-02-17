# HuggingFace Deployment & AI Provider Management

Deploy HuggingFace models using serverless Inference API or dedicated endpoints with cost tracking.

## Overview

AINative Studio supports multiple AI providers via factory pattern with cost tracking:

- **Providers**: OpenAI, Anthropic, MiniMax, HuggingFace, TogetherAI
- All use `BillingService.calculate_cost_with_markup()` (100% markup)

## HuggingFace Deployment Options

### Option A: Inference API (Serverless)

**Use Cases:**
- Audio/TTS models
- Variable usage
- Cost-sensitive deployments
- Prototyping

**URL Pattern:**
```
https://api-inference.huggingface.co/models/{model_id}
```

**Implementation:**
```python
provider = NousCoderProvider(
    api_key=os.getenv("HUGGINGFACE_API_KEY"),
    base_url="https://api-inference.huggingface.co"
)
```

### Option B: Dedicated Endpoints

**Use Cases:**
- Production models
- Low-latency requirements
- Custom inference configs
- GPU-intensive models

**Cost Structure (per hour):**
- T4: $0.60/hr
- L4: $0.80/hr
- A10G: $1.00/hr
- A100: $4.00/hr

**Implementation:**
```python
endpoint_service = HuggingFaceEndpointService(db)
endpoint = await endpoint_service.create_endpoint(
    endpoint_name="my-audio-model",
    model_repo="facebook/mms-tts-eng",
    hardware_type="nvidia-t4",
    auto_scale=True
)
```

## Cost Tracking Flow

1. **Provider Calculates Base Cost**
```python
duration_seconds = 30
cost_per_second = Decimal("0.0001")
base_cost_usd = duration_seconds * cost_per_second
```

2. **Convert to Credits**
```python
base_cost_credits = int(base_cost_usd / Decimal("0.04"))
```

3. **Apply Markup**
```python
billing_service = BillingService(db)
final_cost = await billing_service.calculate_cost_with_markup(
    user_id=user.id,
    base_cost=base_cost_credits,
    developer_markup=Decimal("100.0")
)
```

4. **Deduct from User Account**
```python
transaction = await billing_service.create_transaction(
    user_id=user.id,
    amount=-final_cost,
    transaction_type="usage"
)
```

## Key Implementation Steps

1. Create Provider Class
```python
class YourProvider(BaseAIProvider):
    async def generate_audio(self, text: str, **kwargs):
        # Implementation
```

2. Register in Factory
```python
AIProviderFactory._providers["your_provider"] = YourProvider
```

## Cost Optimization Strategies

- Use Inference API for variable audio models
- Monitor usage patterns
- Implement caching
- Break-even analysis for dedicated endpoints

## Environment Variables

```bash
HUGGINGFACE_API_KEY="hf_xxxxxxxxxxxxxxxxxxxxx"
HUGGINGFACE_BASE_URL="https://api-inference.huggingface.co"
```

## Monitoring

```python
# Check provider registration
providers = AIProviderFactory.get_available_providers()

# Monitor costs
billing = BillingService(db)
total_spent = await billing.get_total_usage(user_id, days=30)
```

## References

- HuggingFace Inference API Docs
- HuggingFace Dedicated Endpoints
- Existing Implementation: `src/backend/app/services/huggingface_endpoint_service.py`

Refs #1179