/**
 * Service Worker - Icon State Manager for Chrome Extension (Manifest V3)
 * Manages extension icon states: Idle, Scanning, Safe, and Risk
 * 
 * States:
 * - idle: Default icon, no badge
 * - scanning: Animated icon with "SCAN" blue badge
 * - safe: Green checkmark with "✓" green badge
 * - risk: Yellow warning with "!" yellow badge
 */

// ============================================================================
// STATE MANAGEMENT
// ============================================================================

let currentState = 'idle';
let animationInterval = null;
let currentFrameIndex = 0;

// PNG frame animation files (update paths based on your icon structure)
const ANIMATION_FRAMES = [
  'icons/loading-frame-1.png',
  'icons/loading-frame-2.png',
  'icons/loading-frame-3.png',
  'icons/loading-frame-4.png',
  'icons/loading-frame-5.png',
  'icons/loading-frame-6.png',
  'icons/loading-frame-7.png',
  'icons/loading-frame-8.png',
];

// Icon paths configuration
const ICON_CONFIG = {
  IDLE: {
    16: 'icons/new.png',
    32: 'icons/new.png',
  },
  SAFE: {
    16: 'icons/icon16.png',
    32: 'icons/icon32.png',
  },
  RISK: {
    16: 'icons/logo-ext16.png',
    32: 'icons/logo-ext32.png',
  },
};

// Badge configuration
const BADGE_CONFIG = {
  IDLE: { text: '', color: '#FFFFFF' },
  SAFE: { text: '✓', color: '#4CAF50' },
  CAUTIOUS: { text: '!', color: '#FFEB3B' },
  WARNING: { text: '!', color: '#FFA726' },
  HIGH_RISK: { text: '!', color: '#FF5252' },
  SCANNING: { text: 'SCAN', color: '#42A5F5' },
};

// ============================================================================
// STATE SETTER FUNCTIONS
// ============================================================================

/**
 * Set the extension to IDLE state
 * - Shows default icon
 * - Clears badge text
 * - No animation
 */
async function setIdleState() {
  // Stop any running animation
  if (animationInterval) {
    clearInterval(animationInterval);
    animationInterval = null;
  }

  currentState = 'idle';

  try {
    await chrome.action.setIcon({ path: ICON_CONFIG.IDLE });
    await chrome.action.setBadgeText({ text: BADGE_CONFIG.IDLE.text });
    await chrome.action.setTitle({ title: 'Unscamable AI - Ready' });
    console.log('[State Manager] ✓ State changed to: IDLE');
  } catch (error) {
    console.error('[State Manager] Error setting idle state:', error);
  }
}

/**
 * Set the extension to SCANNING state
 * - Shows animated rotating icon using PNG frames
 * - Frames switch every 150ms
 * - Displays blue "SCAN" badge
 * - Prevents multiple simultaneous scanning intervals
 */
async function startScanningState() {
  // Prevent multiple scanning intervals
  if (animationInterval) {
    console.warn('[State Manager] ⚠ Scanning already in progress');
    return;
  }

  currentState = 'scanning';
  currentFrameIndex = 0;

  try {
    // Set initial scanning icon (first frame)
    const firstFrame = ANIMATION_FRAMES[0];
    await chrome.action.setIcon({
      path: {
        16: firstFrame,
        32: firstFrame,
      },
    });

    await chrome.action.setBadgeText({ text: BADGE_CONFIG.SCANNING.text });
    await chrome.action.setBadgeBackgroundColor({
      color: BADGE_CONFIG.SCANNING.color,
    });
    await chrome.action.setTitle({ title: 'Unscamable AI - Scanning...' });

    // Start frame animation - switch every 150ms
    animationInterval = setInterval(async () => {
      if (currentState === 'scanning') {
        // Cycle through animation frames
        currentFrameIndex = (currentFrameIndex + 1) % ANIMATION_FRAMES.length;
        const frame = ANIMATION_FRAMES[currentFrameIndex];

        try {
          await chrome.action.setIcon({
            path: {
              16: frame,
              32: frame,
            },
          });
        } catch (error) {
          console.error('[State Manager] Error updating animation frame:', error);
        }
      } else {
        // Stop animation if state changed
        if (animationInterval) {
          clearInterval(animationInterval);
          animationInterval = null;
        }
      }
    }, 150); // Update frame every 150ms

    console.log('[State Manager] ✓ State changed to: SCANNING (animation started)');
  } catch (error) {
    console.error('[State Manager] Error starting scanning state:', error);
    // Clean up on error
    if (animationInterval) {
      clearInterval(animationInterval);
      animationInterval = null;
    }
  }
}

