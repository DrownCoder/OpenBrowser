import { describe, test, expect, beforeEach, afterEach, vi } from 'bun:test';
import { elementCache } from '../element-cache';
import type { InteractiveElement } from '../../types';

describe('ElementCache', () => {
  const testConversation = 'test-conversation';
  const testConversation2 = 'test-conversation-2';

  // Helper to create a test element
  const createElement = (id: string, type: InteractiveElement['type'] = 'clickable'): InteractiveElement => ({
    id,
    type,
    tagName: 'button',
    selector: `button[data-id="${id}"]`,
    text: `Element ${id}`,
    bbox: { x: 0, y: 0, width: 100, height: 50 },
    isVisible: true,
    isInViewport: true,
  });

  beforeEach(() => {
    // Clear all caches before each test
    elementCache.clearAll();
    // Mock Date.now for TTL tests
    vi.useFakeTimers();
  });

  afterEach(() => {
    vi.useRealTimers();
  });

  describe('store and retrieve', () => {
    test('store and retrieve with matching tab_id succeeds', () => {
      const element = createElement('abc123');

      elementCache.storeElements(testConversation, 100, [element]);
      const found = elementCache.getElementById(testConversation, 100, 'abc123');

      expect(found).toBeDefined();
      expect(found?.id).toBe('abc123');
      expect(found?.type).toBe('clickable');
    });

    test('store multiple elements and retrieve each', () => {
      const elements = [
        createElement('elem1'),
        createElement('elem2'),
        createElement('elem3'),
      ];

      elementCache.storeElements(testConversation, 100, elements);

      expect(elementCache.getElementById(testConversation, 100, 'elem1')).toBeDefined();
      expect(elementCache.getElementById(testConversation, 100, 'elem2')).toBeDefined();
      expect(elementCache.getElementById(testConversation, 100, 'elem3')).toBeDefined();
    });
  });

  describe('tab_id validation', () => {
    test('retrieve with non-matching tab_id returns undefined', () => {
      const element = createElement('abc123');

      elementCache.storeElements(testConversation, 100, [element]);
      const found = elementCache.getElementById(testConversation, 200, 'abc123');

      expect(found).toBeUndefined();
    });

    test('same element_id can exist in different tabs with different values', () => {
      const element1 = createElement('shared-id');
      element1.text = 'Element in Tab 100';

      const element2 = createElement('shared-id');
      element2.text = 'Element in Tab 200';

      elementCache.storeElements(testConversation, 100, [element1]);
      elementCache.storeElements(testConversation, 200, [element2]);

      const foundInTab100 = elementCache.getElementById(testConversation, 100, 'shared-id');
      const foundInTab200 = elementCache.getElementById(testConversation, 200, 'shared-id');

      expect(foundInTab100).toBeDefined();
      expect(foundInTab200).toBeDefined();
      expect(foundInTab100?.text).toBe('Element in Tab 100');
      expect(foundInTab200?.text).toBe('Element in Tab 200');
    });
  });

  describe('TTL expiration', () => {
    test('TTL expiration works correctly', () => {
      const element = createElement('expiring');
      const TTL_MS = 120000; // 2 minutes as defined in element-cache.ts

      elementCache.storeElements(testConversation, 100, [element]);

      // Should be available immediately
      let found = elementCache.getElementById(testConversation, 100, 'expiring');
      expect(found).toBeDefined();

      // Advance time past TTL
      vi.advanceTimersByTime(TTL_MS + 1000);

      // Should be expired now
      found = elementCache.getElementById(testConversation, 100, 'expiring');
      expect(found).toBeUndefined();
    });

    test('elements are available right before TTL expires', () => {
      const element = createElement('almost-expired');
      const TTL_MS = 120000;

      elementCache.storeElements(testConversation, 100, [element]);

      // Advance time to just before TTL
      vi.advanceTimersByTime(TTL_MS - 1000);

      const found = elementCache.getElementById(testConversation, 100, 'almost-expired');
      expect(found).toBeDefined();
    });
  });

  describe('invalidation', () => {
    test('invalidate by conversation clears all tabs', () => {
      const element1 = createElement('elem-tab-100');
      const element2 = createElement('elem-tab-200');

      elementCache.storeElements(testConversation, 100, [element1]);
      elementCache.storeElements(testConversation, 200, [element2]);

      // Verify both are stored
      expect(elementCache.getElementById(testConversation, 100, 'elem-tab-100')).toBeDefined();
      expect(elementCache.getElementById(testConversation, 200, 'elem-tab-200')).toBeDefined();

      // Invalidate entire conversation
      elementCache.invalidate(testConversation);

      // Both should be cleared
      expect(elementCache.getElementById(testConversation, 100, 'elem-tab-100')).toBeUndefined();
      expect(elementCache.getElementById(testConversation, 200, 'elem-tab-200')).toBeUndefined();
    });

    test('invalidate by specific tab only clears that tab', () => {
      const element100 = createElement('elem-tab-100');
      const element200 = createElement('elem-tab-200');

      elementCache.storeElements(testConversation, 100, [element100]);
      elementCache.storeElements(testConversation, 200, [element200]);

      // Invalidate only tab 100
      elementCache.invalidate(testConversation, 100);

      // Tab 100 should be cleared
      expect(elementCache.getElementById(testConversation, 100, 'elem-tab-100')).toBeUndefined();

      // Tab 200 should still exist
      expect(elementCache.getElementById(testConversation, 200, 'elem-tab-200')).toBeDefined();
    });

    test('invalidation of one conversation does not affect another', () => {
      const element1 = createElement('conv1-elem');
      const element2 = createElement('conv2-elem');

      elementCache.storeElements(testConversation, 100, [element1]);
      elementCache.storeElements(testConversation2, 100, [element2]);

      elementCache.invalidate(testConversation);

      // Conversation 1 should be cleared
      expect(elementCache.getElementById(testConversation, 100, 'conv1-elem')).toBeUndefined();

      // Conversation 2 should still exist
      expect(elementCache.getElementById(testConversation2, 100, 'conv2-elem')).toBeDefined();
    });
  });

  describe('cross-tab isolation', () => {
    test('cross-tab isolation: same element_id, different tab_id are separate', () => {
      const sharedId = 'shared-button';

      const elementTab1: InteractiveElement = {
        id: sharedId,
        type: 'clickable',
        tagName: 'button',
        selector: '#submit',
        text: 'Submit (Tab 1)',
        bbox: { x: 10, y: 10, width: 100, height: 40 },
        isVisible: true,
        isInViewport: true,
      };

      const elementTab2: InteractiveElement = {
        id: sharedId,
        type: 'clickable',
        tagName: 'button',
        selector: '#submit',
        text: 'Submit (Tab 2)',
        bbox: { x: 20, y: 20, width: 100, height: 40 },
        isVisible: true,
        isInViewport: true,
      };

      elementCache.storeElements(testConversation, 100, [elementTab1]);
      elementCache.storeElements(testConversation, 200, [elementTab2]);

      const fromTab1 = elementCache.getElementById(testConversation, 100, sharedId);
      const fromTab2 = elementCache.getElementById(testConversation, 200, sharedId);

      expect(fromTab1?.text).toBe('Submit (Tab 1)');
      expect(fromTab2?.text).toBe('Submit (Tab 2)');
      expect(fromTab1?.bbox.x).toBe(10);
      expect(fromTab2?.bbox.x).toBe(20);
    });
  });

  describe('edge cases', () => {
    test('getElementById returns undefined for non-existent element', () => {
      const found = elementCache.getElementById(testConversation, 100, 'nonexistent');
      expect(found).toBeUndefined();
    });

    test('getElementById returns undefined for non-existent conversation', () => {
      const element = createElement('test');
      elementCache.storeElements(testConversation, 100, [element]);

      const found = elementCache.getElementById('other-conversation', 100, 'test');
      expect(found).toBeUndefined();
    });

    test('storeElements with empty array does nothing', () => {
      elementCache.storeElements(testConversation, 100, []);
      expect(elementCache.size).toBe(0);
    });

    test('storeElements with empty conversationId does nothing', () => {
      const element = createElement('test');
      elementCache.storeElements('', 100, [element]);
      expect(elementCache.size).toBe(0);
    });

    test('clearAll removes all cached elements', () => {
      elementCache.storeElements(testConversation, 100, [createElement('a')]);
      elementCache.storeElements(testConversation2, 200, [createElement('b')]);

      expect(elementCache.size).toBeGreaterThan(0);

      elementCache.clearAll();

      expect(elementCache.size).toBe(0);
    });
  });

  describe('getElements', () => {
    test('getElements returns all elements for a conversation across tabs', () => {
      const elem1 = createElement('elem1');
      const elem2 = createElement('elem2');

      elementCache.storeElements(testConversation, 100, [elem1]);
      elementCache.storeElements(testConversation, 200, [elem2]);

      const elements = elementCache.getElements(testConversation);

      expect(elements).toHaveLength(2);
      expect(elements?.map((e) => e.id).sort()).toEqual(['elem1', 'elem2']);
    });

    test('getElements returns undefined for empty conversation', () => {
      const elements = elementCache.getElements('nonexistent-conversation');
      expect(elements).toBeUndefined();
    });
  });
});
