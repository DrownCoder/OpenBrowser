import type { InteractiveElement, ElementType } from '../types';

export interface DetectOptions {
  elementTypes?: ElementType[];
  includeHidden?: boolean;
}

/**
 * Detects interactive elements on the page
 * @param options Detection options
 * @returns Array of interactive elements
 */
export function detectInteractiveElements(options?: DetectOptions): InteractiveElement[] {
  const elementTypes = options?.elementTypes ?? ['clickable', 'scrollable', 'inputable', 'hoverable'];
  const includeHidden = options?.includeHidden ?? false;

  const counts: Record<ElementType, number> = {
    clickable: 0,
    scrollable: 0,
    inputable: 0,
    hoverable: 0,
  };

  const elements: InteractiveElement[] = [];
  const allElements = Array.from(document.querySelectorAll('*'));

  for (const el of allElements) {
    // Skip hidden elements unless explicitly included
    if (!includeHidden && !isVisible(el)) continue;

    // Check each element type
    if (elementTypes.includes('clickable') && isClickable(el)) {
      const element = createElementInfo(el, 'clickable', counts.clickable);
      if (element) {
        elements.push(element);
        counts.clickable++;
      }
    } else if (elementTypes.includes('scrollable') && isScrollable(el)) {
      const element = createElementInfo(el, 'scrollable', counts.scrollable);
      if (element) {
        elements.push(element);
        counts.scrollable++;
      }
    } else if (elementTypes.includes('inputable') && isInputable(el)) {
      const element = createElementInfo(el, 'inputable', counts.inputable);
      if (element) {
        elements.push(element);
        counts.inputable++;
      }
    } else if (elementTypes.includes('hoverable') && isHoverable(el)) {
      const element = createElementInfo(el, 'hoverable', counts.hoverable);
      if (element) {
        elements.push(element);
        counts.hoverable++;
      }
    }
  }

  return elements;
}

/**
 * Check if element is clickable
 * Matches: a, button, [role="button"], [onclick], [ng-click], [@click], input[type="submit"], input[type="button"]
 */
function isClickable(el: Element): boolean {
  const tag = el.tagName.toUpperCase();

  // Check tag names
  if (tag === 'A' || tag === 'BUTTON') return true;

  // Check input types
  if (tag === 'INPUT') {
    const inputEl = el as HTMLInputElement;
    const type = inputEl.type?.toLowerCase();
    if (type === 'submit' || type === 'button' || type === 'image' || type === 'reset') {
      return true;
    }
    return false;
  }

  // Check attributes
  if (el.getAttribute('role') === 'button') return true;
  if (el.hasAttribute('onclick')) return true;
  if (el.hasAttribute('ng-click')) return true;
  if (el.hasAttribute('@click')) return true;

  // Check for cursor: pointer style
  const style = window.getComputedStyle(el);
  if (style.cursor === 'pointer') {
    // Additional check: must have some interaction indicator
    if (el.hasAttribute('tabindex') || el.getAttribute('role') === 'link') {
      return true;
    }
  }

  return false;
}

/**
 * Check if element is scrollable
 * Elements with overflow: auto/scroll AND scrollHeight > clientHeight
 */
function isScrollable(el: Element): boolean {
  const style = window.getComputedStyle(el);
  const overflow = style.overflow.toLowerCase();
  const overflowY = style.overflowY.toLowerCase();
  const overflowX = style.overflowX.toLowerCase();

  const hasScrollOverflow =
    overflow === 'auto' || overflow === 'scroll' ||
    overflowY === 'auto' || overflowY === 'scroll' ||
    overflowX === 'auto' || overflowX === 'scroll';

  if (!hasScrollOverflow) return false;

  const htmlEl = el as HTMLElement;
  const hasScrollableContent =
    htmlEl.scrollHeight > htmlEl.clientHeight ||
    htmlEl.scrollWidth > htmlEl.clientWidth;

  return hasScrollableContent;
}

/**
 * Check if element is inputable
 * Matches: input, textarea, [contenteditable="true"], select
 */
