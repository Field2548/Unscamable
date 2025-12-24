// Get risk level label based on score
function getRiskLevel(score) {
  if (score > 70) return "High Risk";
  if (score > 40) return "Warning";
  if (score > 0) return "Be cautious";
  return "Safe";
}

// Get risk level color
function getRiskColor(score) {
  if (score > 70) return "#FF5252";  // Red
  if (score > 40) return "#FFA726";  // Orange
  if (score > 0) return "#DECA30";  // Yellow
  return "#4CAF50";  // Green
}

// Display analysis results
function displayResult(result) {
  const riskScore = result.risk_score || 0;
  const riskLevel = result.status || getRiskLevel(riskScore);
  const riskColor = result.color || getRiskColor(riskScore);
  
  // Update header with color
  const header = document.querySelector('.header');
  header.style.background = `linear-gradient(135deg, ${riskColor} 0%, ${riskColor} 100%)`;
  document.getElementById('riskLevel').textContent = riskLevel;
  
  // Update risk score display with color
  document.getElementById('riskScore').textContent = riskScore;
  document.querySelector('.risk-number').style.color = riskColor;
  
  // Update factors list
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
  
  // Add bank accounts if found
  if (result.entities_found && result.entities_found.length > 0) {
    const li = document.createElement('li');
    li.textContent = `Blacklisted Account: ${result.entities_found[0]}`;
    factorsList.appendChild(li);
  }
}

// Close button handler
document.getElementById('closeBtn').addEventListener('click', () => {
  window.close();
});

// Main analysis logic
chrome.tabs.query({active: true, currentWindow: true}, (tabs) => {
  // Check if we can actually run scripts on this page
  if (tabs[0].url.startsWith("chrome://")) {
    document.getElementById('riskLevel').textContent = "Unavailable";
    document.getElementById('factorsList').innerHTML = '<li>Cannot scan Chrome system pages</li>';
    return;
  }

  chrome.tabs.sendMessage(tabs[0].id, {action: "analyze_text"}, async (response) => {
    // Check if content script responded
    if (chrome.runtime.lastError || !response) {
      document.getElementById('riskLevel').textContent = "Error";
      document.getElementById('factorsList').innerHTML = '<li>Refresh the page and try again</li>';
      console.error(chrome.runtime.lastError?.message || chrome.runtime.lastError);
      return;
    }

    // If we got text, send to backend
    try {
      const serverResponse = await fetch('http://localhost:5000/analyze', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ 
          text: response.text,
          image: ""
        })
      });
      
      const result = await serverResponse.json();
      displayResult(result);
    } catch (error) {
      document.getElementById('riskLevel').textContent = "Error";
      document.getElementById('factorsList').innerHTML = '<li>Backend not running. Start Flask server on port 5000</li>';
      console.error(error);
    }
  });
});