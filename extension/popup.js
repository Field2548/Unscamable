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
  const factorsList = document.getElementById('factorsList');
  
  // Update UI to show scanning state with blue background
  header.style.background = 'linear-gradient(135deg, #42A5F5 0%, #1E88E5 100%)';
  riskLevel.textContent = 'Scanning...';
  riskScore.textContent = '...';
  factorsList.innerHTML = '<li>Analyzing text for scam patterns...</li>';
  
  // Set animated loading icon
  loadingActive = true;
  chrome.action.setIcon({
    path: {
      "16": "icons/loading-animated-16.gif",
      "32": "icons/loading-animated-32.gif",
      "128": "icons/loading-animated-128.gif"
    }
  });
}

// Hide loading animation and restore default icon
function hideLoading() {
  if (!loadingActive) return;
  loadingActive = false;
  
  // Restore default icon to mlogo
  chrome.action.setIcon({
    path: {
      "16": "icons/mlogo.png",
      "32": "icons/mlogo.png",
      "48": "icons/mlogo.png",
      "128": "icons/mlogo.png"
    }
  });
}

// Update action icon based on status and risk score
function updateActionIcon(status) {
  const iconPath = getIconPath(status);
  
  if (iconPath) {
    chrome.action.setIcon({
      path: iconPath
    });
  }
}

// Get icon path based on status
function getIconPath(status) {
  // Status: 'processing' - AI is scanning text (animated GIF)
  if (status === 'processing') {
    return {
      "16": "icons/loading-animated-16.gif",
      "32": "icons/loading-animated-32.gif",
      "128": "icons/loading-animated-128.gif"
    };
  }
  
  // Status: 'cautious' - Risk score = Be cautious (use new.png temporarily)
  if (status === 'cautious') {
    return {
      "16": "icons/new.png",
      "32": "icons/new.png"
    };
  }
  
  // Status: 'highrisk' - High Risk (use new.png temporarily)
  if (status === 'highrisk') {
    return {
      "16": "icons/new.png",
      "32": "icons/new.png"
    };
  }
  
  // Status: 'warning' - Warning (use new.png temporarily)
  if (status === 'warning') {
    return {
      "16": "icons/new.png",
      "32": "icons/new.png"
    };
  }
  
  // Status: 'safe' - Safe (default mlogo)
  if (status === 'safe') {
    return {
      "16": "icons/mlogo.png",
      "32": "icons/mlogo.png",
      "48": "icons/mlogo.png",
      "128": "icons/mlogo.png"
    };
  }
  
  // Default fallback
  return {
    "16": "icons/mlogo.png",
    "32": "icons/mlogo.png",
    "48": "icons/mlogo.png",
    "128": "icons/mlogo.png"
  };
}

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

  // Update action icon based on risk score
  // Safe (score = 0): Default icon, no badge
  // Be cautious (0 < score <= 40): Yellow warning icon with "!" (yellow badge)
  // Warning (40 < score <= 70): Orange warning icon with "!" (orange badge)
  // High Risk (score > 70): Red warning icon with "!" (red badge)
  if (riskScore > 60) {
    chrome.runtime.sendMessage({ action: 'setState', state: 'highrisk' });
    autoOpenPopupIfHighRisk(riskScore);
  } else if (riskScore > 40) {
    chrome.runtime.sendMessage({ action: 'setState', state: 'warning' });
  } else if (riskScore > 0) {
    chrome.runtime.sendMessage({ action: 'setState', state: 'cautious' });
  } else {
    // Safe - show default icon
    chrome.runtime.sendMessage({ action: 'setState', state: 'safe' });
  }

  // Clear any existing timeout and set new one to return to default idle state after 10 seconds
  if (resetIconTimeout) {
    clearTimeout(resetIconTimeout);
  }
  resetIconTimeout = setTimeout(() => {
    chrome.runtime.sendMessage({ action: 'setState', state: 'idle' }, () => {
      console.log('Icon reset to idle state');
    });
    resetIconTimeout = null;
  }, 10000);

  const factorsList = document.getElementById('factorsList');
  factorsList.innerHTML = '';

  if (result.flags && result.flags.length > 0) {
    result.flags.forEach(flag => {
      const li = document.createElement('li');
      li.textContent = flag;
      factorsList.appendChild(li);
    });
  } else {
    const li = document.createElement('li');
    li.textContent = 'No suspicious factors detected';
    factorsList.appendChild(li);
  }

  if (result.entities_found && result.entities_found.length > 0) {
    const li = document.createElement('li');
    li.textContent = `Blacklisted Account: ${result.entities_found[0]}`;
    factorsList.appendChild(li);
  }
}

// Auto-open popup for high risk
function autoOpenPopupIfHighRisk(riskScore) {
  // Only auto-open if risk score is high risk (> 70) and popup is not already open
  if (riskScore > 60) {
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
  const factorsList = document.getElementById('factorsList');
  factorsList.innerHTML = '<li>Extension is paused. Toggle to resume analysis.</li>';
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

async function runAnalysisIfEnabled() {
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
        document.getElementById('factorsList').innerHTML = '<li>Cannot scan Chrome system pages</li>';
        return;
      }

      chrome.tabs.sendMessage(tab.id, { action: 'analyze_text' }, async (response) => {
        if (chrome.runtime.lastError || !response) {
          hideLoading();
          document.getElementById('riskLevel').textContent = 'Error';
          document.getElementById('factorsList').innerHTML = '<li>Refresh the page and try again</li>';
          console.error(chrome.runtime.lastError?.message || chrome.runtime.lastError);
          return;
        }

        try {
          // Show loading animation while analyzing
          showLoading();
          
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
          document.getElementById('factorsList').innerHTML = '<li>Backend not running. Start Flask server on port 5000</li>';
          console.error(error);
        }
      });
    });
  });
}

// Tab change listener - reset icon to default when switching tabs
chrome.tabs.onActivated.addListener(() => {
  hideLoading(); // Stop any running loading animation
  updateActionIcon('safe');
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

// On load
// Set default icon when popup opens
updateActionIcon('safe');
runAnalysisIfEnabled();