/**
 * Set the extension to SAFE state
 * - Shows green checkmark icon
 * - Displays green "✓" badge
 * - Used when risk score is 0 (Safe)
 */
async function setSafeState() {
  // Stop any running animation
  if (animationInterval) {
    clearInterval(animationInterval);
    animationInterval = null;
  }

  currentState = 'safe';

  try {
    await chrome.action.setIcon({ path: ICON_CONFIG.SAFE });
    await chrome.action.setBadgeText({ text: BADGE_CONFIG.SAFE.text });
    await chrome.action.setBadgeBackgroundColor({
      color: BADGE_CONFIG.SAFE.color,
    });
    await chrome.action.setTitle({ title: 'Unscamable AI - Safe' });
    console.log('[State Manager] ✓ State changed to: SAFE');
  } catch (error) {
    console.error('[State Manager] Error setting safe state:', error);
  }
}

/**
 * Set the extension to SAFE state
 * - Shows green safe icon
 * - Displays green "✓" badge
 * - Used when risk score is 0 (Safe)
 */
async function setSafeState() {
  // Stop any running animation
  if (animationInterval) {
    clearInterval(animationInterval);
    animationInterval = null;
  }

  currentState = 'safe';

  try {
    await chrome.action.setIcon({ path: ICON_CONFIG.SAFE });
    await chrome.action.setBadgeText({ text: BADGE_CONFIG.SAFE.text });
    await chrome.action.setBadgeBackgroundColor({
      color: BADGE_CONFIG.SAFE.color,
    });
    await chrome.action.setTitle({ title: 'Unscamable AI - Safe' });
    console.log('[State Manager] ✓ State changed to: SAFE (Green)');
  } catch (error) {
    console.error('[State Manager] Error setting safe state:', error);
  }
}

/**
 * Set the extension to BE CAUTIOUS state
 * - Shows yellow warning icon
 * - Displays yellow "!" badge
 * - Used when risk score is low (0 < score <= 40)
 */
async function setCautiousState() {
  // Stop any running animation
  if (animationInterval) {
    clearInterval(animationInterval);
    animationInterval = null;
  }

  currentState = 'cautious';

  try {
    await chrome.action.setIcon({ path: ICON_CONFIG.RISK });
    await chrome.action.setBadgeText({ text: BADGE_CONFIG.CAUTIOUS.text });
    await chrome.action.setBadgeBackgroundColor({
      color: BADGE_CONFIG.CAUTIOUS.color,
    });
    await chrome.action.setTitle({ title: 'Unscamable AI - Be Cautious' });
    console.log('[State Manager] ✓ State changed to: CAUTIOUS (Yellow)');
  } catch (error) {
    console.error('[State Manager] Error setting cautious state:', error);
  }
}

/**
 * Set the extension to WARNING state
 * - Shows orange warning icon
 * - Displays orange "!" badge
 * - Used when risk score is in warning range (40 < score <= 70)
 */
async function setWarningState() {
  // Stop any running animation
  if (animationInterval) {
    clearInterval(animationInterval);
    animationInterval = null;
  }

  currentState = 'warning';

  try {
    await chrome.action.setIcon({ path: ICON_CONFIG.RISK });
    await chrome.action.setBadgeText({ text: BADGE_CONFIG.WARNING.text });
    await chrome.action.setBadgeBackgroundColor({
      color: BADGE_CONFIG.WARNING.color,
    });
    await chrome.action.setTitle({ title: 'Unscamable AI - Warning' });
    console.log('[State Manager] ✓ State changed to: WARNING (Orange)');
  } catch (error) {
    console.error('[State Manager] Error setting warning state:', error);
  }
}

