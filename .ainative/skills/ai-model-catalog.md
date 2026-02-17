---
description: AI Model Catalog - pricing standards, implementation guides, and provider integration for audio, video, image, text/code, and embeddings models with mandatory 100% markup
---

# AI Model Catalog

## Overview

This skill documents pricing, implementation, and provider integration for **all AI model categories** available in the AINative Studio AI Models page:

- **Audio Models** ✅ (TTS, Music Generation, Speech Recognition) - Actively maintained
- **Video Models** 🚧 (Coming soon)
- **Image Models** 🚧 (Coming soon)
- **Text/Code Models** 🚧 (Coming soon)
- **Embeddings Models** 🚧 (Coming soon)

---

# PART 1: AUDIO MODELS

## MANDATORY: 100% Markup on All Audio Model Endpoints

**ZERO TOLERANCE RULE**: Every audio model endpoint MUST apply a minimum 100% markup on base costs. This is NON-NEGOTIABLE for platform profitability.

## Pricing Formula

```
Customer Price = Base Cost × 2 (100% markup)
Credits Charged = (Base Cost USD × 1000) × 2
```

## Audio Model Categories and Pricing

### 1. Text-to-Speech (TTS)

#### MiniMax TTS Models
- **Base Cost**: $30-50 per million characters (varies by model)
- **Model Variants**:
  - `speech-2.8-hd`: $50/million chars (latest, highest quality)
  - `speech-2.8-turbo`: $30/million chars (latest, faster)
  - `speech-02-hd`: $50/million chars (legacy)
  - `speech-02-turbo`: $30/million chars (legacy)

**REQUIRED Markup Calculation**:
```python
# Example for speech-02-hd at $50/million chars
base_cost_per_char = 0.00005  # $50 / 1,000,000
chars_in_text = len(text)
base_cost_usd = Decimal(str(base_cost_per_char * chars_in_text))

# Apply 100% markup
customer_cost_usd = base_cost_usd * 2
credits_charged = int(customer_cost_usd * 1000)
```

#### OpenAI Whisper Models
- **Base Cost**: $0.006 per minute
- **Customer Price**: $0.012 per minute (100% markup)
- **Credits**: 6 credits per minute base × 2 = 12 credits per minute

#### HuggingFace TTS Models
- **Base Cost**: $0.001 per request
- **Customer Price**: $0.002 per request (100% markup)
- **Credits**: 2 credits per request

### 2. Music Generation

#### MiniMax Music 2.0
- **Base Cost**: $0.01 per generation
- **Customer Price**: $0.02 per generation (100% markup)
- **Credits**: 20 credits per generation
- **VERIFIED**: Already implemented correctly in music endpoint

### 3. Speech Recognition

#### OpenAI Whisper Transcription
- **Base Cost**: $0.006 per minute
- **Customer Price**: $0.012 per minute (100% markup)
- **Credits**: 12 credits per minute

#### OpenAI Whisper Translation
- **Base Cost**: $0.006 per minute
- **Customer Price**: $0.012 per minute (100% markup)
- **Credits**: 12 credits per minute

## Implementation Checklist

When implementing ANY audio model endpoint:

- [ ] Calculate base cost from provider API documentation
- [ ] Apply 100% markup: `customer_price = base_cost × 2`
- [ ] Convert to credits: `credits = int(customer_price_usd × 1000)`
- [ ] Implement credit check before API call
- [ ] Deduct credits after successful generation
- [ ] Log usage with both base cost and credits charged
- [ ] Document pricing in API docs
- [ ] Verify markup in tests (base_cost × 2 = charged)

## Common Mistakes to Avoid

### ❌ WRONG: Charging base cost directly
```python
credits_charged = int(base_cost_usd * 1000)  # Only 0% markup!
```

### ✅ CORRECT: Apply 100% markup
```python
customer_cost_usd = base_cost_usd * 2  # 100% markup
credits_charged = int(customer_cost_usd * 1000)
```

### ❌ WRONG: Using "per_second" for character-based pricing
```python
# MiniMax charges per character, not per second!
base_cost_per_second = 0.003  # INCORRECT
```

### ✅ CORRECT: Use character-based pricing
```python
# MiniMax actual pricing
base_cost_per_million_chars = 50.00  # $50/million for HD
base_cost_per_char = base_cost_per_million_chars / 1_000_000
base_cost_usd = Decimal(str(base_cost_per_char * len(text)))
```

## Database Schema Requirements

