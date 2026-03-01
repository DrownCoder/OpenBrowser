/**
 * Visual Highlight Drawing Module
 * Draws bounding boxes on screenshots to highlight interactive elements.
 * Uses OffscreenCanvas for Service Worker compatibility (Manifest V3).
 */

import type { InteractiveElement, ElementType, HighlightOptions } from '../types';

/**
 * Color mapping for different element types
 */
const COLORS: Record<ElementType, string> = {
  clickable: '#0066FF',
  scrollable: '#00CC66',
  inputable: '#FF9900',
  hoverable: '#9966FF',
};

/**
 * Maximum number of elements to draw at once to prevent performance issues
 */
const MAX_ELEMENTS = 50;

/**
 /**
 * Base sizes in CSS pixels (will be multiplied by scale for device pixels)
 */
const BASE_FONT_SIZE = 16; // Font size at scale=1
const BASE_LABEL_PADDING = 5; // Label padding at scale=1
const BASE_BOX_PADDING = 3; // Box padding at scale=1
const BASE_LINE_WIDTH = 2.5; // Box border width at scale=1

/**
 * Draw highlights (bounding boxes with labels) on a screenshot
 * 
 * @param screenshotDataUrl - Base64 data URL of the screenshot
 * @param elements - Array of interactive elements to highlight
 * @param options - Highlight options (limit, offset, elementTypes filter, scale)
 * @returns Promise resolving to base64 PNG data URL with highlights drawn
 */