/**
 * Set the extension to HIGH RISK state
 * - Shows red warning icon
 * - Displays red "!" badge
 * - Used when risk score is high (> 70)
 */
async function setHighRiskState() {
  // Stop any running animation
  if (animationInterval) {
    clearInterval(animationInterval);
    animationInterval = null;
  }

  currentState = 'highRisk';

  try {
    await chrome.action.setIcon({ path: ICON_CONFIG.RISK });
    await chrome.action.setBadgeText({ text: BADGE_CONFIG.HIGH_RISK.text });
    await chrome.action.setBadgeBackgroundColor({
      color: BADGE_CONFIG.HIGH_RISK.color,
    });
    await chrome.action.setTitle({ title: 'Unscamable AI - High Risk' });
    console.log('[State Manager] ✓ State changed to: HIGH RISK (Red)');
  } catch (error) {
    console.error('[State Manager] Error setting high risk state:', error);
  }
}

// ============================================================================
// UTILITY FUNCTIONS
// ============================================================================

/**
 * Get the current state of the extension
 * @returns {string} Current state: 'idle', 'scanning', 'safe', 'risk', or 'highRisk'
 */
function getCurrentState() {
  return currentState;
}

/**
 * Check if the extension is currently scanning
 * @returns {boolean} True if scanning state is active with animation
 */
function isScanning() {
  return currentState === 'scanning' && animationInterval !== null;
}

/**
 * Initialize the extension to IDLE state on startup
 */
async function initializeExtension() {
  console.log('[State Manager] Initializing extension...');
  await setIdleState();
}

// ============================================================================
// MESSAGE LISTENER & INITIALIZATION
// ============================================================================

// Initialize when service worker starts
initializeExtension();

/**
 * Open the extension popup
 */
async function openPopup() {
  try {
    await chrome.action.openPopup();
    console.log('[State Manager] Popup opened');
  } catch (error) {
    console.error('[State Manager] Error opening popup:', error);
  }
}

/**
 * Listen for messages from popup or content scripts
 * Supported messages:
 * - { action: 'setState', state: 'idle' | 'scanning' | 'safe' | 'cautious' | 'warning' | 'highRisk' }
 * - { action: 'getState' }
 * - { action: 'openPopup' }
 */
chrome.runtime.onMessage.addListener((request, sender, sendResponse) => {
  if (request.action === 'setState') {
    const state = request.state?.toLowerCase();

    switch (state) {
      case 'idle':
        setIdleState().then(() => sendResponse({ success: true, state: 'idle' }));
        break;

      case 'scanning':
        startScanningState().then(() =>
          sendResponse({ success: true, state: 'scanning' })
        );
        break;

      case 'safe':
        setSafeState().then(() => sendResponse({ success: true, state: 'safe' }));
        break;

      case 'cautious':
        setCautiousState().then(() => sendResponse({ success: true, state: 'cautious' }));
        break;

      case 'warning':
        setWarningState().then(() =>
          sendResponse({ success: true, state: 'warning' })
        );
        break;

      case 'highrisk':
        setHighRiskState().then(() =>
          sendResponse({ success: true, state: 'highRisk' })
        );
        break;

      default:
        sendResponse({ success: false, error: `Unknown state: ${state}` });
    }

    return true; // Keep message channel open for async response
  }

  if (request.action === 'getState') {
    sendResponse({
      state: getCurrentState(),
      isScanning: isScanning(),
    });
  }

  if (request.action === 'openPopup') {
    openPopup().then(() => sendResponse({ success: true }));
    return true; // Keep message channel open for async response
  }
});

// ============================================================================
// AUTO-SCAN FUNCTIONALITY
// ============================================================================

/**
 * Analyze text from a tab by sending a message to content script
 * @param {number} tabId - The tab ID to analyze
 */
