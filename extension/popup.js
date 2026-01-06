// Helpers: risk label/color
function getRiskLevel(score) {
  if (score > 70) return "High Risk";
  if (score > 40) return "Warning";
  if (score > 0) return "Be cautious";
  return "Safe";
}

function getRiskColor(score) {
  if (score > 70) return "#FF5252";
  if (score > 40) return "#FFA726";
  if (score > 0) return "#DECA30";
  return "#4CAF50";
}

// Loading animation variables
let loadingActive = false;
let resetIconTimeout = null;

// Show loading animation
function showLoading() {
  const header = document.querySelector('.header');
  const riskLevel = document.getElementById('riskLevel');
  const riskScore = document.getElementById('riskScore');
  const categoriesContainer = document.getElementById('categoriesContainer');
  
  // Update UI to show scanning state with blue background
  header.style.background = 'linear-gradient(135deg, #42A5F5 0%, #1E88E5 100%)';
  riskLevel.textContent = 'Scanning...';
  riskScore.textContent = '...';
  categoriesContainer.innerHTML = '<div class="category-item"><p class="category-name">Analyzing text for scam patterns...</p></div>';
  
  // Notify service worker to set scanning state (service worker manages icons)
  loadingActive = true;
  chrome.runtime.sendMessage({ action: 'setState', state: 'scanning' });
}

// Hide loading animation and restore default icon
function hideLoading() {
  if (!loadingActive) return;
  loadingActive = false;
  // Icon will be managed by service worker based on analysis results
}

// Icon management is handled entirely by service_worker.js
// This ensures consistent icon state across all tabs and contexts

// Helper function to determine status based on risk score
function getStatusFromRiskScore(riskScore) {
  if (riskScore > 70) return 'highrisk';
  if (riskScore > 40) return 'warning';
  if (riskScore > 0) return 'cautious';
  return 'safe';
}

