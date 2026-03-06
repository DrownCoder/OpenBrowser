# Task 1: Remove _add_screenshot_to_response() Calls

## Changes Made

✅ **File Modified**: `/Users/yangxiao/git/OpenBrowser-screenshot-refactor/server/core/processor.py`

✅ **Lines Removed**:
- Lines 316-319: Call to `_add_screenshot_to_response()` in `_execute_tab_command()` method
- Lines 353-355: Call to `_add_screenshot_to_response()` in `_execute_javascript_execute()` method

✅ **Method Preserved**: 
- `_add_screenshot_to_response()` method definition (lines 59-111) remains intact for potential rollback

## Current Behavior (After Changes)

### _execute_tab_command() (around line 315)
```python
# BEFORE (removed):
if response.success and command.action in ("init", "switch", "open", "refresh"):
    return await self._add_screenshot_to_response(
        response, command.conversation_id
    )

# AFTER:
# (Just blank lines - method now returns response directly)
```

### _execute_javascript_execute() (around line 346)
```python
# BEFORE (removed):
if response.success:
    return await self._add_screenshot_to_response(
        response, command.conversation_id
    )

# AFTER:
# (Just blank lines - method now returns response directly)
```

## Verification Status

⚠️ **IMPORTANT**: The server is currently running from a different directory:
```
/Users/yangxiao/git/OpenBrowser-new-tab-screenshot/
```

The working directory is:
```
/Users/yangxiao/git/OpenBrowser-screenshot-refactor/
```

## Verification Steps Required

To verify the changes work correctly,1. Stop the current server
2. Start server from the correct directory:
   ```bash
   cd /Users/yangxiao/git/OpenBrowser-screenshot-refactor
   uv run local-chrome-server serve
   ```

3. Run verification tests:
   ```bash
   # Test 1: Tab init should not return screenshot
   curl -s -X POST http://localhost:8765/command \
     -H "Content-Type: application/json" \
     -d '{"type":"tab","action":"init","url":"https://example.com","conversation_id":"test-verify"}' | jq '.data.screenshot'
   # Expected: null
   
   # Test 2: Javascript execute should not return screenshot
   curl -s -X POST http://localhost:8765/command \
     -H "Content-Type: application/json" \
     -d '{"type":"javascript_execute","script":"document.title","conversation_id":"test-verify"}' | jq '.data.screenshot'
   # Expected: null
   ```

## Evidence Files Created

- `/Users/yangxiao/git/OpenBrowser-screenshot-refactor/.sisyphus/evidence/task-1-tab-no-screenshot.txt`
- `/Users/yangxiao/git/OpenBrowser-screenshot-refactor/.sisyphus/evidence/task-1-js-no-screenshot.txt`

Note: These tests were run against the OLD server (wrong directory), so they show screenshots are still present.
After restarting the server in the correct directory, both should return `null`.
