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

// UI: display results
function displayResult(result) {
  const riskScore = result.risk_score || 0;
  const riskLevel = result.status || getRiskLevel(riskScore);
  const riskColor = result.color || getRiskColor(riskScore);

  const header = document.querySelector('.header');
  header.style.background = `linear-gradient(135deg, ${riskColor} 0%, ${riskColor} 100%)`;
  document.getElementById('riskLevel').textContent = riskLevel;

  document.getElementById('riskScore').textContent = riskScore;
  document.querySelector('.risk-number').style.color = riskColor;

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
          document.getElementById('riskLevel').textContent = 'Error';
          document.getElementById('factorsList').innerHTML = '<li>Refresh the page and try again</li>';
          console.error(chrome.runtime.lastError?.message || chrome.runtime.lastError);
          return;
        }

        try {
          const serverResponse = await fetch('http://localhost:5000/analyze', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ text: response.text, image: '' })
          });

          const result = await serverResponse.json();
          displayResult(result);
        } catch (error) {
          document.getElementById('riskLevel').textContent = 'Error';
          document.getElementById('factorsList').innerHTML = '<li>Backend not running. Start Flask server on port 5000</li>';
          console.error(error);
        }
      });
    });
  });
}

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
runAnalysisIfEnabled();