export async function drawHighlights(
  screenshotDataUrl: string,
  elements: InteractiveElement[],
  options?: HighlightOptions & { scale?: number; viewportWidth?: number; viewportHeight?: number },
): Promise<string> {
  console.log(`🎨 [VisualHighlight] Drawing highlights for ${elements.length} elements...`);
  console.log(`🎨 [VisualHighlight] Drawing highlights for ${elements.length} elements...`);

  // Check OffscreenCanvas availability
  if (typeof OffscreenCanvas === 'undefined') {
    throw new Error(
      '[VisualHighlight] OffscreenCanvas is not available. ' +
        'Visual highlighting requires OffscreenCanvas support.',
    );
  }

  // Check createImageBitmap availability
  if (typeof createImageBitmap === 'undefined') {
    throw new Error(
      '[VisualHighlight] createImageBitmap is not available. ' +
        'Visual highlighting requires createImageBitmap support.',
    );
  }

  try {
    // ========================================
    // STEP 1: Validate screenshot data URL format
    // ========================================
    if (!screenshotDataUrl || typeof screenshotDataUrl !== 'string') {
      throw new Error(
        '[VisualHighlight] Invalid screenshot data: expected a data URL string, got ' +
          (screenshotDataUrl === null ? 'null' : screenshotDataUrl === undefined ? 'undefined' : typeof screenshotDataUrl),
      );
    }

    if (!screenshotDataUrl.startsWith('data:')) {
      throw new Error(
        '[VisualHighlight] Invalid screenshot data URL: must start with "data:" prefix. ' +
          `Got: "${screenshotDataUrl.substring(0, 50)}..."`,
      );
    }

    if (!screenshotDataUrl.includes(',')) {
      throw new Error(
        '[VisualHighlight] Invalid screenshot data URL: must contain comma separator between header and data. ' +
          `Got: "${screenshotDataUrl.substring(0, 100)}..."`,
      );
    }

    // ========================================
    // STEP 2: Parse data URL into components
    // ========================================
    const dataUrlParts = screenshotDataUrl.split(',');
    const headerPart = dataUrlParts[0];
    const colonIndex = headerPart.indexOf(':');
    const semicolonIndex = headerPart.indexOf(';');

    if (colonIndex === -1 || semicolonIndex === -1) {
      throw new Error(
        '[VisualHighlight] Invalid screenshot data URL header: expected format "data:image/format;base64". ' +
          `Got: "${headerPart}"`,
      );
    }

    const mimeType = headerPart.substring(colonIndex + 1, semicolonIndex);
    const base64Data = dataUrlParts[1];

    if (!base64Data || base64Data.length === 0) {
      throw new Error('[VisualHighlight] Screenshot data URL contains no image data after header');
    }

    // ========================================
    // STEP 3: Decode base64 to binary
    // ========================================
    const binaryString = atob(base64Data);
    const bytes = new Uint8Array(binaryString.length);
    for (let i = 0; i < binaryString.length; i++) {
      bytes[i] = binaryString.charCodeAt(i);
    }

    // ========================================
    // STEP 4: Create Blob and ImageBitmap
    // ========================================
    const blob = new Blob([bytes], { type: mimeType });
    const imageBitmap = await createImageBitmap(blob);

    // Extract options before using them
    const viewportWidth = options?.viewportWidth ?? 0;
    const viewportHeight = options?.viewportHeight ?? 0;
    
    console.log(`🖼️ [VisualHighlight] Screenshot dimensions: ${imageBitmap.width}x${imageBitmap.height}`);
    
    // Calculate actual scale from screenshot dimensions (more reliable than trusting DPR)
    const actualScaleX = viewportWidth > 0 ? imageBitmap.width / viewportWidth : 1;
    const actualScaleY = viewportHeight > 0 ? imageBitmap.height / viewportHeight : 1;
    const actualScale = (actualScaleX + actualScaleY) / 2; // Average in case of rounding
    
    console.log(`📐 [VisualHighlight] Calculated scale: ${actualScale.toFixed(3)} (from ${viewportWidth}x${viewportHeight} → ${imageBitmap.width}x${imageBitmap.height})`);
    
    // Prefer calculated scale if it differs significantly from provided scale
    const providedScale = options?.scale ?? 1;
    const scale = Math.abs(actualScale - providedScale) > 0.1 ? actualScale : providedScale;
    console.log(`📐 [VisualHighlight] Using scale: ${scale.toFixed(3)} (provided: ${providedScale}, calculated: ${actualScale})`);

    // Create OffscreenCanvas with same dimensions as screenshot
    console.log(`🖼️ [VisualHighlight] Screenshot dimensions: ${imageBitmap.width}x${imageBitmap.height}`);

    // Create OffscreenCanvas with same dimensions as screenshot
    const canvas = new OffscreenCanvas(imageBitmap.width, imageBitmap.height);
    const ctx = canvas.getContext('2d');

    if (!ctx) {
      throw new Error('[VisualHighlight] Failed to get 2d context from OffscreenCanvas');
    }

    // Draw original screenshot onto canvas
    ctx.drawImage(imageBitmap, 0, 0);

    // Close the bitmap to free memory
    imageBitmap.close();

    // Filter by element types if specified (caller already paginated)
    // Note: DO NOT re-paginate here - the caller has already done pagination
    if (options?.elementTypes && options.elementTypes.length > 0) {
      const typeFiltered = elements.filter((el) => options.elementTypes!.includes(el.type));
      console.log(
        `🎨 [VisualHighlight] Drawing ${typeFiltered.length} elements (type filter: ${options.elementTypes.join(',')}, scale=${scale})`,
      );
    } else {
      console.log(
        `🎨 [VisualHighlight] Drawing ${elements.length} elements (no type filter, scale=${scale})`,
      );
    }

    // Draw each element's bounding box and label
    // Scale coordinates from CSS pixels to device pixels
    for (const element of (options?.elementTypes ? typeFiltered : elements)) {
      drawBoundingBox(ctx, element, scale);
    }

    const resultBlob = await canvas.convertToBlob({ type: 'image/png' });

    // Convert blob to data URL
    return new Promise((resolve, reject) => {
      const reader = new FileReader();
      reader.onloadend = () => {
        const resultDataUrl = reader.result as string;
        console.log(`✅ [VisualHighlight] Highlights drawn successfully`);
        resolve(resultDataUrl);
      };
      reader.onerror = () => reject(new Error('[VisualHighlight] Failed to convert result to data URL'));
      reader.readAsDataURL(resultBlob);
    });
  } catch (error) {
    const errorMsg = `[VisualHighlight] Error drawing highlights: ${error instanceof Error ? error.message : error}`;
    console.error(`❌ ${errorMsg}`);
    throw new Error(errorMsg);
  }
}

