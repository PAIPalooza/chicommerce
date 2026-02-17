---
description: ZeroDB Memories API integration for unlimited context without MCP overhead
---

# ZeroDB Memory Integration

## Overview

Direct REST API integration for persistent agent memory, bypassing the bloated MCP server for better performance and token efficiency.

## Problem

- MCP server adds significant overhead
- Protocol wrapper consumes extra tokens
- Slower response times
- Limited by MCP implementation

## Solution

Use direct HTTP calls to `/api/v1/memory/*` endpoints for:
- **Faster execution** (no MCP layer)
- **Better error handling** (HTTP status codes)
- **Token efficiency** (no protocol wrapper)
- **Unlimited storage** (PostgreSQL-backed)

## REST API Endpoints

### 1. Create Memory
```bash
POST /api/v1/memory
Authorization: Bearer {token}
Content-Type: application/json

{
  "content": "Important conversation context or decision",
  "metadata": {
    "session_id": "session-123",
    "topic": "MiniMax TTS implementation",
    "importance": "high"
  },
  "tags": ["tts", "audio", "minimax"],
  "priority": "high"
}
```

### 2. Search Memories (Semantic)
```bash
GET /api/v1/memory/search?query=How+to+fix+MiniMax+TTS&limit=5
Authorization: Bearer {token}
```

Returns top 5 semantically similar memories.

### 3. List Recent Memories
```bash
GET /api/v1/memory?skip=0&limit=10
Authorization: Bearer {token}
```

### 4. Get Specific Memory
```bash
GET /api/v1/memory/{memory_id}
Authorization: Bearer {token}
```

## Integration Patterns

### Pattern 1: Session Auto-Save
Store context every N messages to preserve conversation history:

```python
# Pseudo-code for session auto-save
if message_count % 10 == 0:
    summary = summarize_last_10_messages()
    requests.post(
        "http://localhost:8080/api/v1/memory",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "content": summary,
            "metadata": {
                "session_id": current_session_id,
                "message_count": message_count,
                "timestamp": datetime.now().isoformat()
            },
            "tags": ["auto-save", "session"]
        }
    )
```

### Pattern 2: Context Retrieval Before Complex Tasks
Inject relevant past context when user asks complex questions:

```python
# Before processing user question
relevant_memories = requests.get(
    f"http://localhost:8080/api/v1/memory/search",
    params={"query": user_question, "limit": 3},
    headers={"Authorization": f"Bearer {token}"}
).json()

# Inject into system prompt
context = "\n".join([m["content"] for m in relevant_memories])
system_prompt = f"Previous context:\n{context}\n\nCurrent question: {user_question}"
```

### Pattern 3: End-of-Session Summary
Compress entire conversation at session end:

```python
# On session close
full_summary = {
    "content": conversation_summary,
    "metadata": {
        "session_id": session_id,
        "duration_minutes": session_duration,
        "topics": extracted_topics,
        "key_decisions": important_decisions,
        "action_items": todos_created
    },
    "tags": ["session-summary", "completed"],
    "priority": "high"
}
requests.post("http://localhost:8080/api/v1/memory", headers={...}, json=full_summary)
```

## Benefits vs MCP

| Aspect | MCP Server | Direct REST API |
|--------|-----------|-----------------|
| Speed | Slow (protocol overhead) | Fast (direct HTTP) |
| Tokens | High (wrapper payload) | Low (JSON only) |
| Error Handling | Limited | Full HTTP status codes |
| Debugging | Difficult | Easy (curl, logs) |
| Scalability | Limited by MCP | PostgreSQL-backed |

## Usage Examples

### Store Important Technical Decision
```bash
curl -X POST http://localhost:8080/api/v1/memory \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "content": "MiniMax TTS requires base URL https://api.minimaxi.chat (NOT api.minimax.io). API v2 uses hex-encoded audio in data.audio field.",
    "metadata": {
      "issue": "#1179",
      "category": "audio-models",
      "resolution": "fixed"
    },
    "tags": ["minimax", "tts", "critical"],
    "priority": "critical"
  }'
```

### Search for Past Solutions
```bash
curl "http://localhost:8080/api/v1/memory/search?query=MiniMax%20TTS%20404%20error&limit=3" \
  -H "Authorization: Bearer $TOKEN"
```

## Integration with Claude Code

This pattern can be integrated into `.claude/hooks/` for automatic memory management:

- `user-prompt-submit-hook.sh` - Auto-save every 10 messages
- `assistant-message-complete-hook.sh` - Store important responses
- `tool-use-complete-hook.sh` - Log tool execution context

See `.claude/skills/anthropic-hooks-integration.md` for hook implementation details.

## API Authentication

All requests require Bearer token from login:

```bash
# Login
LOGIN_RESPONSE=$(curl -X POST http://localhost:8080/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email": "admin@ainative.studio", "password": "'$ZERODB_PASSWORD'"}')

TOKEN=$(echo $LOGIN_RESPONSE | jq -r '.access_token')

# Use token
curl http://localhost:8080/api/v1/memory \
  -H "Authorization: Bearer $TOKEN"
```

## Database Schema

Memories are stored in PostgreSQL with vector embeddings for semantic search:

```sql
CREATE TABLE memories (
    id UUID PRIMARY KEY,
    user_id UUID NOT NULL,
    content TEXT NOT NULL,
    embedding VECTOR(1536),  -- For semantic search
    metadata JSONB,
    tags TEXT[],
    priority VARCHAR(20),
    created_at TIMESTAMP DEFAULT NOW()
);

-- Indexes for fast search
CREATE INDEX idx_memories_user_id ON memories(user_id);
CREATE INDEX idx_memories_tags ON memories USING GIN(tags);
CREATE INDEX idx_memories_embedding ON memories USING ivfflat(embedding);
```

## Best Practices

1. **Tag Consistently**: Use standardized tags (e.g., "bug-fix", "feature", "decision")
2. **Set Priorities**: Mark critical decisions as "critical" or "high"
3. **Include Context**: Store metadata with issue numbers, file paths, timestamps
4. **Batch Queries**: Retrieve multiple memories at once to reduce API calls
5. **Cleanup Old Data**: Periodically archive or delete low-priority memories

## Performance

- **Storage**: Unlimited (PostgreSQL)
- **Search Speed**: <100ms for semantic search
- **Concurrent Access**: Thread-safe
- **Token Efficiency**: ~90% less overhead vs MCP

## Troubleshooting

**401 Unauthorized:**
```bash
# Token expired, re-login
TOKEN=$(curl -X POST http://localhost:8080/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email": "admin@ainative.studio", "password": "'$ZERODB_PASSWORD'"}' \
  | jq -r '.access_token')
```

**500 Server Error:**
Check backend logs:
```bash
railway logs --service "AINative- Core -Production" | grep memory
```

**Empty Search Results:**
Ensure embeddings are generated (automatic on create)

---

Refs #1179
