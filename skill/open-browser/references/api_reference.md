# OpenBrowser API Reference

Complete REST API documentation for OpenBrowser Agent Server.

## Base URL

- HTTP: `http://127.0.0.1:8765`
- WebSocket: `ws://127.0.0.1:8766`

---

## Health & Status

### GET /health

Server health check (does not require extension connection).

**Response:**
```json
{
  "status": "healthy",
  "websocket_connected": true,
  "websocket_connections": 1
}
```

### GET /api

API info with extension connection status.

**Response:**
```json
{
  "name": "Local Chrome Server",
  "version": "0.1.0",
  "status": "running",
  "websocket_connected": true,
  "websocket_connections": 1
}
```

---

## Configuration

### GET /api/config/llm

Get LLM configuration (API key masked).

**Response:**
```json
{
  "success": true,
  "config": {
    "model": "dashscope/qwen3.5-plus",
    "base_url": "https://dashscope.aliyuncs.com/compatible-mode/v1",
    "api_key": "********",
    "has_api_key": true
  }
}
```

### POST /api/config/llm

Update LLM configuration.

**Request Body:**
```json
{
  "model": "dashscope/qwen3.5-plus",
  "base_url": "https://dashscope.aliyuncs.com/compatible-mode/v1",
  "api_key": "sk-xxx"
}
```

**Response:**
```json
{
  "success": true,
  "message": "LLM configuration updated successfully",
  "config": {
    "model": "dashscope/qwen3.5-plus",
    "base_url": "https://dashscope.aliyuncs.com/compatible-mode/v1",
    "api_key": "********",
    "has_api_key": true
  }
}
```

### GET /api/config

Get full application configuration.

**Response:**
```json
{
  "success": true,
  "config": {
    "llm": {
      "model": "...",
      "base_url": "...",
      "api_key": "********",
      "has_api_key": true
    },
    "default_cwd": "/path/to/workspace",
    "is_configured": true
  }
}
```

### GET /api/config/cwd

Get default working directory.

### POST /api/config/cwd

Set default working directory.

**Request Body:**
```json
{
  "cwd": "/path/to/workspace"
}
```

---

## Agent Conversations

### POST /agent/conversations

Create a new agent conversation.

**Request Body:**
```json
{
  "cwd": "/path/to/working/directory"
}
```

**Response:**
```json
{
  "success": true,
  "conversation_id": "550e8400-e29b-41d4-a716-446655440000",
  "message": "Conversation created: ...",
  "cwd": "/path/to/working/directory"
}
```

### GET /agent/conversations

List all conversations.

**Query Parameters:**
- `status`: Filter by status (`active`, `idle`, `error`, `completed`)

**Response:**
```json
{
  "success": true,
  "conversations": [
    {
      "id": "...",
      "status": "idle",
      "created_at": "2025-01-15T10:30:00Z",
      "message_count": 5
    }
  ],
  "count": 1,
  "filter": null
}
```

### GET /agent/conversations/{conversation_id}

Get conversation details.

**Response:**
```json
{
  "success": true,
  "conversation": {
    "id": "...",
    "status": "active",
    "created_at": "...",
    "message_count": 3
  }
}
```

### DELETE /agent/conversations/{conversation_id}

Delete a conversation.

### GET/POST /agent/conversations/{conversation_id}/messages

Send message or connect to SSE stream.

**GET:** Connect to SSE stream for real-time updates.

**POST:** Send message and receive SSE stream response.

**Request Body (POST):**
```json
{
  "text": "Go to example.com and extract the main heading",
  "cwd": "."
}
```

**SSE Events:**

The response is a Server-Sent Events stream with the following event types:

| Event Type | Description |
|------------|-------------|
| `connected` | Stream connection established |
| `heartbeat` | Periodic keepalive (30s interval) |
| `thought` | AI thinking/reasoning |
| `action` | Tool action being executed |
| `observation` | Tool result/observation |
| `message` | AI response text |
| `error` | Error occurred |
| `complete` | Conversation turn completed |

**Example SSE Stream:**
```
event: connected
data: {"status": "connected", "conversation_id": "..."}

event: thought
data: {"content": "I need to navigate to the website first..."}

event: action
data: {"action": "tab_init", "params": {"url": "https://example.com"}}

event: observation
data: {"result": {"success": true, "screenshot": "base64..."}}

event: message
data: {"content": "I've navigated to example.com and found the heading is 'Example Domain'"}

event: complete
data: {"conversation_id": "...", "status": "completed"}
```

### GET /agent/conversations/{conversation_id}/events

Get event history (without images).

**Response:**
```json
{
  "success": true,
  "conversation_id": "...",
  "events": [
    {
      "event_type": "message",
      "event_data": {"content": "..."}
    }
  ],
  "count": 10
}
```

### GET /agent/conversations/{conversation_id}/replay

Replay conversation as SSE stream.

### GET /agent/conversations/{conversation_id}/messages

Get user messages only.

---

## Browser Commands (Internal)

These are used by the agent internally via the extension:

### Tab Management
- `tab_init` - Initialize tab with URL
- `tab_open` - Open new tab
- `tab_switch` - Switch to tab
- `tab_close` - Close tab
- `tab_refresh` - Refresh page
- `tab_list` - List all tabs

### Visual Interaction
- `highlight_elements` - Get interactive elements with IDs
- `click_element` - Click element by ID
- `hover_element` - Hover element by ID
- `scroll_element` - Scroll element by ID
- `keyboard_input` - Type text into element

### JavaScript Execution
- `javascript_execute` - Run arbitrary JavaScript

### Screenshots
- `screenshot` - Capture page screenshot

### Dialogs
- `handle_dialog` - Accept/dismiss browser dialogs

---

## Error Handling

All endpoints return errors in consistent format:

```json
{
  "detail": "Error message describing the issue"
}
```

**Common HTTP Status Codes:**
- `400` - Bad request (missing fields, invalid JSON)
- `404` - Conversation not found
- `500` - Internal server error

---

## Rate Limiting

No built-in rate limiting. Limited by:
- LLM API rate limits (DashScope)
- Browser rendering speed
- Network latency

---

## WebSocket Protocol

Extension communication uses WebSocket on port 8766.

**Message Format:**
```json
{
  "type": "command_type",
  "conversation_id": "...",
  "params": {...}
}
```

**Response Format:**
```json
{
  "type": "response",
  "conversation_id": "...",
  "success": true,
  "data": {...}
}
```
