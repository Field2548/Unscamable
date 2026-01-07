// ============================================================================
// CHAT SELECTORS FOR DIFFERENT PLATFORMS
// ============================================================================

// Define main message container selectors for each platform
const MESSAGE_CONTAINER_SELECTORS = {
  messenger: [
    '[role="main"]', // Main conversation area in Messenger
    '[data-qa="conversation"]', // Conversation container
    '[class*="conversation"]', // Fallback
  ],
  whatsapp: [
    '[data-testid="conversation-panel-messages"]',
    '[class*="message"]',
  ],
  gmail: [
    '[role="main"]',
  ],
  telegram: [
    '[class*="messages-container"]',
  ],
};

const PLATFORM_SELECTORS = {
  // Facebook Messenger / Messenger.com
  messenger: [
    '[data-testid="messageContent"]',
    '[role="article"]', // Message bubbles
    'span[dir="auto"]', // Text content in messages
    '.msg',
    '[data-qa="message_body"]',
  ],
  
  // WhatsApp Web
  whatsapp: [
    '[data-testid="msg-text"]',
    '.copyable-text span',
    '[class*="message"] span',
  ],
  
  // Gmail
  gmail: [
    '[data-message-id] [role="presentation"] .gmail_quote',
    'div[role="main"] .gs',
    'div[data-message-id] div[role="article"]',
  ],
  
  // Telegram Web
  telegram: [
    '.message-text',
    '[class*="text-content"]',
  ],
  
  // Generic chat/messaging (fallback)
  generic: [
    '[data-testid="message"]',
    '[data-testid="messageContent"]',
    '[role="textbox"]',
    '.message-text',
    '.chat-message',
    '.message',
    '.msg',
    '.bubble',
    '.conversation',
    '[class*="message"]',
    '[class*="chat"]',
  ]
};

// Selectors to identify user's own messages (to be excluded)
const USER_MESSAGE_SELECTORS = {
  messenger: [
    // Facebook Messenger specific selectors
    '[data-testid="outgoing_message"]',
    '[data-testid="incoming_message"]', // Will be inverted - we want to exclude outgoing
    '[class*="x1n2onr6"]', // Blue bubble styling (user messages on right)
  ],
  whatsapp: [
    '.message-out',
    '[class*="message-out"]',
  ],
  telegram: [
    '.message.is-out',
    '[class*="is-out"]',
  ],
  gmail: [
    '[role="listitem"][class*="bkL"]',
  ],
  generic: [
    '[class*="outgoing"]',
    '[class*="sent"]',
  ]
};

const MESSAGE_OBSERVERS = new Map();
let seenMessages = new Set();
let seenMessageHashes = new Set(); // Track analyzed message hashes
let newMessagesToAnalyze = []; // Queue of new messages waiting to be analyzed

// ============================================================================
// DETECT CURRENT PLATFORM
// ============================================================================

function detectPlatform() {
  const hostname = window.location.hostname;
  
  if (hostname.includes('messenger.com') || hostname.includes('facebook.com')) {
    return 'messenger';
  } else if (hostname.includes('web.whatsapp.com')) {
    return 'whatsapp';
  } else if (hostname.includes('gmail.com') || hostname.includes('google.com/mail')) {
    return 'gmail';
  } else if (hostname.includes('web.telegram.org')) {
    return 'telegram';
  }
  return 'generic'; // Default to generic for all other websites
}

function isSupportedChatPlatform() {
  const platform = detectPlatform();
  return platform !== 'generic'; // True only if it's a known chat platform
}

// ============================================================================
// MESSAGE EXTRACTION & DEDUPLICATION
// ============================================================================

