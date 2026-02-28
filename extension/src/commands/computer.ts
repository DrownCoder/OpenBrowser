/**
 * Screenshot metadata caching utilities
 */
import type { ScreenshotMetadata } from '../types';

// Cache for screenshot metadata per tab
const screenshotCache = new Map<number, ScreenshotMetadata>();

/**
 * Cache screenshot metadata for a tab
 */
export function cacheScreenshotMetadata(
  tabId: number,
  imageWidth: number,
  imageHeight: number,
  viewportWidth: number,
  viewportHeight: number,
): void {
  const metadata: ScreenshotMetadata = {
    imageWidth,
    imageHeight,
    viewportWidth,
    viewportHeight,
    timestamp: Date.now(),
    tabId,
  };
  screenshotCache.set(tabId, metadata);
  console.log(
    `📸 [Computer] Screenshot metadata cached for tab ${tabId}: ${imageWidth}x${imageHeight} image, ${viewportWidth}x${viewportHeight} viewport`,
  );
}

/**
 * Clear screenshot cache for a tab
 */
export function clearScreenshotCache(tabId?: number): void {
  if (tabId !== undefined) {
    screenshotCache.delete(tabId);
  } else {
    screenshotCache.clear();
  }
}

/**
 * Get cached screenshot metadata for a tab
 */
export function getScreenshotMetadata(
  tabId: number,
): ScreenshotMetadata | undefined {
  return screenshotCache.get(tabId);
}

export const computer = {
  cacheScreenshotMetadata,
  clearScreenshotCache,
  getScreenshotMetadata,
};
