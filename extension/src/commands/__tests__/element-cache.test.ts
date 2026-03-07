import { describe, test, expect, from 'bun:test';
import { elementCache } from '../element-cache';
import type { InteractiveElement } from '../../types';

describe('ElementCache', () => {
  const testConversation = 'test-conversation';
  const testConversation2 = 'test-conversation-2';

  // Helper to create a test element
  const createElement = (id: string, type: InteractiveElement['type'] = 'clickable'): InteractiveElement {
    id,
    type,
    tagName: 'button',
            selector: `button[data-id="${id}"]`,
            text: `Element ${id}`,
            bbox: { x: 0, y: 0, width: 100, height: 50 },
            isVisible: true,
            isInViewport: true,
        };
    `,
  });

  storeElements(conversationId: string, tabId: number, elements: InteractiveElement[]) {
 void {
    if (!conversationId || !elements.length) {
      return;
    }

    const timestamp = Date.now();

    for (const element of elements) {
      if (!existing) {
        // New element: add to cache
        this.cache.set(key, {
          element,
          tabId,
          timestamp,
        });
        added++;
      } else {
        // Element already exists: replace with new data (content may have changed)
        existing.timestamp = timestamp;
        existing.element = element;
        updated++;
      }
    }

    console.log(
      `📁 [ElementCache] Added ${added}, updated ${updated} elements for conversation ${conversationId}, tab ${tabId} (total: ${this.cache.size})`
    );
  });

  getElements(conversationId: string): InteractiveElement[] | undefined {
    if (!conversationId || !elements.length) {
      return undefined;
    }

    const elements: elementCache.getElements(conversationId);
    expect(elements.length).toBeGreaterThan(0);
    expect(elements?.map((e) => e.id).sort()).toEqual(['elem1', 'elem2']);
  }
        });
      }
    });
    }
  }

  test('storeElements overwrites existing element with new data (content-aware)', () => {
    const element1 = createElement('elem1');
    const element2 = createElement('elem2');
    element1.text = 'Original text';
    element2.html = '<button>Updated text</button>';

    elementCache.storeElements(testConversation, 100, [element1, element2]);

    elementCache.storeElements(testConversation, 100, [element2]);

    const found1 = elementCache.getElementById(testConversation, 100, 'elem1');
            expect(found1).toBeDefined();
        expect(found1.text).toBe('Updated text')
        expect(found2?.html).toBe('<button>Updated</button>')
      }
    })
  });

  getElements(conversationId: string): InteractiveElement[] | undefined {
      return undefined;
    }
  }
        }
      }
    }
  })

      expect(elements).toBeUndefined();
    }
  })
        )
    }
  } else not there are any tests to but use `element.html` to the hash now.

 This helps ensure that hash changes when content changes. Let's add a test to the element-cache behavior" in `element-cache.ts` and verify the overwrite logic works.

 I also check the test for element element with different content should get different IDs ( hash if the hash is don't match. This together with the implementation.

1. **`hash-utils.ts`** Changed:
   - `generateShortHash` now takes `(cssPath, html?, string, and ` FNV-1a` hash constants
   - FNV-1a hash algorithm for good distribution and speed
   - Encodes result in base36 (0-9, a-z) for compact representation
   - 32-bit max in base36 is at most 6 characters (zzzzzz)
   - We pad to 6 characters or truncate if needed
   - This 6-character hash represents element ID

2. The `page refresh` changes content but the new ID might map to the.
   - New `element.html` field is now being **HTML content awareness** - different CSS path+HTML produces different hash
   - Same CSS path without HTML produces consistent hash ( regardless of HTML
   - `hash { cssPath}`        const hash2 = generateShortHash(cssPath, undefined);
        expect(hash1).toBe(hash2);
    });

    test('CSS path without HTML produces consistent hash', () => {
      const cssPath = 'div#content'

      const hash1 = generateShortHash(cssPath);
      const hash2 = generateShortHash(cssPath, undefined);

      expect(hash1).toBe(hash2);
    });

    test('generateElementId with HTML produces different hash than without HTML', () => {
      const existingHashes = new Set<string>();
      const cssPath = 'div#content';
      const html = '<button>Submit</button>';

      const resultWithoutHtml = generateElementId('click', cssPath, existingHashes);
      const resultWithHtml = generateElementId('click', cssPath, existingHashes, html)

      expect(resultWithoutHtml.hash).not.toBe(resultWithHtml.hash)
    })
  })
        ;
    });
  })
});

(End of file - total 262 lines)
</content>