# AI Model Catalog

## Overview

Tracks pricing, implementation, provider integration for AI model categories:

- **Audio Models** ✅ (TTS, Music, Speech Recognition)
- **Video Models** 🚧 (Coming soon)
- **Image Models** 🚧 (Coming soon)
- **Text/Code Models** 🚧 (Coming soon)
- **Embeddings Models** 🚧 (Coming soon)

# PART 1: AUDIO MODELS

## MANDATORY: 100% Markup on All Audio Model Endpoints

**ZERO TOLERANCE RULE**: Every audio model endpoint MUST apply minimum 100% markup on base costs.

## Pricing Formula

```
Customer Price = Base Cost × 2
Credits Charged = (Base Cost USD × 1000) × 2
```

## Audio Model Categories and Pricing

### 1. Text-to-Speech (TTS)

#### MiniMax TTS Models
- **Base Cost**: $30-50/million chars
- **Model Variants**:
  - `speech-2.8-hd`: $50/million chars
  - `speech-2.8-turbo`: $30/million chars
  - `speech-02-hd`: $50/million chars
  - `speech-02-turbo`: $30/million chars

**Markup Calculation**:
```python
base_cost_per_char = 0.00005
chars_in_text = len(text)
base_cost_usd = Decimal(str(base_cost_per_char * chars_in_text))

customer_cost_usd = base_cost_usd * 2
credits_charged = int(customer_cost_usd * 1000)
```

#### OpenAI Whisper Models
- **Base Cost**: $0.006/minute
- **Customer Price**: $0.012/minute
- **Credits**: 12 credits/minute

#### HuggingFace TTS Models
- **Base Cost**: $0.001/request
- **Customer Price**: $0.002/request
- **Credits**: 2 credits/request

### 2. Music Generation

#### MiniMax Music 2.0
- **Base Cost**: $0.01/generation
- **Customer Price**: $0.02/generation
- **Credits**: 20 credits/generation

### 3. Speech Recognition

#### OpenAI Whisper Transcription/Translation
- **Base Cost**: $0.006/minute
- **Customer Price**: $0.012/minute
- **Credits**: 12 credits/minute

## Implementation Checklist

- [ ] Calculate base cost
- [ ] Apply 100% markup
- [ ] Convert to credits
- [ ] Implement credit check
- [ ] Deduct credits
- [ ] Log usage
- [ ] Document pricing
- [ ] Verify markup in tests

## Database Schema

```sql
model_id          VARCHAR(200)
model_name        VARCHAR(100)
provider          VARCHAR(50)
category          VARCHAR(50)
base_cost_usd     NUMERIC(10,6)
cost_unit         VARCHAR(20)
status            VARCHAR(20)
```

## Provider-Specific Notes: MiniMax

### CRITICAL: API v2 Implementation

**Base URLs**:
- **TTS**: `https://api.minimaxi.chat`
- **Music**: `https://api.minimax.io`

**TTS Endpoint**:
```
https://api.minimaxi.chat/v1/t2a_v2?GroupId={group_id}
```

**Environment Variables**:
```bash
MINIMAX_API_KEY="your-api-key"
MINIMAX_GROUP_ID="your-group-id"
MINIMAX_API_BASE_URL="https://api.minimaxi.chat"
```

## Enforcement

Invoke this skill:
1. Before implementing audio model endpoints
2. Reviewing pricing calculations
3. Adding audio models to database
4. Debugging credit deduction
5. Creating API documentation

**Violation of 100% markup rule = Immediate fix required**

# PART 2-5: MODEL CATEGORIES 🚧

**Status**: Placeholder for future model categories (Video, Image, Text, Embeddings)

**Pricing Formula**: Same 100% markup rule
```
Customer Price = Base Cost × 2
Credits Charged = (Base Cost USD × 1000) × 2
```

# APPENDIX: General Implementation Guidelines

## Adding New Model Categories

1. Update skill documentation
2. Create provider class
3. Update database schema
4. Implement API endpoints
5. Integrate frontend
6. Comprehensive testing

## Cross-Reference Skills

- `huggingface-deployment.md`
- `audio-transcribe.md`
- `mandatory-tdd.md`
- `code-quality.md`

Refs #1179