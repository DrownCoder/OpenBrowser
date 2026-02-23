/**
 * OpenBrowser Helper Library
 * 
 * A collection of utility functions for common browser automation tasks.
 * These functions are designed to be used with the open_browser tool.
 * 
 * Usage: Copy the function body into your javascript_execute script parameter.
 */

// ============================================================================
// Element Waiting Functions
// ============================================================================

/**
 * Wait for an element to appear in the DOM
 * @param {string} selector - CSS selector to wait for
 * @param {number} timeout - Maximum wait time in milliseconds (default: 10000)
 * @returns {Promise<{found: boolean, text?: string}>}
 */
const waitForElement = (selector, timeout = 10000) => {
    return new Promise((resolve) => {
        const check = () => {
            const el = document.querySelector(selector);
            if (el) {
                resolve({
                    found: true,
                    text: el.textContent?.substring(0, 100),
                    visible: el.offsetParent !== null
                });
            } else {
                setTimeout(check, 100);
            }
        };
        check();
        setTimeout(() => resolve({found: false}), timeout);
    });
};

/**
 * Wait for an element to contain specific text
 * @param {string} selector - CSS selector
 * @param {string} targetText - Text to wait for
 * @param {number} timeout - Maximum wait time in milliseconds
 * @returns {Promise<{found: boolean, text?: string}>}
 */
const waitForText = (selector, targetText, timeout = 10000) => {
    return new Promise((resolve) => {
        const check = () => {
            const el = document.querySelector(selector);
            if (el && el.textContent.includes(targetText)) {
                resolve({found: true, text: el.textContent});
            } else {
                setTimeout(check, 100);
            }
        };
        check();
        setTimeout(() => resolve({found: false}), timeout);
    });
};

/**
 * Wait for an element to be clickable (visible and enabled)
 * @param {string} selector - CSS selector
 * @param {number} timeout - Maximum wait time in milliseconds
 * @returns {Promise<{ready: boolean, element?: object}>}
 */
const waitForClickable = (selector, timeout = 10000) => {
    return new Promise((resolve) => {
        const check = () => {
            const el = document.querySelector(selector);
            if (el && el.offsetParent !== null && !el.disabled) {
                resolve({
                    ready: true,
                    element: {
                        tag: el.tagName,
                        text: el.textContent?.substring(0, 50),
                        enabled: !el.disabled
                    }
                });
            } else {
                setTimeout(check, 100);
            }
        };
        check();
        setTimeout(() => resolve({ready: false}), timeout);
    });
};

// ============================================================================
// Element Interaction Functions
// ============================================================================

/**
 * Highlight an element for debugging (draws red border)
 * @param {string} selector - CSS selector
 * @returns {{highlighted: boolean, error?: string}}
 */
const highlightElement = (selector) => {
    const el = document.querySelector(selector);
    if (!el) {
        return {highlighted: false, error: 'Element not found'};
    }
    
    const originalBorder = el.style.border;
    el.style.border = '3px solid red';
    el.scrollIntoView({behavior: 'smooth', block: 'center'});
    
    // Remove highlight after 2 seconds
    setTimeout(() => {
        el.style.border = originalBorder;
    }, 2000);
    
    return {highlighted: true};
};

/**
 * Click an element with proper event triggering
 * @param {string} selector - CSS selector
 * @returns {{success: boolean, error?: string}}
 */
const clickElement = (selector) => {
    const el = document.querySelector(selector);
    if (!el) {
        return {success: false, error: 'Element not found'};
    }
    
    // Scroll into view
    el.scrollIntoView({behavior: 'smooth', block: 'center'});
    
    // Click
    el.click();
    
    return {success: true, clicked: true};
};

/**
 * Simulate real typing with input/change events
 * @param {string} selector - CSS selector for input element
 * @param {string} text - Text to type
 * @param {{clear: boolean, delay: number}} options - Options
 * @returns {{success: boolean, error?: string, typed?: string}}
 */
const typeText = (selector, text, options = {}) => {
    const input = document.querySelector(selector);
    if (!input) {
        return {success: false, error: 'Element not found'};
    }
    
    const {clear = true, delay = 0} = options;
    
    input.focus();
    
    if (clear) {
        input.value = '';
        input.dispatchEvent(new Event('input', {bubbles: true}));
    }
    
    if (delay > 0) {
        // Simulate real typing with delays
        for (const char of text) {
            input.value += char;
            input.dispatchEvent(new Event('input', {bubbles: true}));
        }
    } else {
        // Fast typing
        input.value = text;
        input.dispatchEvent(new Event('input', {bubbles: true}));
    }
    
    input.dispatchEvent(new Event('change', {bubbles: true}));
    
    return {success: true, typed: text};
};

