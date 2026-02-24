# REST API Reference

## Base URL

```
http://127.0.0.1:8765
```

Default host and port can be changed via configuration.

## Authentication

No authentication required for local development. In production, consider adding API key authentication.

## Response Format

All endpoints return JSON responses with the following structure:

```json
{
  "success": true,
  "message": "Operation completed successfully",
  "data": { /* command-specific data */ },
  "error": null,
  "timestamp": 1678886400.123
}
```

Error responses:
```json
{
  "success": false,
  "message": null,
  "data": null,
  "error": "Error description",
  "timestamp": 1678886400.123
}
```

## Health Check Endpoints

### GET `/`
**Description**: Server information and status

**Response**:
```json
{
  "success": true,
  "message": "Local Chrome Server is running",
  "data": {
    "name": "Local Chrome Server",
    "version": "0.1.0",
    "status": "healthy",
    "websocket_connections": 1,
    "extensions_connected": 1
  },
  "timestamp": 1678886400.123
}
```

### GET `/health`
**Description**: Simple health check

**Response**:
```json
{
  "success": true,
  "message": "Server is healthy",
  "data": {
    "status": "ok",
    "timestamp": 1678886400.123
  },
  "timestamp": 1678886400.123
}
```

## Command Execution

### POST `/command`
**Description**: Execute any command

**Request Body**:
```json
{
  "type": "command_type",
  "command_id": "optional-unique-id",
  // ... command-specific parameters
}
```

**Command Types**:
- `javascript_execute`: Execute JavaScript code in browser tab (core functionality)
- `screenshot`: Capture screenshot (WYSIWYG mode - actual dimensions)
- `tab`: Tab operations (init, open, close, switch, list, refresh)
- `get_tabs`: Get list of all tabs (shows only managed tabs when session initialized)

**Response**:
```json
{
  "success": true,
  "message": "Command executed successfully",
  "data": { /* command-specific response data */ },
  "command_id": "request-command-id",
  "timestamp": 1678886400.123
}
```

## JavaScript Execution

### POST `/javascript/execute`
**Description**: Execute JavaScript code in browser tab (primary interaction method)

**Request Body**:
```json
{
  "script": "document.querySelector('#button').click()",
  "return_by_value": true,
  "await_promise": false,
  "timeout": 30000,
  "tab_id": 123,  // optional, uses current managed tab if not specified
  "command_id": "js-1"
}
```

**Parameters**:
- `script` (string): JavaScript code to execute (required)
- `return_by_value` (boolean, optional): Return result as serializable JSON (default: true)
- `await_promise` (boolean, optional): Wait for Promise resolution (default: false)
- `timeout` (number, optional): Execution timeout in milliseconds (default: 30000)
- `tab_id` (number, optional): Target tab ID (uses current managed tab if not specified)

**Response**:
```json
{
  "success": true,
  "message": "JavaScript executed successfully",
  "data": {
    "result": {/* JavaScript return value */},
    "tab_id": 123
  },
  "command_id": "js-1",
  "timestamp": 1678886400.123
}
```

**Usage Examples**:
```javascript
// Click a button
{"script": "document.querySelector('#submit').click()"}

// Fill form field
{"script": "document.querySelector('#email').value = 'test@example.com'"}

// Scroll page
{"script": "window.scrollTo(0, document.body.scrollHeight)"}

// Extract data with return value
{
  "script": "({title: document.title, url: window.location.href})",
  "return_by_value": true
}

// Handle async operations
{
  "script": "fetch('/api/data').then(r => r.json())",
  "await_promise": true
}
```

## Screenshot Command

### POST `/screenshot`
**Description**: Capture screenshot of current tab (WYSIWYG mode - actual viewport dimensions)

**Request Body**:
```json
{
  "include_cursor": true,
  "quality": 90,
  "tab_id": 123,
  "command_id": "screenshot-1"
}
```

**Parameters**:
- `include_cursor` (boolean, optional): Include mouse cursor in screenshot (default: true)
- `quality` (number, optional): JPEG quality 1-100 (default: 90, PNG ignores this parameter)
- `tab_id` (number, optional): Target tab ID (uses current managed tab if not specified)

**Response**:
```json
{
  "success": true,
  "message": "Screenshot captured",
  "data": {
    "imageData": "data:image/png;base64,iVBORw0KGgo...",
    "format": "png",
    "width": 1920,
    "height": 1080,
    "viewportWidth": 1920,
    "viewportHeight": 1080,
    "devicePixelRatio": 2,
    "quality": 90,
    "includeCursor": true,
    "tab_id": 123,
    "captureMethod": "cdp",
    "timestamp": 1678886400.123
  },
  "command_id": "screenshot-1",
  "timestamp": 1678886400.123
}
```

**Note**: The `imageData` field contains a data URL with base64-encoded image. You can extract the base64 portion after the comma.

## Tab Commands

### POST `/tabs`
**Description**: Tab management operations

**Request Body**:
```json
{
  "action": "open",  // "init", "open", "close", "switch", "list"
  "url": "https://example.com",  // required for "init" and "open"
  "tab_id": 123,  // required for "close", "switch"
  "command_id": "tab-1"
}
```

**Actions**:
- `init`: Initialize new managed session with starting URL (creates tab group)
- `open`: Open new tab with specified URL (automatically added to managed tab group)
- `close`: Close specified tab
- `switch`: Switch to specified tab
- `list`: List all tabs (shows only managed tabs when session initialized)