// UI: display results
function displayResult(result) {
  // Stop loading animation first
  hideLoading();
  
  const riskScore = result.risk_score || 0;
  const riskLevel = result.status || getRiskLevel(riskScore);
  const riskColor = result.color || getRiskColor(riskScore);
  const status = getStatusFromRiskScore(riskScore);

  const header = document.querySelector('.header');
  header.style.background = `linear-gradient(135deg, ${riskColor} 0%, ${riskColor} 100%)`;
  document.getElementById('riskLevel').textContent = riskLevel;

  document.getElementById('riskScore').textContent = riskScore;
  document.querySelector('.risk-number').style.color = riskColor;

  // Update extension state based on risk score via service worker
  // Safe (score = 0): Default icon, no badge
  // Be cautious (0 < score <= 40): Yellow "!" badge
  // Warning (40 < score <= 70): Orange "!" badge
  // High Risk (score > 70): Red "!" badge
  if (riskScore > 70) {
    chrome.runtime.sendMessage({ action: 'setState', state: 'highrisk' });
    autoOpenPopupIfHighRisk(riskScore);
  } else if (riskScore > 40) {
    chrome.runtime.sendMessage({ action: 'setState', state: 'warning' });
  } else if (riskScore > 0) {
    chrome.runtime.sendMessage({ action: 'setState', state: 'cautious' });
  } else {
    // Safe - show safe state
    chrome.runtime.sendMessage({ action: 'setState', state: 'safe' });
  }

  // Service worker will automatically reset to idle state after analysis

  const categoriesContainer = document.getElementById('categoriesContainer');
  categoriesContainer.innerHTML = '';

  if (result.flags && result.flags.length > 0) {
    // Parse flags to extract category and message information
    const categoriesMap = {};
    
    result.flags.forEach(flag => {
      // Parse flag format: "Category: detected in X message(s)" or "Category, ... → "message content""
      let category = flag;
      let message = '';
      let count = 1;
      
      if (flag.includes(': detected in')) {
        // Format: "Category: detected in X message(s)"
        const match = flag.match(/^(.+?):\s+detected in (\d+) message\(s\)$/);
        if (match) {
          category = match[1];
          count = parseInt(match[2]);
        }
      } else if (flag.includes(' → ')) {
        // Format: "Category, ... → "message content""
        const parts = flag.split(' → ');
        const categoryPart = parts[0];
        message = parts[1] || '';
        
        // Extract main category (first category before comma)
        const categoryMatch = categoryPart.match(/^([^,]+)/);
        if (categoryMatch) {
          category = categoryMatch[1];
        }
      }
      
      if (!categoriesMap[category]) {
        categoriesMap[category] = {
          name: category,
          messages: [],
          count: 0
        };
      }
      
      if (message) {
        categoriesMap[category].messages.push(message);
      }
      categoriesMap[category].count = Math.max(categoriesMap[category].count, count);
    });
    
    // Create category cards
    Object.keys(categoriesMap).forEach(key => {
      const categoryData = categoriesMap[key];
      const categoryDiv = document.createElement('div');
      categoryDiv.className = 'category-item';
      
      const categoryName = document.createElement('p');
      categoryName.className = 'category-name';
      categoryName.textContent = categoryData.name;
      categoryDiv.appendChild(categoryName);
      
      if (categoryData.messages.length > 0) {
        const messagesList = document.createElement('ul');
        messagesList.className = 'messages-list';
        
        categoryData.messages.forEach(msg => {
          const li = document.createElement('li');
          const wrapper = document.createElement('div');
          wrapper.className = 'message-wrapper';
          
          const msgText = document.createElement('span');
          msgText.className = 'message-text truncated';
          
          const isLong = msg.length > 80;
          if (isLong) {
            msgText.textContent = msg.substring(0, 80) + '...';
          } else {
            msgText.textContent = msg;
          }
          wrapper.appendChild(msgText);
          
          if (isLong) {
            const expandBtn = document.createElement('button');
            expandBtn.className = 'expand-btn';
            expandBtn.textContent = 'More';
            
            let isExpanded = false;
            expandBtn.addEventListener('click', (e) => {
              e.preventDefault();
              isExpanded = !isExpanded;
              
              if (isExpanded) {
                msgText.textContent = msg;
                msgText.className = 'message-text full';
                expandBtn.textContent = 'Less';
              } else {
                msgText.textContent = msg.substring(0, 80) + '...';
                msgText.className = 'message-text truncated';
                expandBtn.textContent = 'More';
              }
            });
            
            wrapper.appendChild(expandBtn);
          }
          
          li.appendChild(wrapper);
          messagesList.appendChild(li);
        });
        
        categoryDiv.appendChild(messagesList);
      }
      
      const countDiv = document.createElement('div');
      countDiv.className = 'message-count';
      countDiv.textContent = `Detected in ${categoryData.count} message(s)`;
      categoryDiv.appendChild(countDiv);
      
      categoriesContainer.appendChild(categoryDiv);
    });
  } else {
    const noneDiv = document.createElement('div');
    noneDiv.className = 'category-item';
    const p = document.createElement('p');
    p.className = 'category-name';
    p.textContent = 'No suspicious factors detected';
    noneDiv.appendChild(p);
    categoriesContainer.appendChild(noneDiv);
  }

  if (result.entities_found && result.entities_found.length > 0) {
    const blacklistDiv = document.createElement('div');
    blacklistDiv.className = 'category-item';
    const categoryName = document.createElement('p');
    categoryName.className = 'category-name';
    categoryName.textContent = 'Blacklisted Account';
    blacklistDiv.appendChild(categoryName);
    
    const messagesList = document.createElement('ul');
    messagesList.className = 'messages-list';
    
    result.entities_found.forEach(entity => {
      const li = document.createElement('li');
      li.textContent = entity;
      messagesList.appendChild(li);
    });
    
    blacklistDiv.appendChild(messagesList);
    categoriesContainer.appendChild(blacklistDiv);
  }
}

// Auto-open popup for high risk
function autoOpenPopupIfHighRisk(riskScore) {
  // Only auto-open if risk score is high risk (> 70) and popup is not already open
  if (riskScore > 70) {
    // Send message to service worker to confirm high risk detected
    chrome.runtime.sendMessage({ action: 'openPopup' }, (response) => {
      if (response && response.success) {
        console.log('High risk popup auto-opened');
      }
    });
  }
}