function isInputable(el: Element): boolean {
  const tag = el.tagName.toUpperCase();

  if (tag === 'TEXTAREA' || tag === 'SELECT') return true;

  if (tag === 'INPUT') {
    const inputEl = el as HTMLInputElement;
    const type = inputEl.type?.toLowerCase();
    // Exclude button-like inputs (handled by isClickable)
    if (type === 'submit' || type === 'button' || type === 'image' || type === 'reset') {
      return false;
    }
    return true;
  }

  // Check contenteditable
  const contentEditable = el.getAttribute('contenteditable');
  if (contentEditable === 'true' || contentEditable === '') return true;

  return false;
}

/**
 * Check if element is hoverable
 * Elements with :hover CSS or cursor: pointer style
 */
function isHoverable(el: Element): boolean {
  // Skip elements already classified as clickable or inputable
  if (isClickable(el) || isInputable(el)) return false;

  const style = window.getComputedStyle(el);

  // Check cursor: pointer
  if (style.cursor === 'pointer') return true;

  // Check for :hover pseudo-class by comparing styles
  // This is a heuristic - check for common hover indicators
  const parent = el.parentElement;
  if (parent) {
    const hoverSelector = el.id ? `#${el.id}:hover` : null;
    if (hoverSelector) {
      try {
        // Try to see if there's a hover rule defined
        const sheets = document.styleSheets;
        for (const sheet of sheets) {
          try {
            const rules = sheet.cssRules || sheet.rules;
            for (const rule of rules) {
              // Type guard to check if it's a CSSStyleRule with selectorText
              if ('selectorText' in rule && typeof rule.selectorText === 'string' && rule.selectorText.includes(':hover')) {
                const styleRule = rule as CSSStyleRule;
                if (styleRule.selectorText.includes(el.tagName.toLowerCase()) ||
                    (el.id && styleRule.selectorText.includes(`#${el.id}`)) ||
                    (el.className && typeof el.className === 'string' &&
                     el.className.split(' ').some((c: string) => styleRule.selectorText.includes(`.${c}`)))) {
                  return true;
                }
              }
            }
          } catch {
            // CORS restriction, skip this stylesheet
          }
        }
      } catch {
        // Ignore errors
      }
    }
  }

  // Check for aria roles that suggest interactivity
  const role = el.getAttribute('role');
  if (role === 'menuitem' || role === 'tab' || role === 'tooltip') return true;

  return false;
}

/**
 * Check if element is visible
 * Uses offsetParent check and opacity
 */
function isVisible(el: Element): boolean {
  // Check offsetParent (null for hidden elements)
  if ((el as HTMLElement).offsetParent === null) {
    // Exception: position: fixed elements may have null offsetParent
    const style = window.getComputedStyle(el);
    if (style.position !== 'fixed') return false;
  }

  // Check opacity
  const style = window.getComputedStyle(el);
  if (style.opacity === '0') return false;
  if (style.visibility === 'hidden') return false;
  if (style.display === 'none') return false;

  // Check bounding box
  const bbox = getBBox(el);
  if (bbox.width === 0 || bbox.height === 0) return false;

  return true;
}

/**
 * Check if element is in viewport
 */
function isInViewport(el: Element): boolean {
  const bbox = getBBox(el);

  return (
    bbox.x < window.innerWidth &&
    bbox.x + bbox.width > 0 &&
    bbox.y < window.innerHeight &&
    bbox.y + bbox.height > 0
  );
}

/**
 * Get bounding box for element
 */
function getBBox(el: Element): { x: number; y: number; width: number; height: number } {
  const rect = el.getBoundingClientRect();
  return {
    x: rect.x,
    y: rect.y,
    width: rect.width,
    height: rect.height,
  };
}

/**
 * Generate a CSS selector for the element
 */
function generateSelector(el: Element): string {
  // Prefer id
  if (el.id) {
    return '#' + CSS.escape(el.id);
  }

  // Try name attribute
  const name = el.getAttribute('name');
  if (name) {
    return `[name="${CSS.escape(name)}"]`;
  }

  // Try data-testid
  const dataTestId = el.getAttribute('data-testid');
  if (dataTestId) {
    return `[data-testid="${CSS.escape(dataTestId)}"]`;
  }

  // Try aria-label
  const ariaLabel = el.getAttribute('aria-label');
  if (ariaLabel) {
    return `[aria-label="${CSS.escape(ariaLabel)}"]`;
  }

  // Fall back to CSS path
  return getCssPath(el);
}

/**
 * Generate CSS path for element
 */
