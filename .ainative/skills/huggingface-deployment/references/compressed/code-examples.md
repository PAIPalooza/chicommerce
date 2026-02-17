# HuggingFace Deployment: Audio Models

## Audio TTS Model (Inference API)

### Provider Implementation

```python
class AudioModelProvider(BaseAIProvider):
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
            base_cost_usd = Decimal("0.001")
            estimated_duration = len(text) / 10

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
@router.post("/tts", response_model=TTSResponse)
async def generate_tts(
    request: TTSRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    audio_model = db.query(AudioModel).filter(
        AudioModel.model_id == request.model_id
    ).first()

    if not audio_model:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Audio model '{request.model_id}' not found"
        )

    provider = AudioModelProvider(
        api_key=os.getenv("HUGGINGFACE_API_KEY"),
        model_id=request.model_id
    )

    result = await provider.generate_speech(
        text=request.text,
        voice=request.voice
    )

    base_cost_usd = result["cost_usd"]
    base_cost_credits = int(base_cost_usd / Decimal("0.04"))
    base_cost_credits = max(1, base_cost_credits)

    billing_service = BillingService(db)
    final_cost_credits = await billing_service.calculate_cost_with_markup(
        user_id=current_user.id,
        base_cost=base_cost_credits,
        developer_markup=current_user.developer_markup
    )

    if current_user.credits < final_cost_credits:
        raise HTTPException(
            status_code=status.HTTP_402_PAYMENT_REQUIRED,
            detail=f"Insufficient credits. Required: {final_cost_credits}, Available: {current_user.credits}"
        )

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
def upgrade():
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
        sa.Column('status', sa.String(20), default='active'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now())
    )

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
```

### Provider Factory

```python
class AIProviderFactory:
    _providers: Dict[str, Type[BaseAIProvider]] = {
        AIProviderSchema.HUGGINGFACE: AudioModelProvider,
    }

    @classmethod
    def get_audio_provider(
        cls,
        model_id: str,
        api_key: Optional[str] = None
    ) -> AudioModelProvider:
        if api_key is None:
            api_key = os.environ.get("HUGGINGFACE_API_KEY")
            if not api_key:
                raise ValueError("HUGGINGFACE_API_KEY not found")

        return AudioModelProvider(api_key=api_key, model_id=model_id)
```

### Cost Calculation Helper

```python
class BillingService:
    CREDIT_VALUE_USD = Decimal("0.04")

    @staticmethod
    def usd_to_credits(amount_usd: Decimal) -> int:
        credits = int(amount_usd / BillingService.CREDIT_VALUE_USD)
        return max(1, credits)
```

Refs #1179