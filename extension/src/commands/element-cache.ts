/**
 * Element Cache Manager
 * Stores detected interactive elements per conversation with auto-invalidation
 */

import type { InteractiveElement } from '../types';

interface CacheEntry {
  elements: InteractiveElement[];
  timestamp: number;
}

const CACHE_TTL_MS = 30000; // 30 seconds
const MAX_ELEMENTS_PER_SESSION = 100;

class ElementCacheImpl {
  private cache = new Map<string, CacheEntry>();

  /**
   * Store elements for a conversation
   * Limits to MAX_ELEMENTS_PER_SESSION
   */
  storeElements(conversationId: string, elements: InteractiveElement[]): void {
    if (!conversationId || !elements.length) {
      return;
    }

    // Cleanup expired entries first
    this.cleanup(conversationId);

    // Limit elements to max count
    const limitedElements = elements.slice(0, MAX_ELEMENTS_PER_SESSION);

    this.cache.set(conversationId, {
      elements: limitedElements,
      timestamp: Date.now(),
    });

    console.log(
      `📁 [ElementCache] Stored ${limitedElements.length} elements for conversation ${conversationId}`
    );
  }

  /**
   * Get all elements for a conversation if not expired
   */
  getElements(conversationId: string): InteractiveElement[] | undefined {
    if (!conversationId) {
      return undefined;
    }

    const entry = this.cache.get(conversationId);
    if (!entry) {
      return undefined;
    }

    // Check if expired
    if (Date.now() - entry.timestamp > CACHE_TTL_MS) {
      this.cache.delete(conversationId);
      console.log(`⏰ [ElementCache] Cache expired for conversation ${conversationId}`);
      return undefined;
    }

    return entry.elements;
  }

  /**
   * Find a specific element by ID within a conversation's cache
   */
  getElementById(conversationId: string, elementId: string): InteractiveElement | undefined {
    const elements = this.getElements(conversationId);
    if (!elements) {
      return undefined;
    }

    return elements.find((el) => el.id === elementId);
  }

  /**
   * Invalidate (clear) cache for a specific conversation
   */
  invalidate(conversationId: string): void {
    if (this.cache.has(conversationId)) {
      this.cache.delete(conversationId);
      console.log(`🗑️ [ElementCache] Invalidated cache for conversation ${conversationId}`);
    }
  }

  /**
   * Remove expired entries for a conversation (or all if no conversationId)
   */
  private cleanup(conversationId?: string): void {
    const now = Date.now();

    if (conversationId) {
      // Check specific conversation
      const entry = this.cache.get(conversationId);
      if (entry && now - entry.timestamp > CACHE_TTL_MS) {
        this.cache.delete(conversationId);
        console.log(`🧹 [ElementCache] Cleaned up expired cache for ${conversationId}`);
      }
    } else {
      // Check all conversations
      for (const [id, entry] of this.cache.entries()) {
        if (now - entry.timestamp > CACHE_TTL_MS) {
          this.cache.delete(id);
          console.log(`🧹 [ElementCache] Cleaned up expired cache for ${id}`);
        }
      }
    }
  }

  /**
   * Clear all cached elements
   */
  clearAll(): void {
    this.cache.clear();
    console.log('🧹 [ElementCache] Cleared all caches');
  }

  /**
   * Get cache size (number of conversations with cached elements)
   */
  get size(): number {
    return this.cache.size;
  }
}

export const elementCache = new ElementCacheImpl();