/**
 * Draw a bounding box with label for an interactive element
 * 
 * @param ctx - Canvas 2D rendering context
 * @param element - Interactive element to draw
 * @param scale - Scale factor to convert CSS pixels to device pixels (default: 1)
 */
function drawBoundingBox(ctx: OffscreenCanvasRenderingContext2D, element: InteractiveElement, scale: number = 1): void {
  const color = COLORS[element.type] || '#CCCCCC';
  const { x, y, width, height } = element.bbox;

  // Calculate device-pixel values from base CSS sizes
  const boxPadding = Math.round(BASE_BOX_PADDING * scale);
  const lineWidth = BASE_LINE_WIDTH * scale;

  // Apply scale to convert CSS pixels to device pixels, then apply padding
  // x, y are viewport-relative from getBoundingClientRect()
  const boxX = Math.round(x * scale) - boxPadding;
  const boxY = Math.round(y * scale) - boxPadding;
  const boxWidth = Math.round(width * scale) + boxPadding * 2;
  const boxHeight = Math.round(height * scale) + boxPadding * 2;

  console.log(`[VisualHighlight] Drawing bbox for ${element.id}: CSS(${x}, ${y}, ${width}, ${height}) → Device(${boxX}, ${boxY}, ${boxWidth}, ${boxHeight}) scale=${scale}`);

  // Draw bounding box
  ctx.strokeStyle = color;
  ctx.lineWidth = lineWidth;
  ctx.strokeRect(boxX, boxY, boxWidth, boxHeight);

  // Draw element ID label
  drawLabel(ctx, element.id, boxX, boxY, color, scale);
}

/**
 * Draw a label with background at the specified position
 * 
 * @param ctx - Canvas 2D rendering context
 * @param text - Label text (element ID)
 * @param x - X position (top-left of bounding box)
 * @param y - Y position (top-left of bounding box)
 * @param bgColor - Background color for the label
 * @param scale - Scale factor for device pixels
 */
function drawLabel(
  ctx: OffscreenCanvasRenderingContext2D,
  text: string,
  x: number,
  y: number,
  bgColor: string,
  scale: number,
): void {
  // Calculate device-pixel values from base CSS sizes
  const fontSize = Math.round(BASE_FONT_SIZE * scale);
  const labelPadding = Math.round(BASE_LABEL_PADDING * scale);

  // Set font before measuring text
  ctx.font = `bold ${fontSize}px Arial`;

  // Measure text width
  const metrics = ctx.measureText(text);
  const textWidth = metrics.width;
  const textHeight = fontSize; // Height matches font size

  // Calculate label dimensions
  const labelWidth = textWidth + labelPadding * 2;
  const labelHeight = textHeight + labelPadding * 2;

  // Position label above the box (or inside if at top edge)
  let labelX = x;
  let labelY = y - labelHeight;

  // If label would go above canvas, position it inside the box
  if (labelY < 0) {
    labelY = y;
  }

  // Draw label background
  ctx.fillStyle = bgColor;
  ctx.fillRect(labelX, labelY, labelWidth, labelHeight);

  // Draw label text (white for contrast)
  ctx.fillStyle = '#FFFFFF';
  ctx.textBaseline = 'top';
  ctx.fillText(text, labelX + labelPadding, labelY + labelPadding);
}

/**
 * Get the color for a specific element type
 * 
 * @param type - Element type
 * @returns Hex color string
 */
export function getElementColor(type: ElementType): string {
  return COLORS[type] || '#CCCCCC';
}