/**
 * Clear an input field
 * @param {string} selector - CSS selector
 * @returns {{success: boolean, error?: string}}
 */
const clearInput = (selector) => {
    const input = document.querySelector(selector);
    if (!input) {
        return {success: false, error: 'Element not found'};
    }
    
    input.value = '';
    input.dispatchEvent(new Event('input', {bubbles: true}));
    input.dispatchEvent(new Event('change', {bubbles: true}));
    
    return {success: true};
};

// ============================================================================
// Page Exploration Functions
// ============================================================================

/**
 * Explore the page structure and return matching elements
 * @param {string} pattern - CSS selector pattern (default: interactive elements)
 * @param {number} limit - Maximum number of elements to return
 * @returns {Array<{index, tag, text, className, id, href, type}>}
 */
const explorePage = (pattern = 'button, a, input, [role="button"]', limit = 20) => {
    const elements = document.querySelectorAll(pattern);
    return Array.from(elements).slice(0, limit).map((el, i) => ({
        index: i,
        tag: el.tagName,
        text: el.textContent?.trim().substring(0, 50),
        className: el.className?.substring(0, 50),
        id: el.id,
        href: el.href,
        type: el.type,
        role: el.getAttribute('role'),
        ariaLabel: el.getAttribute('aria-label')
    }));
};

/**
 * Get all links on the page
 * @returns {Array<{text, href, title}>}
 */
const getLinks = () => {
    return Array.from(document.links).map(link => ({
        text: link.textContent?.trim().substring(0, 100),
        href: link.href,
        title: link.title
    }));
};

/**
 * Get all buttons on the page
 * @returns {Array<{text, className, id, disabled}>}
 */
const getButtons = () => {
    return Array.from(document.querySelectorAll('button, [role="button"]')).map(btn => ({
        text: btn.textContent?.trim().substring(0, 100),
        className: btn.className?.substring(0, 100),
        id: btn.id,
        disabled: btn.disabled
    }));
};

/**
 * Get all input fields on the page
 * @returns {Array<{type, name, placeholder, value, required}>}
 */
const getInputs = () => {
    return Array.from(document.querySelectorAll('input, textarea')).map(input => ({
        type: input.type,
        name: input.name,
        placeholder: input.placeholder,
        value: input.value,
        required: input.required
    }));
};

// ============================================================================
// Form Helper Functions
// ============================================================================

/**
 * Fill a form with multiple fields
 * @param {Object} fields - Key-value pairs of selector and value
 * @returns {{success: boolean, filled: number, errors: Array}}
 */
const fillForm = (fields) => {
    const errors = [];
    let filled = 0;
    
    for (const [selector, value] of Object.entries(fields)) {
        const input = document.querySelector(selector);
        if (!input) {
            errors.push({selector, error: 'Element not found'});
            continue;
        }
        
        input.focus();
        input.value = value;
        input.dispatchEvent(new Event('input', {bubbles: true}));
        input.dispatchEvent(new Event('change', {bubbles: true}));
        filled++;
    }
    
    return {
        success: errors.length === 0,
        filled,
        errors
    };
};

/**
 * Submit a form
 * @param {string} selector - Form selector
 * @returns {{success: boolean, error?: string}}
 */
const submitForm = (selector) => {
    const form = document.querySelector(selector);
    if (!form) {
        return {success: false, error: 'Form not found'};
    }
    
    form.submit();
    return {success: true};
};

// ============================================================================
// Navigation Functions
// ============================================================================

/**
 * Navigate to a URL
 * @param {string} url - Target URL
 * @returns {{navigated: true, url: string}}
 */
const navigateTo = (url) => {
    window.location.href = url;
    return {navigated: true, url};
};

/**
 * Go back in history
 * @returns {{wentBack: true}}
 */
const goBack = () => {
    window.history.back();
    return {wentBack: true};
};

/**
 * Go forward in history
 * @returns {{wentForward: true}}
 */
const goForward = () => {
    window.history.forward();
    return {wentForward: true};
};

/**
 * Reload the page
 * @returns {{reloaded: true}}
 */
const reloadPage = () => {
    window.location.reload();
    return {reloaded: true};
};

// ============================================================================
// Scrolling Functions
// ============================================================================

/**
 * Scroll to the top of the page
 * @returns {{scrolled: true, position: {x, y}}}
 */