### audio_models table
```sql
model_id          VARCHAR(200)    -- e.g., "minimax-tts-sync"
model_name        VARCHAR(100)    -- e.g., "MiniMax TTS Sync"
provider          VARCHAR(50)     -- e.g., "minimax"
category          VARCHAR(50)     -- "tts", "music", "stt"
base_cost_usd     NUMERIC(10,6)   -- Provider's base cost
cost_unit         VARCHAR(20)     -- "per_character", "per_request", "per_minute"
status            VARCHAR(20)     -- "active", "deprecated"
```

**CRITICAL**: `base_cost_usd` should store the PROVIDER'S cost, NOT the customer price. The 100% markup is applied at runtime in the endpoint.

## Testing Requirements

Every audio endpoint test MUST verify:

1. **Markup Verification**:
```python
assert credits_charged == base_cost_credits * 2  # 100% markup
```

2. **Cost Calculation**:
```python
expected_cost = base_cost_usd * 2
assert result["cost_credits"] == int(expected_cost * 1000)
```

3. **Credit Deduction**:
```python
initial_credits = user.credits
# ... make API call ...
final_credits = user.credits
assert initial_credits - final_credits == credits_charged
```

## Provider-Specific Notes

###  MiniMax

#### CRITICAL: API v2 Implementation Details (Refs #1179)

**Base URLs (Different for Each Service):**
- **TTS Base URL**: `https://api.minimaxi.chat` ✅
- **Music Base URL**: `https://api.minimax.io` ✅
- ❌ **DO NOT** use `https://api.minimax.io` for TTS (returns 404)

**TTS Endpoint Format:**
```
https://api.minimaxi.chat/v1/t2a_v2?GroupId={group_id}
```

**Critical Configuration:**
| Setting | Correct Value | WRONG Value |
|---------|--------------|-------------|
| TTS Base URL | `https://api.minimaxi.chat` | ❌ `https://api.minimax.io` |
| Endpoint | `/v1/t2a_v2?GroupId={group_id}` | ❌ `/v1/t2a` (deprecated) |
| Voice ID Format | `English_Graceful_Lady` | ❌ `audiobook_female_1` |
| Response Field | `data.audio` (hex) | ❌ `data.audio_file` (base64) |
| Audio Decoding | `bytes.fromhex(audio_hex)` | ❌ `base64.b64decode()` |
| Pricing Model | Per character ($30-50/million) | ❌ Per second |

**Request Payload (API v2):**
```python
payload = {
    "model": "speech-02-turbo",  # REQUIRED
    "text": "Your text here",     # REQUIRED
    "stream": False,              # REQUIRED
    "voice_setting": {            # REQUIRED
        "voice_id": "English_Graceful_Lady",  # Valid system voice
        "speed": 1.0              # Optional: 0.5-2.0
    },
    "audio_setting": {            # REQUIRED
        "sample_rate": 32000,     # Recommended
        "bitrate": 128000,        # Recommended
        "format": "mp3"           # Options: mp3, wav, pcm
    }
}
```

**Response Parsing (CRITICAL):**
```python
result = response.json()

# Check for API errors
base_resp = result.get("base_resp", {})
if base_resp.get("status_code") != 0:
    raise ValueError(f"MiniMax API error: {base_resp.get('status_msg')}")

# Extract audio data (HEX-encoded, NOT base64!)
data = result.get("data", {})
audio_hex = data.get("audio", "")  # NOTE: "audio", NOT "audio_file"!

# Convert HEX to bytes (NOT base64!)
audio_data = bytes.fromhex(audio_hex)  # CRITICAL: Use fromhex()
```

**Environment Variables:**
```bash
MINIMAX_API_KEY="your-api-key"
MINIMAX_GROUP_ID="your-group-id"
MINIMAX_API_BASE_URL="https://api.minimaxi.chat"  # For TTS
```

**Common Errors:**
- **404**: Using wrong base URL (`api.minimax.io` instead of `api.minimaxi.chat`)
- **2054 "voice id not exist"**: Using wrong voice format (use `English_Graceful_Lady` not `audiobook_female_1`)
- **"No audio data"**: Looking for `audio_file` instead of `audio`
- **Invalid audio**: Using `base64.b64decode()` on hex data (use `bytes.fromhex()`)

**Pricing**: Per character (not per second!)
**Models**: 6 variants (speech-2.8-hd, speech-2.8-turbo, speech-02-hd, speech-02-turbo)
**API Key**: Required in `MINIMAX_API_KEY` env var
**Group ID**: Required in `MINIMAX_GROUP_ID` env var (MANDATORY query parameter)

### OpenAI
- **Endpoint**: `/v1/audio/*`
- **Pricing**: Per minute for transcription, per 1K chars for TTS
- **Models**: whisper-1, tts-1, tts-1-hd
- **API Key**: Required in `OPENAI_API_KEY` env var

