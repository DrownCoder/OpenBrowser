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