**Response for "init"**:
```json
{
  "success": true,
  "message": "Session initialized with https://example.com",
  "data": {
    "tabId": 456,
    "groupId": 1070690641,
    "url": "https://example.com/",
    "isManaged": true
  },
  "command_id": "tab-1",
  "timestamp": 1678886400.123
}
```

**Response for "open"**:
```json
{
  "success": true,
  "message": "Tab opened successfully",
  "data": {
    "tabId": 456,
    "url": "https://example.com",
    "title": "Example Domain"
  },
  "command_id": "tab-1",
  "timestamp": 1678886400.123
}
```

**Response for "close"**:
```json
{
  "success": true,
  "message": "Tab closed successfully",
  "data": {
    "tabId": 123
  },
  "command_id": "tab-1",
  "timestamp": 1678886400.123
}
```

**Response for "switch"**:
```json
{
  "success": true,
  "message": "Switched to tab 123",
  "data": {
    "tabId": 123,
    "active": true
  },
  "command_id": "tab-1",
  "timestamp": 1678886400.123
}
```

**Response for "list"**:
```json
{
  "success": true,
  "message": "Found 3 tabs",
  "data": {
    "tabs": [
      {
        "id": 123,
        "title": "Google",
        "url": "https://google.com",
        "active": true,
        "windowId": 1
      },
      {
        "id": 456,
        "title": "Example",
        "url": "https://example.com",
        "active": false,
        "windowId": 1
      }
    ],
    "count": 2
  },
  "command_id": "tab-1",
  "timestamp": 1678886400.123
}
```

### GET `/tabs`
**Description**: Get list of all tabs (same as POST with action="list")

**Response**: Same as POST `/tabs` with action="list"

## Error Handling

### HTTP Status Codes
- `200 OK`: Command executed successfully
- `400 Bad Request`: Invalid command or parameters
- `404 Not Found`: Endpoint not found
- `422 Unprocessable Entity`: Validation error
- `503 Service Unavailable`: Server or extension not ready

### Common Errors

**Invalid Command Type**:
```json
{
  "success": false,
  "message": null,
  "data": null,
  "error": "Unknown command type: invalid_type",
  "timestamp": 1678886400.123
}
```

**Missing Required Parameter**:
```json
{
  "success": false,
  "message": null,
  "data": null,
  "error": "Field required: 'dx'",
  "timestamp": 1678886400.123
}
```

**Extension Not Connected**:
```json
{
  "success": false,
  "message": null,
  "data": null,
  "error": "No Chrome extension connected",
  "timestamp": 1678886400.123
}
```

## Examples

### Using curl

**Check server health**:
```bash
curl http://127.0.0.1:8765/health
```

**Execute JavaScript (click button)**:
```bash
curl -X POST http://127.0.0.1:8765/command \
  -H "Content-Type: application/json" \
  -d '{"type": "javascript_execute", "script": "document.querySelector(\"#submit-button\").click()"}'
```

**Execute JavaScript (fill form)**:
```bash
curl -X POST http://127.0.0.1:8765/command \
  -H "Content-Type: application/json" \
  -d '{"type": "javascript_execute", "script": "document.querySelector(\"#email\").value = \"test@example.com\""}'
```

**Take screenshot**:
```bash
curl -X POST http://127.0.0.1:8765/screenshot \
  -H "Content-Type: application/json" \
  -d '{"include_cursor": true, "quality": 90}' \
  -o screenshot.json
```

**Initialize managed session**:
```bash
curl -X POST http://127.0.0.1:8765/tabs \
  -H "Content-Type: application/json" \
  -d '{"action": "init", "url": "https://example.com"}'
```

**Open new tab**:
```bash
curl -X POST http://127.0.0.1:8765/tabs \
  -H "Content-Type: application/json" \
  -d '{"action": "open", "url": "https://google.com"}'
```

### Using Python

```python
import requests

base_url = "http://127.0.0.1:8765"

# Check health
response = requests.get(f"{base_url}/health")
print(response.json())

# Execute JavaScript to click a button
response = requests.post(f"{base_url}/command", json={
    "type": "javascript_execute",
    "script": "document.querySelector('#submit-button').click()",
    "tab_id": 123  # optional
})
print(response.json())

# Execute JavaScript to fill form
response = requests.post(f"{base_url}/command", json={
    "type": "javascript_execute",
    "script": "document.querySelector('#email').value = 'test@example.com'"
})
print(response.json())

# Take screenshot and save
response = requests.post(f"{base_url}/screenshot", json={
    "include_cursor": True,
    "quality": 90
})
data = response.json()
if data["success"]:
    import base64
    image_data = data["data"]["imageData"]
    # Extract base64 from data URL
    if image_data.startswith('data:image/'):
        image_data = image_data.split(',', 1)[1]
    
    with open('screenshot.png', 'wb') as f:
        f.write(base64.b64decode(image_data))
    print("Screenshot saved")
```

## Rate Limiting

No rate limiting implemented for local development. In production, consider adding rate limiting to prevent abuse.

## Versioning

API version is included in the server response metadata. Current version: 0.1.0

Backward compatibility will be maintained within major version 0.x. Breaking changes will be introduced in major version 1.0.0.