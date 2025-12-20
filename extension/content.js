// Example: Scrape text from a specific chat element
function scrapeChatText() {
  const messages = document.querySelectorAll('.message-text-class'); // Change to actual class
  let fullText = "";
  messages.forEach(msg => fullText += msg.innerText + " ");
  return fullText || "Test Connection Successful!"; // Fallback if no messages found
}

// Listen for messages from the popup
chrome.runtime.onMessage.addListener((request, sender, sendResponse) => {
  if (request.action === "analyze_text") {
    sendResponse({ text: scrapeChatText() });
  }
  return true; // Keeps the message channel open
});