function setPausedUI() {
  const header = document.querySelector('.header');
  header.style.background = 'linear-gradient(135deg, #9E9E9E 0%, #757575 100%)';
  document.getElementById('riskLevel').textContent = 'Paused';
  document.getElementById('riskScore').textContent = '-';
  document.querySelector('.risk-number').style.color = '#757575';
  const categoriesContainer = document.getElementById('categoriesContainer');
  categoriesContainer.innerHTML = '<div class="category-item"><p class="category-name">Extension is paused. Toggle to resume analysis.</p></div>';
}

function setToggleUI(enabled) {
  const toggleSwitch = document.getElementById('toggleSwitch');
  const toggleLabel = document.getElementById('toggleLabel');
  if (toggleSwitch) toggleSwitch.checked = !!enabled;
  if (toggleLabel) toggleLabel.textContent = enabled ? 'On' : 'Off';
}

function getEnabled(callback) {
  chrome.storage.local.get({ extensionEnabled: true }, (res) => {
    callback(Boolean(res.extensionEnabled));
  });
}

function setEnabled(value, callback) {
  chrome.storage.local.set({ extensionEnabled: Boolean(value) }, () => {
    if (callback) callback();
  });
}

function runAnalysisIfEnabled() {
  getEnabled((enabled) => {
    setToggleUI(enabled);
    if (!enabled) {
      setPausedUI();
      return;
    }

    chrome.tabs.query({ active: true, currentWindow: true }, (tabs) => {
      const tab = tabs && tabs[0];
      if (!tab || !tab.url) {
        setPausedUI();
        return;
      }

      if (tab.url.startsWith('chrome://')) {
        document.getElementById('riskLevel').textContent = 'Unavailable';
        document.getElementById('categoriesContainer').innerHTML = '<div class="category-item"><p class="category-name">Cannot scan Chrome system pages</p></div>';
        return;
      }

      showLoading(); // Show loading before sending message

      chrome.tabs.sendMessage(tab.id, { action: 'analyze_text' }, (response) => {
        // Check for lastError immediately with safe access
        const lastError = chrome.runtime.lastError;
        if (lastError) {
          console.error('[Unscamable] Content script error:', lastError?.message || lastError?.toString() || 'Unknown error');
          hideLoading();
          document.getElementById('riskLevel').textContent = 'Error';
          document.getElementById('categoriesContainer').innerHTML = '<div class="category-item"><p class="category-name">Refresh the page and try again</p></div>';
          return;
        }

        if (!response) {
          console.error('[Unscamable] No response from content script');
          hideLoading();
          document.getElementById('riskLevel').textContent = 'Error';
          document.getElementById('categoriesContainer').innerHTML = '<div class="category-item"><p class="category-name">Refresh the page and try again</p></div>';
          return;
        }

        // Proceed with async analysis
        (async () => {
          try {
            const serverResponse = await fetch('http://localhost:5000/analyze', {
              method: 'POST',
              headers: { 'Content-Type': 'application/json' },
              body: JSON.stringify({ text: response.text, image: '' })
            });

            const result = await serverResponse.json();
            
            // Hide loading animation and display results
            displayResult(result);
          } catch (error) {
            hideLoading();
            document.getElementById('riskLevel').textContent = 'Error';
            document.getElementById('categoriesContainer').innerHTML = '<div class="category-item"><p class="category-name">Backend not running. Start Flask server on port 5000</p></div>';
            console.error('[Unscamable] Fetch error:', error?.message || String(error));
          }
        })();
      });
    });
  });
}

// Tab change listener - cleanup on tab switch
chrome.tabs.onActivated.addListener(() => {
  hideLoading(); // Stop loading UI state
});

// Init handlers
document.getElementById('closeBtn').addEventListener('click', () => window.close());

document.getElementById('toggleSwitch').addEventListener('change', (e) => {
  const next = !!e.target.checked;
  setEnabled(next, () => {
    setToggleUI(next);
    if (next) {
      runAnalysisIfEnabled();
    } else {
      setPausedUI();
    }
  });
});

// On load - run analysis
runAnalysisIfEnabled();

// Listen for auto-analysis updates from content script
chrome.runtime.onMessage.addListener((request, sender, sendResponse) => {
  if (request.action === 'auto_analyze_result') {
    // Update popup display with new analysis results
    displayResult(request.result);
    sendResponse({ success: true });
  }
  return true;
});