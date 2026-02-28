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
 * Padding around element bounding box (in pixels)
 */
const BOX_PADDING = 2;

/**
 * Font settings for labels
 */
const LABEL_FONT = 'bold 12px Arial';
const LABEL_PADDING = 4;

/**
 * Draw highlights (bounding boxes with labels) on a screenshot
 * 
 * @param screenshotDataUrl - Base64 data URL of the screenshot
 * @param elements - Array of interactive elements to highlight
 * @param options - Highlight options (limit, offset, elementTypes filter)
 * @returns Promise resolving to base64 PNG data URL with highlights drawn
 */
export async function drawHighlights(
  screenshotDataUrl: string,
  elements: InteractiveElement[],
  options?: HighlightOptions,
): Promise<string> {
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
    // Convert data URL to Blob and create ImageBitmap
    const response = await fetch(screenshotDataUrl);
    const blob = await response.blob();
    const imageBitmap = await createImageBitmap(blob);

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

    // Filter and paginate elements
    let filteredElements = elements;

    // Filter by element types if specified
    if (options?.elementTypes && options.elementTypes.length > 0) {
      filteredElements = elements.filter((el) => options.elementTypes!.includes(el.type));
    }

    // Apply pagination
    const offset = options?.offset ?? 0;
    const limit = Math.min(options?.limit ?? MAX_ELEMENTS, MAX_ELEMENTS);
    const paginatedElements = filteredElements.slice(offset, offset + limit);

    console.log(
      `🎨 [VisualHighlight] Drawing ${paginatedElements.length} elements (filtered from ${elements.length}, offset=${offset}, limit=${limit})`,
    );

    // Draw each element's bounding box and label
    for (const element of paginatedElements) {
      drawBoundingBox(ctx, element);
    }

    // Convert canvas to PNG blob
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
 */
function drawBoundingBox(ctx: OffscreenCanvasRenderingContext2D, element: InteractiveElement): void {
  const color = COLORS[element.type] || '#CCCCCC';
  const { x, y, width, height } = element.bbox;

  // Apply padding
  const boxX = x - BOX_PADDING;
  const boxY = y - BOX_PADDING;
  const boxWidth = width + BOX_PADDING * 2;
  const boxHeight = height + BOX_PADDING * 2;

  // Draw bounding box
  ctx.strokeStyle = color;
  ctx.lineWidth = 2;
  ctx.strokeRect(boxX, boxY, boxWidth, boxHeight);

  // Draw element ID label
  drawLabel(ctx, element.id, boxX, boxY, color);
}

/**
 * Draw a label with background at the specified position
 * 
 * @param ctx - Canvas 2D rendering context
 * @param text - Label text (element ID)
 * @param x - X position (top-left of bounding box)
 * @param y - Y position (top-left of bounding box)
 * @param bgColor - Background color for the label
 */
function drawLabel(
  ctx: OffscreenCanvasRenderingContext2D,
  text: string,
  x: number,
  y: number,
  bgColor: string,
): void {
  // Set font before measuring text
  ctx.font = LABEL_FONT;

  // Measure text width
  const metrics = ctx.measureText(text);
  const textWidth = metrics.width;
  const textHeight = 12; // Approximate height for 12px font

  // Calculate label dimensions
  const labelWidth = textWidth + LABEL_PADDING * 2;
  const labelHeight = textHeight + LABEL_PADDING * 2;

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
  ctx.fillText(text, labelX + LABEL_PADDING, labelY + LABEL_PADDING);
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