### HuggingFace
- **Endpoint**: `https://api-inference.huggingface.co/models/{model_id}`
- **Pricing**: Per request (flat rate)
- **Models**: Various community models
- **API Key**: Required in `HUGGINGFACE_API_KEY` env var

## Enforcement

This skill should be invoked:
1. **Before implementing** any new audio model endpoint
2. **When reviewing** pricing calculations in existing code
3. **When adding** new audio models to the database
4. **When debugging** credit deduction issues
5. **When creating** API documentation

**Violation of 100% markup rule = Immediate fix required**

---

# PART 2: VIDEO MODELS 🚧

**Status**: Placeholder - To be documented as video models are added to AI Models page

## Planned Video Model Categories

### 1. Video Generation
- OpenAI Sora (when available)
- Runway ML
- Pika Labs
- Other text-to-video models

### 2. Video Analysis
- Frame extraction
- Object detection
- Scene classification
- Content moderation

### 3. Video Editing
- Automated editing
- Style transfer
- Effects generation

**Pricing Formula**: Same 100% markup rule applies
```
Customer Price = Base Cost × 2 (100% markup)
Credits Charged = (Base Cost USD × 1000) × 2
```

---

# PART 3: IMAGE MODELS 🚧

**Status**: Placeholder - To be documented as image models are added to AI Models page

## Planned Image Model Categories

### 1. Image Generation
- DALL-E 3
- Stable Diffusion XL
- Midjourney API
- Flux models
- Other text-to-image models

### 2. Image Editing
- Inpainting
- Outpainting
- Style transfer
- Background removal

### 3. Image Analysis
- Object detection
- Face recognition
- OCR (Optical Character Recognition)
- Content moderation

**Pricing Formula**: Same 100% markup rule applies
```
Customer Price = Base Cost × 2 (100% markup)
Credits Charged = (Base Cost USD × 1000) × 2
```

---

# PART 4: TEXT/CODE MODELS 🚧

**Status**: Placeholder - To be documented as text/code models are added to AI Models page

## Planned Text/Code Model Categories

### 1. Language Models (LLMs)
- GPT-4, GPT-4 Turbo, GPT-3.5
- Claude 3 Opus, Sonnet, Haiku
- Gemini Pro
- Llama models
- Mixtral models

### 2. Code Generation
- GitHub Copilot models
- CodeLlama
- Codex
- Specialized coding models

### 3. Text Processing
- Summarization
- Translation
- Sentiment analysis
- Named entity recognition

**Pricing Formula**: Same 100% markup rule applies
```
Customer Price = Base Cost × 2 (100% markup)
Credits Charged = (Base Cost USD × 1000) × 2
```

---

# PART 5: EMBEDDINGS MODELS 🚧

**Status**: Placeholder - To be documented as embeddings models are added to AI Models page

## Planned Embeddings Model Categories

### 1. Text Embeddings
- OpenAI text-embedding-3-large
- OpenAI text-embedding-3-small
- Cohere embeddings
- Sentence transformers
- Custom embedding models

### 2. Multimodal Embeddings
- CLIP (text + image)
- ImageBind
- Other multimodal models

### 3. Specialized Embeddings
- Code embeddings
- Domain-specific embeddings
- Multilingual embeddings

**Pricing Formula**: Same 100% markup rule applies
```
Customer Price = Base Cost × 2 (100% markup)
Credits Charged = (Base Cost USD × 1000) × 2
```

---

# APPENDIX: General Implementation Guidelines

## Adding New Model Categories

When implementing a new model category (video, image, text, embeddings):

1. **Update This Skill**:
   - Replace the 🚧 placeholder section with detailed implementation
   - Document provider-specific configuration
   - Add critical implementation details (like MiniMax TTS v2 section)
   - Include common errors and solutions

2. **Create Provider Class**:
   - Follow existing provider patterns (see `huggingface-deployment.md` skill)
   - Implement cost calculation with 100% markup
   - Add comprehensive error handling

3. **Database Schema**:
   - Add model catalog tables
   - Track usage and costs
   - Store provider-specific metadata

4. **API Endpoints**:
   - Implement RESTful endpoints
   - Add credit checks before API calls
   - Deduct credits after successful generation
   - Log all usage for analytics

5. **Frontend Integration**:
   - Add models to AI Models page catalog
   - Create playground interfaces
   - Show pricing and capabilities

6. **Testing**:
   - Unit tests for provider integration
   - Integration tests for endpoints
   - Verify 100% markup in all tests
   - Test error scenarios

## Cross-Reference Skills

- `huggingface-deployment.md` - HuggingFace provider patterns
- `audio-transcribe.md` - Audio transcription workflows
- `mandatory-tdd.md` - Testing requirements
- `code-quality.md` - Security and validation standards

---

Refs #1179