function isUserMessage(element, platform) {
  if (!element) return false;
  
  // Platform-specific detection for Facebook Messenger
  if (platform === 'messenger') {
    // Get the message container/bubble
    const bubble = element.closest('[role="article"]') || element;
    
    // Check the computed width and position to determine if it's on the RIGHT (user) or LEFT (other)
    const styles = window.getComputedStyle(bubble);
    
    // Method 1: Check if element is near the RIGHT edge
    // Get the bounding rectangle to check actual position
    const rect = bubble.getBoundingClientRect();
    const mainContainer = document.querySelector('[role="main"]') || document.body;
    const containerRect = mainContainer.getBoundingClientRect();
    
    // Calculate position from right edge
    const distanceFromRight = containerRect.right - rect.right;
    const distanceFromLeft = rect.left - containerRect.left;
    
    // Debug info
    // console.log('[DEBUG] Distance - Left:', distanceFromLeft, 'Right:', distanceFromRight);
    
    // If closer to RIGHT edge (smaller distance from right), it's user's message
    // Allow some threshold for rounding
    if (distanceFromRight < 100 && distanceFromLeft > 100) {
      return true; // This is user's message (right side)
    }
    
    // Method 2: Check for large left margin (user messages pushed to right)
    const marginLeft = styles.marginLeft;
    try {
      const leftMargin = parseFloat(marginLeft || '0');
      if (leftMargin > 50) {
        return true; // User's message (right side, large left margin)
      }
    } catch (e) {
      // Continue
    }
    
    // Method 3: Check for background color or styling specific to user messages
    const bgColor = styles.backgroundColor;
    // User messages on Messenger are typically blue/light color, other messages are light gray
    // Check if background suggests this is user's message
    if (bgColor && (bgColor.includes('rgb(0, 132, 255)') || bgColor.includes('rgb(31, 121, 226)'))) {
      return true; // Blue background typical for user messages
    }
    
    // Method 4: More aggressive position check
    // User messages are typically in right 40% of container area
    const containerWidth = containerRect.width;
    const messageCenter = rect.left - containerRect.left + (rect.width / 2);
    
    // If message is in right 35% of container, likely user's message
    if (messageCenter > containerWidth * 0.65) {
      console.log('[Unscamable] Filtering out user message at position:', messageCenter, 'of', containerWidth);
      return true;
    }
    
    // If we get here, it's likely a message from someone else (left side)
    return false;
  }
  
  // For other platforms, try generic selectors
  const selectors = USER_MESSAGE_SELECTORS[platform] || USER_MESSAGE_SELECTORS.generic;
  
  for (const selector of selectors) {
    try {
      if (element.matches?.(selector)) {
        return true;
      }
      let parent = element.parentElement;
      let depth = 0;
      while (parent && depth < 5) {
        if (parent.matches?.(selector)) {
          return true;
        }
        parent = parent.parentElement;
        depth++;
      }
    } catch (e) {
      // Selector error, skip
    }
  }
  
  return false;
}

function extractMessageText(element) {
  if (!element) return '';
  
  // Clone the element to avoid modifying the DOM
  const clone = element.cloneNode(true);
  
  // Remove script and style tags
  clone.querySelectorAll('script, style').forEach(el => el.remove());
  
  // Get text content
  const text = clone.innerText?.trim() || clone.textContent?.trim() || '';
  
  return text;
}

function isElementInViewport(element) {
  const rect = element.getBoundingClientRect();
  return (
    rect.top < window.innerHeight &&
    rect.bottom > 0 &&
    rect.left < window.innerWidth &&
    rect.right > 0
  );
}

function getMessageHash(text) {
  // Simple hash to detect duplicate messages
  if (!text) return '';
  const trimmed = text.trim().substring(0, 100);
  return trimmed;
}

/**
 * CORE FUNCTION: Scrape all chat text from the page
 * Returns combined text of all visible messages from the main message box only
 */
function scrapeChatText(platform = null) {
  if (!platform) {
    platform = detectPlatform();
  }

  const messages = [];
  
  // First, find the main message container (not the sidebar)
  let mainContainer = null;
  const containerSelectors = MESSAGE_CONTAINER_SELECTORS[platform] || MESSAGE_CONTAINER_SELECTORS.generic || [];
  
  for (const containerSelector of containerSelectors) {
    try {
      mainContainer = document.querySelector(containerSelector);
      if (mainContainer) {
        console.log('[Unscamable] Found main message container');
        break;
      }
    } catch (e) {
      // Continue
    }
  }
  
  // If no container found, use the whole document but be more restrictive
  if (!mainContainer) {
    console.log('[Unscamable] Main container not found, using document.body');
    mainContainer = document.body;
  }

  const selectors = PLATFORM_SELECTORS[platform] || PLATFORM_SELECTORS.generic;

  for (const selector of selectors) {
    try {
      // Query only within the main container
      const elements = mainContainer.querySelectorAll(selector);
      
      for (const el of elements) {
        // Only include visible AND in-viewport messages
        if (el && el.offsetHeight > 0 && isElementInViewport(el)) {
          // Skip user's own messages (right side)
          if (isUserMessage(el, platform)) {
            continue;
          }
          
          const text = extractMessageText(el);
          
          if (text.length >= 3) { // include short Thai words like "ศาล"
            messages.push(text);
          }
        }
      }
      
      if (messages.length > 0) break; // found messages, stop searching
    } catch (e) {
      console.error('[Unscamable] Selector error:', e);
    }
  }

  const combinedText = messages.join('\n\n').trim();

  return combinedText || 'No content detected.';
}