async function analyzeTabContent(tabId) {
  try {
    // Check if extension is enabled
    const result = await chrome.storage.local.get({ extensionEnabled: true });
    if (!result.extensionEnabled) {
      console.log('[Auto-Scan] Extension is disabled, skipping analysis');
      return;
    }

    // Start scanning state
    await startScanningState();

    // Send message to content script to get text
    chrome.tabs.sendMessage(tabId, { action: 'analyze_text' }, async (response) => {
      if (chrome.runtime.lastError) {
        console.log('[Auto-Scan] Could not send message to tab:', chrome.runtime.lastError);
        await setIdleState();
        return;
      }

      if (!response || response.paused) {
        console.log('[Auto-Scan] Extension is paused or no response');
        await setIdleState();
        return;
      }

      try {
        // Send text to backend for analysis
        const serverResponse = await fetch('http://localhost:5000/analyze', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ text: response.text, image: '' })
        });

        const analysisResult = await serverResponse.json();
        const riskScore = analysisResult.risk_score || 0;

        // Update extension state based on risk score
        if (riskScore > 70) {
          await setHighRiskState();
          console.log('[Auto-Scan] High risk detected! Score:', riskScore);
        } else if (riskScore > 40) {
          await setWarningState();
          console.log('[Auto-Scan] Warning detected. Score:', riskScore);
        } else if (riskScore > 0) {
          await setCautiousState();
          console.log('[Auto-Scan] Caution recommended. Score:', riskScore);
        } else {
          await setSafeState();
          console.log('[Auto-Scan] Page is safe. Score:', riskScore);
        }

        // Reset to idle after 10 seconds
        setTimeout(async () => {
          await setIdleState();
          console.log('[Auto-Scan] Reset to idle state');
        }, 10000);
      } catch (error) {
        console.error('[Auto-Scan] Error analyzing content:', error);
        await setIdleState();
      }
    });
  } catch (error) {
    console.error('[Auto-Scan] Error in analyzeTabContent:', error);
    await setIdleState();
  }
}

/**
 * Listen for tab updates and auto-scan if enabled
 */
chrome.tabs.onUpdated.addListener((tabId, changeInfo, tab) => {
  // Only scan when page is loaded and not a Chrome system page
  if (changeInfo.status === 'complete' && tab.url && !tab.url.startsWith('chrome://')) {
    console.log('[Auto-Scan] Tab updated and loaded:', tab.url);
    analyzeTabContent(tabId);
  }
});

/**
 * Listen for tab activation and auto-scan if enabled
 */
chrome.tabs.onActivated.addListener((activeInfo) => {
  chrome.tabs.get(activeInfo.tabId, (tab) => {
    if (tab && tab.url && !tab.url.startsWith('chrome://')) {
      console.log('[Auto-Scan] Tab activated:', tab.url);
      analyzeTabContent(activeInfo.tabId);
    }
  });
});

// ============================================================================
// EXTENSION ICON CLICK HANDLER
// ============================================================================

/**
 * Handle extension icon click
 * Example workflow: idle → scanning → result (safe/risk) → idle
 */
chrome.action.onClicked.addListener(async (tab) => {
  const state = getCurrentState();

  if (state === 'idle') {
    console.log('[State Manager] Icon clicked - Starting scan...');
    await startScanningState();

    // Simulate analysis delay (3 seconds)
    setTimeout(async () => {
      // Example: Randomly determine result for demonstration
      const randomScore = Math.random() * 100;

      if (randomScore > 40) {
        await setWarningState();
        console.log('[State Manager] Analysis complete - Risk detected');
      } else {
        await setSafeState();
        console.log('[State Manager] Analysis complete - Safe');
      }

      // Return to idle after displaying result (5 seconds)
      setTimeout(async () => {
        await setIdleState();
        console.log('[State Manager] Reset to idle');
      }, 5000);
    }, 3000);
  } else if (state !== 'scanning') {
    // If in any other state (safe, risk, etc.), reset to idle
    console.log('[State Manager] Icon clicked - Resetting to idle...');
    await setIdleState();
  }
  // If already scanning, do nothing (prevent multiple scans)
});

// ============================================================================
// EXPORT FUNCTIONS (for internal use if needed)
// ============================================================================

// Expose functions to global scope if needed by other scripts
// Note: These are primarily used via message passing, but can be called
// directly from service worker context if needed
