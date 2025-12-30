// ============================================================================
// CHAT SELECTORS FOR DIFFERENT PLATFORMS
// ============================================================================

const PLATFORM_SELECTORS = {
  // Facebook Messenger / Messenger.com
  messenger: [
    '[data-testid="messageContent"]',
    '[role="article"] span',
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

const MESSAGE_OBSERVERS = new Map();
let seenMessages = new Set();

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

function getMessageHash(text) {
  // Simple hash to detect duplicate messages
  if (!text) return '';
  const trimmed = text.trim().substring(0, 100);
  return trimmed;
}

function scrapeChatText(platform = null) {
  if (!platform) {
    platform = detectPlatform();
  }

  const selectors = PLATFORM_SELECTORS[platform] || PLATFORM_SELECTORS.generic;
  const messages = [];

  for (const selector of selectors) {
    try {
      const elements = document.querySelectorAll(selector);
      
      for (const el of elements) {
        if (el && el.offsetHeight > 0) { // only visible elements
          const text = extractMessageText(el);
          
          if (text.length > 3) { // filter out tiny fragments
            const hash = getMessageHash(text);
            
            if (!seenMessages.has(hash)) {
              messages.push(text);
              seenMessages.add(hash);
            }
          }
        }
      }
      
      if (messages.length > 0) break; // found messages, stop searching
    } catch (e) {
      console.error('[Unscamable] Selector error:', e);
    }
  }

  // If no messages found, return all visible text from the page
  if (messages.length === 0 && document.body) {
    const bodyText = document.body.innerText?.trim() || '';
    if (bodyText) {
      messages.push(bodyText);
    }
  }

  const combinedText = messages.join('\n\n').trim();
  return combinedText || 'No content detected.';
}

// ============================================================================
// CONTINUOUS MONITORING WITH MUTATIONOBSERVER
// ============================================================================

function observeNewMessages() {
  const platform = detectPlatform();
  const selectors = PLATFORM_SELECTORS[platform] || PLATFORM_SELECTORS.generic;
  
  const containerSelectors = [
    '[data-testid="messageContent"]',
    '[class*="chat"]',
    '[role="main"]',
    '.messages',
    '.conversation',
    'main',
    '[data-qa="conversation"]',
  ];

  let container = null;
  for (const sel of containerSelectors) {
    container = document.querySelector(sel);
    if (container) break;
  }

  if (!container) {
    container = document.body;
  }

  const observer = new MutationObserver((mutations) => {
    mutations.forEach((mutation) => {
      // Check if new nodes were added
      if (mutation.type === 'childList') {
        mutation.addedNodes.forEach((node) => {
          // Only process element nodes
          if (node.nodeType !== 1) return;

          // Check if the new node or its children contain messages
          const messageElements = node.querySelectorAll?.(...selectors) || [];
          
          if (messageElements.length > 0) {
            // New messages detected, trigger analysis
            scheduleAnalysis();
          }
        });
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
  const text = scrapeChatText();
  const now = Date.now();
  
  // Check if enough time has passed since last analysis
  if (now - lastAnalysisTime < MIN_ANALYSIS_INTERVAL) {
    console.log('[Unscamable] Skipping analysis (too frequent)');
    return;
  }
  
  if (text && text !== 'No content detected.') {
    // Always analyze even if text is the same (in case backend logic changed or for periodic updates)
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
// MESSAGE LISTENER
// ============================================================================

chrome.runtime.onMessage.addListener((request, sender, sendResponse) => {
  if (request.action === 'analyze_text') {
    chrome.storage.local.get({ extensionEnabled: true }, (res) => {
      if (!res.extensionEnabled) {
        sendResponse({ text: '', paused: true });
        return;
      }
      sendResponse({ text: scrapeChatText() });
    });
    return true;
  }
  return true;
});

// ============================================================================
// INITIALIZATION
// ============================================================================

// Start monitoring when the page loads
if (document.readyState === 'loading') {
  document.addEventListener('DOMContentLoaded', () => {
    observeNewMessages();
    startPeriodicScanning();
  });
} else {
  observeNewMessages();
  startPeriodicScanning();
}