// ============================================================================
// MESSAGE COLLECTION (NEW & UNSEEN ONLY)
// ============================================================================

// ============================================================================
// CONTINUOUS MONITORING WITH MUTATIONOBSERVER
// ============================================================================

function extractNewMessages(nodes, platform) {
  const selectors = PLATFORM_SELECTORS[platform] || PLATFORM_SELECTORS.generic;
  const newMessages = [];
  
  nodes.forEach((node) => {
    // Only process element nodes
    if (node.nodeType !== 1) return;
    
    // Check if the node itself is a message
    for (const selector of selectors) {
      try {
        if (node.matches?.(selector)) {
          // Skip if this is the user's own message
          if (isUserMessage(node, platform)) {
            console.log('[Unscamable] Skipping user\'s own message');
            return;
          }
          
          const text = extractMessageText(node);
          if (text.length >= 3) {
            const hash = getMessageHash(text);
            if (!seenMessageHashes.has(hash)) {
              newMessages.push({ text, hash });
              seenMessageHashes.add(hash);
            }
          }
          return; // Found message in this node
        }
      } catch (e) {
        // Selector error, skip
      }
    }
    
    // Check if the node's children contain messages
    try {
      const selectorString = selectors.join(',');
      const messageElements = node.querySelectorAll(selectorString) || [];
      
      messageElements.forEach((el) => {
        // Skip if this is the user's own message
        if (isUserMessage(el, platform)) {
          return;
        }
        
        const text = extractMessageText(el);
        if (text.length >= 3) {
          const hash = getMessageHash(text);
          if (!seenMessageHashes.has(hash)) {
            newMessages.push({ text, hash });
            seenMessageHashes.add(hash);
          }
        }
      });
    } catch (e) {
      // Selector error, ignore
    }
  });
  
  return newMessages;
}

function observeNewMessages() {
  const platform = detectPlatform();
  
  // More specific selectors for the main message container
  const containerSelectors = {
    messenger: [
      '[role="main"]', // Main conversation area
      '[data-qa="conversation"]',
      'main',
    ],
    whatsapp: [
      '[data-testid="conversation-panel-messages"]',
    ],
    generic: [
      '[role="main"]',
      '.messages',
      '.conversation',
      '[class*="chat"]',
    ]
  };
  
  let container = null;
  const selectors = containerSelectors[platform] || containerSelectors.generic;
  
  for (const sel of selectors) {
    try {
      container = document.querySelector(sel);
      if (container) {
        console.log('[Unscamable] Found container:', sel);
        break;
      }
    } catch (e) {
      // Continue
    }
  }

  if (!container) {
    console.log('[Unscamable] No container found, using document.body');
    container = document.body;
  }

  const observer = new MutationObserver((mutations) => {
    mutations.forEach((mutation) => {
      // Check if new nodes were added
      if (mutation.type === 'childList' && mutation.addedNodes.length > 0) {
        // Extract messages from newly added nodes
        const newMessages = extractNewMessages(Array.from(mutation.addedNodes), platform);
        
        if (newMessages.length > 0) {
          // Add to queue and schedule analysis
          newMessagesToAnalyze.push(...newMessages);
          scheduleAnalysis();
          console.log(`[Unscamable] Detected ${newMessages.length} new message(s)`, newMessages);
        }
      }
    });
  });

  observer.observe(container, {
    childList: true,
    subtree: true,
    characterData: false,
  });

  console.log('[Unscamable] Chat monitoring enabled for', platform);
}

let analysisTimeout;
let lastAnalyzedText = '';
let lastAnalysisTime = 0;
const MIN_ANALYSIS_INTERVAL = 2000; // Minimum 2 seconds between analyses
let periodicScanInterval = null;

function scheduleAnalysis() {
  // Debounce: wait 500ms after the last DOM change before analyzing
  clearTimeout(analysisTimeout);
  analysisTimeout = setTimeout(() => {
    performAnalysis();
  }, 500);
}

