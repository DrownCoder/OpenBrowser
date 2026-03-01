# Learnings: Visual Interaction Refactor

## 2026-02-28: Interactive Element Detection Module

### TypeScript Type Inference with Circular References
- **Issue**: When a variable references another variable that later gets assigned from it, TypeScript infers `any` type.
- **Example**: `const parent = current.parentElement; ... current = parent;` causes `parent` to have implicit `any`.
- **Fix**: Add explicit type annotation: `const parent: Element | null = current.parentElement;`

### CSSRule vs CSSStyleRule
- **Issue**: `CSSRule` type doesn't have `selectorText` property.
- **Fix**: Use type guard `'selectorText' in rule` before accessing, or cast to `CSSStyleRule`.

### Element Detection Patterns
1. **Clickable**: Check tag name, role attribute, event handler attributes (onclick, ng-click, @click), and cursor style
2. **Scrollable**: Check computed style for `overflow: auto/scroll` AND actual scrollable content
3. **Inputable**: Check tag name (input, textarea, select) and contenteditable attribute
4. **Hoverable**: Check cursor: pointer style, :hover pseudo-class rules, and ARIA roles

### Selector Generation Priority
1. Element ID (`#id`)
2. Name attribute (`[name="..."]`)
3. data-testid attribute
4. aria-label attribute
5. CSS path (fallback using nth-of-type)

## 2026-02-28: Page Context Execution for Element Detection

### Document Access in Background Script
- **Issue**: `document is not defined` error when calling `detectInteractiveElements()` directly in background script
- **Root Cause**: Background scripts run in a worker context without DOM access
- **Fix**: Execute detection script in page context using `javascript.executeJavaScript()` (CDP Runtime.evaluate)

### Key Change
- Removed direct call to `detectInteractiveElements()` which used `document`
- Built detection script as string and executed via CDP
- Result accessed via `detectionResult.result.value` (CDP returns result in `.value` property)

### Pattern for Page-Context Operations
```typescript
const script = `(function() {
  // DOM operations here - runs in page context
  return result;
})();`;

const result = await javascript.executeJavaScript(tabId, conversationId, script, true, false, timeout);
const data = result.result?.value; // Access the returned data
```

## 2026-03-01: Element Deduplication & Detection Refinement

### Problem: Parent-Child Element Overlap
- **Issue**: Large containers with `cursor: pointer` were being highlighted alongside their smaller clickable children, causing overlapping bounding boxes
- **Root Cause Chain**:
  ```
  BUTTON (clickable, 2,532px²)
    └── SPAN (cursor: pointer → hoverable, 1,385px²)
          └── SVG (cursor: pointer → hoverable, 100px²)
  ```
  All three elements were being detected and returned!

### Solution: Multi-Layer Fix

#### 1. Exclude Clickable Children in `isHoverable`
```javascript
function isHoverable(el) {
  if (style.cursor !== 'pointer') return false;
  
  // Check parent chain for clickable elements
  let parent = el.parentElement;
  while (parent && parent !== document.body) {
    if (['a', 'button', 'input', ...].includes(parent.tagName)) {
      return false; // Skip - parent is already clickable
    }
    parent = parent.parentElement;
  }
  return true;
}
```

#### 2. Bbox-Based Deduplication in Detection Script
```javascript
// Sort by area (largest first)
elements.sort((a, b) => bArea - aArea);

// Skip larger elements that mostly contain smaller elements
const SKIP_OVERLAP_RATIO = 0.6;
if (overlapArea / smallerArea > SKIP_OVERLAP_RATIO) {
  shouldSkip = true; // Skip the larger container
}
```

### Remaining Issue: Adjacent Buttons (2026-03-01)
- **Problem**: Unlike/Favorite/Share buttons still not individually highlighted
- **Cause**: These buttons are **adjacent** (not nested) to VoteButton
  ```
  [赞同 Button] [评论 Button] [收藏 Button] [分享 Button]  // Same level, not nested
  ```
- Deduplication only removes **containing** elements, not **adjacent** ones
- Need to investigate why these buttons aren't detected as clickable

### Diagnostic Code for Adjacent Buttons
```javascript
const actions = ['赞同', '评论', '收藏', '分享', '喜欢'];
actions.forEach(text => {
  const btns = Array.from(document.querySelectorAll('*')).filter(el => 
    el.textContent?.includes(text) && el.textContent?.length < 10
  );
  btns.forEach(btn => {
    console.log(`${text}:`, btn.tagName, btn.className?.slice(0,30));
    console.log('  cursor:', getComputedStyle(btn).cursor);
  });
});
```

### Key Learning: Inline Detection Scripts
- Detection logic in `interactive-elements.ts` was **NOT being used** for highlight_elements!
- Actual detection happens via **inline script string** in `background/index.ts` (line ~909)
- This script is injected into page context via `javascript.executeJavaScript()`
- **Always modify the inline script in background/index.ts for highlight_elements!**