const scrollToTop = () => {
    window.scrollTo({top: 0, left: 0, behavior: 'smooth'});
    return {
        scrolled: true,
        position: {x: window.scrollX, y: window.scrollY}
    };
};

/**
 * Scroll to the bottom of the page
 * @returns {{scrolled: true, position: {x, y}}}
 */
const scrollToBottom = () => {
    window.scrollTo({
        top: document.body.scrollHeight,
        left: 0,
        behavior: 'smooth'
    });
    return {
        scrolled: true,
        position: {x: window.scrollX, y: window.scrollY}
    };
};

/**
 * Scroll by a specified amount
 * @param {number} x - Horizontal scroll amount
 * @param {number} y - Vertical scroll amount
 * @returns {{scrolled: true, position: {x, y}}}
 */
const scrollBy = (x = 0, y = 0) => {
    window.scrollBy({left: x, top: y, behavior: 'smooth'});
    return {
        scrolled: true,
        position: {x: window.scrollX, y: window.scrollY}
    };
};

/**
 * Scroll an element into view
 * @param {string} selector - CSS selector
 * @returns {{scrolled: boolean, error?: string}}
 */
const scrollIntoView = (selector) => {
    const el = document.querySelector(selector);
    if (!el) {
        return {scrolled: false, error: 'Element not found'};
    }
    
    el.scrollIntoView({behavior: 'smooth', block: 'center'});
    return {scrolled: true};
};

// ============================================================================
// Data Extraction Functions
// ============================================================================

/**
 * Extract text content from the page
 * @param {string} selector - CSS selector (optional, defaults to body)
 * @returns {{text: string}}
 */
const extractText = (selector = 'body') => {
    const el = document.querySelector(selector);
    if (!el) {
        return {text: '', error: 'Element not found'};
    }
    
    return {text: el.textContent?.trim()};
};

/**
 * Extract HTML content from the page
 * @param {string} selector - CSS selector (optional, defaults to body)
 * @returns {{html: string}}
 */
const extractHTML = (selector = 'body') => {
    const el = document.querySelector(selector);
    if (!el) {
        return {html: '', error: 'Element not found'};
    }
    
    return {html: el.innerHTML};
};

/**
 * Extract attributes from elements
 * @param {string} selector - CSS selector
 * @param {Array<string>} attributes - List of attribute names to extract
 * @returns {Array<Object>}
 */
const extractAttributes = (selector, attributes = ['id', 'class', 'href', 'src']) => {
    const elements = document.querySelectorAll(selector);
    return Array.from(elements).map(el => {
        const result = {};
        for (const attr of attributes) {
            result[attr] = el.getAttribute(attr);
        }
        return result;
    });
};

/**
 * Take a screenshot (returns current viewport info)
 * Note: Actual screenshot is handled by the open_browser tool
 * @returns {{width: number, height: number, url: string, title: string}}
 */
const getViewportInfo = () => {
    return {
        width: window.innerWidth,
        height: window.innerHeight,
        url: window.location.href,
        title: document.title,
        scrollX: window.scrollX,
        scrollY: window.scrollY
    };
};

// ============================================================================
// Utility Functions
// ============================================================================

/**
 * Sleep for a specified duration
 * @param {number} ms - Duration in milliseconds
 * @returns {Promise<{slept: true, duration: number}>}
 */
const sleep = (ms) => {
    return new Promise(resolve => {
        setTimeout(() => resolve({slept: true, duration: ms}), ms);
    });
};

/**
 * Get page information
 * @returns {{url: string, title: string, readyState: string}}
 */
const getPageInfo = () => {
    return {
        url: window.location.href,
        title: document.title,
        readyState: document.readyState
    };
};

/**
 * Check if page is fully loaded
 * @returns {{loaded: boolean, readyState: string}}
 */
const isPageLoaded = () => {
    return {
        loaded: document.readyState === 'complete',
        readyState: document.readyState
    };
};

// Export all functions for use in open_browser tool
// Note: When using with open_browser, copy the function body directly into your script
export {
    waitForElement,
    waitForText,
    waitForClickable,
    highlightElement,
    clickElement,
    typeText,
    clearInput,
    explorePage,
    getLinks,
    getButtons,
    getInputs,
    fillForm,
    submitForm,
    navigateTo,
    goBack,
    goForward,
    reloadPage,
    scrollToTop,
    scrollToBottom,
    scrollBy,
    scrollIntoView,
    extractText,
    extractHTML,
    extractAttributes,
    getViewportInfo,
    sleep,
    getPageInfo,
    isPageLoaded
};