function performAnalysis() {
  // Only analyze if there are new messages
  if (newMessagesToAnalyze.length === 0) {
    return;
  }
  
  const now = Date.now();
  
  // Check if enough time has passed since last analysis
  if (now - lastAnalysisTime < MIN_ANALYSIS_INTERVAL) {
    console.log('[Unscamable] Skipping analysis (too frequent)');
    return;
  }
  
  // Combine all new messages into one text
  const text = newMessagesToAnalyze.map(m => m.text).join('\n\n');
  newMessagesToAnalyze = []; // Clear the queue
  
  if (text) {
    lastAnalyzedText = text;
    lastAnalysisTime = now;
    
    // Store chat history in storage for persistent analysis
    chrome.storage.local.get({ chatHistory: [] }, (res) => {
      const history = res.chatHistory || [];
      
      // Add new message with timestamp
      history.push({
        text: text,
        timestamp: Date.now(),
        url: window.location.href
      });
      
      // Keep last 50 messages to avoid storage bloat
      if (history.length > 50) {
        history.shift();
      }
      
      chrome.storage.local.set({ chatHistory: history });
      
      // Trigger service worker to auto-analyze
      chrome.runtime.sendMessage(
        { action: 'auto_analyze', text: text },
        (response) => {
          if (chrome.runtime.lastError) {
            console.log('[Unscamable] Service worker not ready');
          } else {
            console.log('[Unscamable] Auto-analysis triggered successfully');
          }
        }
      );
    });
  }
}

// Start periodic scanning every 10 seconds
function startPeriodicScanning() {
  // Clear any existing interval
  if (periodicScanInterval) {
    clearInterval(periodicScanInterval);
  }
  
  // Perform initial scan after 2 seconds
  setTimeout(() => {
    performAnalysis();
  }, 2000);
  
  // Then scan every 10 seconds
  periodicScanInterval = setInterval(() => {
    chrome.storage.local.get({ extensionEnabled: true }, (res) => {
      if (res.extensionEnabled) {
        console.log('[Unscamable] Periodic scan triggered');
        performAnalysis();
      }
    });
  }, 10000); // Scan every 10 seconds
  
  console.log('[Unscamable] Periodic scanning enabled (every 10 seconds)');
}

// ============================================================================
// DEBUG FUNCTION - Check what messages are detected
// ============================================================================

function debugMessages() {
  const platform = detectPlatform();
  console.log('[Unscamable DEBUG] Platform:', platform);
  
  // Find main container
  let mainContainer = document.querySelector('[role="main"]');
  if (!mainContainer) {
    mainContainer = document.querySelector('[data-qa="conversation"]');
  }
  if (!mainContainer) {
    mainContainer = document.body;
  }
  
  console.log('[Unscamable DEBUG] Main container:', mainContainer);
  
  // Try to find messages
  const articles = mainContainer.querySelectorAll('[role="article"]');
  console.log('[Unscamable DEBUG] Found', articles.length, 'articles');
  
  articles.forEach((article, index) => {
    const text = extractMessageText(article);
    const isUser = isUserMessage(article, platform);
    const rect = article.getBoundingClientRect();
    
    console.log(`[Unscamable DEBUG] Message ${index}:`, {
      text: text.substring(0, 50),
      isUserMessage: isUser,
      position: { left: rect.left, right: rect.right },
      offsetHeight: article.offsetHeight
    });
  });
}

// ============================================================================
// MESSAGE LISTENER - BACKWARDS COMPATIBLE
// ============================================================================

chrome.runtime.onMessage.addListener((request, sender, sendResponse) => {
  if (request.action === 'analyze_text') {
    chrome.storage.local.get({ extensionEnabled: true }, (res) => {
      if (!res.extensionEnabled) {
        sendResponse({ text: '', messages: [], paused: true });
        return;
      }
      
      // Extract text and send for analysis
      const platform = detectPlatform();
      const text = scrapeChatText(platform);
      
      sendResponse({ 
        text: text,
        success: true
      });
    });
    return true;
  }
  return true;
});

// Expose debug function globally
window.unscamableDebug = debugMessages;
window.unscamableForceAnalysis = performAnalysis;


// ============================================================================
// INITIALIZATION
// ============================================================================

// Start monitoring when the page loads
if (document.readyState === 'loading') {
  document.addEventListener('DOMContentLoaded', () => {
    observeNewMessages();
  });
} else {
  observeNewMessages();
}