function getCssPath(el: Element): string {
  const path: string[] = [];
  let current: Element | null = el;

  while (current && current !== document.documentElement) {
    let selector = current.tagName.toLowerCase();

    // Add nth-child if needed
    const parent: Element | null = current.parentElement;
    if (parent) {
      const siblings = Array.from(parent.children).filter((c: Element) => c.tagName === current!.tagName);
      if (siblings.length > 1) {
        const index = siblings.indexOf(current) + 1;
        selector += `:nth-of-type(${index})`;
      }
    }

    path.unshift(selector);
    current = parent;

    // Stop if we have a unique path
    if (parent) {
      try {
        const testSelector = path.join(' > ');
        if (document.querySelectorAll(testSelector).length === 1) {
          break;
        }
      } catch {
        // Invalid selector, continue building path
      }
    }
  }

  return path.join(' > ');
}

/**
 * Create element info object
 */
function createElementInfo(el: Element, type: ElementType, index: number): InteractiveElement | null {
  const bbox = getBBox(el);
  
  // Skip elements with zero dimensions
  if (bbox.width === 0 || bbox.height === 0) return null;

  const visible = isVisible(el);
  const inViewport = isInViewport(el);

  // Get text content (limit to 200 chars)
  const text = (el.textContent || '').trim().slice(0, 200) || undefined;

  return {
    id: `${type}-${index + 1}`,
    type,
    tagName: el.tagName.toLowerCase(),
    selector: generateSelector(el),
    text,
    bbox,
    isVisible: visible,
    isInViewport: inViewport,
  };
}

/**
 * Score breakdown for an interactive element
 */
export interface ElementScore {
  element: InteractiveElement;
  score: number;
}

/**
 * Sort interactive elements by composite score
 * Ranking: viewport visibility (40%) + size (30%) + z-index (20%) + position (10%)
 * @param elements Array of interactive elements to sort
 * @returns Sorted array with reassigned IDs
 */
export function sortInteractiveElements(elements: InteractiveElement[]): InteractiveElement[] {
  // Calculate score for each element
  const scored = elements.map((el, index) => ({
    element: el,
    score: calculateElementScore(el),
    originalIndex: index, // For tie-breaking
  }));

  // Sort by score descending, then by original index for determinism
  scored.sort((a, b) => {
    if (b.score !== a.score) return b.score - a.score;
    return a.originalIndex - b.originalIndex;
  });

  // Reassign IDs based on new order
  const counts: Record<ElementType, number> = { clickable: 0, scrollable: 0, inputable: 0, hoverable: 0 };
  return scored.map(({ element }) => {
    const newIndex = counts[element.type] + 1;
    counts[element.type]++;
    return { ...element, id: `${element.type}-${newIndex}` };
  });
}

/**
 * Calculate composite score for an element
 */
function calculateElementScore(el: InteractiveElement): number {
  // Viewport visibility (40% weight)
  const viewportScore = el.isInViewport ? 40 : 0;

  // Size score (30% weight) - normalize by viewport
  const area = el.bbox.width * el.bbox.height;
  const viewportArea = window.innerWidth * window.innerHeight;
  const sizeScore = Math.min(30, (area / viewportArea) * 300); // Cap at 30

  // Z-index score (20% weight)
  const zScore = getZIndexScore(el) * 20; // 0-20

  // Position score (10% weight) - top-left is better
  const maxDist = Math.sqrt(window.innerWidth ** 2 + window.innerHeight ** 2);
  const dist = Math.sqrt(el.bbox.x ** 2 + el.bbox.y ** 2);
  const positionScore = (1 - dist / maxDist) * 10; // 0-10

  return viewportScore + sizeScore + zScore + positionScore;
}

/**
 * Get z-index score for an element (0-1 normalized)
 */
function getZIndexScore(el: InteractiveElement): number {
  try {
    const domEl = document.querySelector(el.selector);
    if (!domEl) return 0;

    const style = window.getComputedStyle(domEl);
    const zIndex = style.zIndex;

    // Parse z-index value
    if (zIndex === 'auto' || zIndex === '') return 0.5; // Normal stacking

    const zValue = parseInt(zIndex, 10);
    if (isNaN(zValue)) return 0;

    // Normalize: typical z-index range 0-9999, map to 0-1
    // Negative z-index gets lower score
    if (zValue < 0) return 0;
    return Math.min(1, zValue / 100);
  } catch {
    return 0;
  }
}
