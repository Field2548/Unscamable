const MESSAGE_SELECTORS = [
  '.message-text-class',           // placeholder
  '[data-testid="message-text"]',
  '[data-testid="conversation"]',
  '[role="textbox"]',
  '.chat-message',
  '.message',
  '.msg',
  '.bubble',
  '.conversation',
  '.text'
];

function uniqueStrings(items) {
  const seen = new Set();
  const result = [];
  for (const item of items) {
    const trimmed = item.trim();
    if (!trimmed) continue;
    if (seen.has(trimmed)) continue;
    seen.add(trimmed);
    result.push(trimmed);
  }
  return result;
}

function scrapeChatText() {
  const collected = [];

  for (const selector of MESSAGE_SELECTORS) {
    document.querySelectorAll(selector).forEach((node) => {
      if (node && node.innerText) {
        collected.push(node.innerText);
      }
    });
    if (collected.length > 0) break; // stop at first selector that yields text
  }

  if (collected.length === 0 && document.body) {
    collected.push(document.body.innerText || '');
  }

  const text = uniqueStrings(collected).join(' ').trim();

  return text || 'Test Connection Successful!';
}

chrome.runtime.onMessage.addListener((request, sender, sendResponse) => {
  if (request.action === 'analyze_text') {
    chrome.storage.local.get({ extensionEnabled: true }, (res) => {
      if (!res.extensionEnabled) {
        sendResponse({ text: '', paused: true });
        return;
      }
      sendResponse({ text: scrapeChatText() });
    });
    return true; // keep the message channel open for async sendResponse
  }
  return true;
});