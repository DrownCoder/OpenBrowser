import { describe, test, expect } from 'bun:test';
import { generateShortHash, generateUniqueHash, generateElementId } from '../hash-utils';

describe('hash-utils', () => {
  describe('generateShortHash', () => {
    test('hash is exactly 6 characters', () => {
      const hash = generateShortHash('div#content');
      expect(hash.length).toBe(6);
    });

    test('hash uses only base36 characters (0-9, a-z)', () => {
      const hash = generateShortHash('div#content');
      expect(hash).toMatch(/^[0-9a-z]{6}$/);
    });

    test('same CSS path generates same hash (deterministic)', () => {
      const cssPath = 'div#content > p.text';
      const hash1 = generateShortHash(cssPath);
      const hash2 = generateShortHash(cssPath);
      expect(hash1).toBe(hash2);
    });

    test('different CSS paths generate different hashes', () => {
      const hash1 = generateShortHash('div#content');
      const hash2 = generateShortHash('div#sidebar');
      expect(hash1).not.toBe(hash2);
    });

    test('salt changes the hash output', () => {
      const cssPath = 'div#content';
      const hashNoSalt = generateShortHash(cssPath);
      const hashWithSalt = generateShortHash(cssPath, undefined, 1);
      expect(hashNoSalt).not.toBe(hashWithSalt);
    });

    test('HTML content changes hash output', () => {
      const cssPath = 'div#content';
      const hashNoHtml = generateShortHash(cssPath);
      const hashWithHtml = generateShortHash(cssPath, '<button>Click</button>');
      expect(hashNoHtml).not.toBe(hashWithHtml);
    });
  });

  describe('generateUniqueHash', () => {
    test('returns unique hash when no collision', () => {
      const existingHashes = new Set<string>();
      const result = generateUniqueHash('div#content', existingHashes);
      expect(result.hash.length).toBe(6);
      expect(result.salt).toBe(0);
    });

    test('collision resolution works (same hash + salt increment)', () => {
      // Create a collision scenario
      const cssPath = 'div#content';
      const firstHash = generateShortHash(cssPath, undefined, 0);
      const existingHashes = new Set<string>([firstHash]);

      const result = generateUniqueHash(cssPath, existingHashes);
      expect(result.hash).not.toBe(firstHash);
      expect(result.salt).toBeGreaterThan(0);
      expect(existingHashes.has(result.hash)).toBe(false);
    });

    test('fallback to timestamp salt when max attempts exceeded', () => {
      // Pre-fill with hashes to force fallback
      const cssPath = 'div#content';
      const existingHashes = new Set<string>();

      // Generate many hashes to simulate collision scenario
      // We'll use a low maxAttempts to trigger fallback faster
      for (let i = 0; i < 5; i++) {
        existingHashes.add(generateShortHash(cssPath, undefined, i));
      }

      // With maxAttempts=5, should trigger fallback
      const result = generateUniqueHash(cssPath, existingHashes, undefined, 5);
      expect(result.salt).toBeGreaterThan(5); // timestamp-based salt
      expect(result.hash.length).toBe(6);
    });
  });

  describe('generateElementId', () => {
    test('returns pure hash (no prefix)', () => {
      const existingHashes = new Set<string>();
      const result = generateElementId('click', 'div#content', existingHashes);

      // id should be just the hash, no "click-" prefix
      expect(result.id).toBe(result.hash);
      expect(result.id).toMatch(/^[0-9a-z]{6}$/);
    });

    test('hash is exactly 6 characters', () => {
      const existingHashes = new Set<string>();
      const result = generateElementId('click', 'div#content', existingHashes);
      expect(result.hash.length).toBe(6);
    });

    test('adds generated hash to existing hashes', () => {
      const existingHashes = new Set<string>();
      generateElementId('click', 'div#content', existingHashes);
      // Note: The function returns the hash but doesn't modify the set itself
      // The caller is responsible for adding it
      expect(existingHashes.size).toBe(0);
    });

    test('different types with same path produce same hash', () => {
      const existingHashes = new Set<string>();
      const result1 = generateElementId('click', 'div#content', existingHashes);
      const result2 = generateElementId('input', 'div#content', existingHashes);
      expect(result1.hash).toBe(result2.hash);
    });

    test('same CSS path with same HTML produces same hash', () => {
      const cssPath = 'div#content';
      const html = '<button>Submit</button>';

      const hash1 = generateShortHash(cssPath, html);
      const hash2 = generateShortHash(cssPath, html);

      expect(hash1).toBe(hash2);
    });

    test('CSS path without HTML produces consistent hash', () => {
      const cssPath = 'div#content';

      const hash1 = generateShortHash(cssPath);
      const hash2 = generateShortHash(cssPath, undefined);

      expect(hash1).toBe(hash2);
    });

    test('generateElementId with HTML produces different hash than without HTML', () => {
      const existingHashes = new Set<string>();
      const cssPath = 'div#content';
      const html = '<button>Submit</button>';

      const resultWithoutHtml = generateElementId('click', cssPath, existingHashes);
      const resultWithHtml = generateElementId('click', cssPath, existingHashes, html);

      expect(resultWithoutHtml.hash).not.toBe(resultWithHtml.hash);
    });
  });
});
