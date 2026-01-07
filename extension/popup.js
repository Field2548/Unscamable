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

  // Build categories map focused on the snippets tied to each category
  const categoriesMap = {};
  // Category keywords and their weights from NLP module (scam_keywords.py)
  const CATEGORY_KEYWORDS = {
    "Authority" : ["ตำรวจ", "เจ้าหน้าที่", "กรม", "กระทรวง", "ฝ่ายความปลอดภัย", "ศาล", "หมายศาล", "คดีความ", "ปปง.", "สิทธิ์รัฐ", "ธนาคาร", "ศูนย์บริการ", "ฝ่ายกฎหมาย", "ฝ่าย กฎหมาย"],
    "Financial Pressure": ["ยอดค้างชำระ", "ค้างชำระ", "ค่าปรับ", "ค่าธรรมเนียม", "หนี้ค้าง", "ชำระเงิน", "โอนเงิน", "จ่ายบิล", "โอนเงินผิดปกติ", "คืนเงิน", "โอนเงินคืน", "ใบสั่งออนไลน์", "ชำระค่าปรับ", "วงเงินเหลือ", "ค่าไฟฟ้า", "ค่าปรับจราจร"],
    "OTP Request": ["รหัส OTP", "OTP"],
    "Promotional Bait": ["ได้รับรางวัล", "iPhone", "โปรโมชั่น", "โปรเด็ด", "โปรพิเศษ", "ฝาก100รับ200", "เงินคืน", "กำไรการันตี", "ลงทุนน้อย", "งานพาร์ทไทม์", "รายได้ดี", "รับของรางวัล", "แบบสอบถาม", "ฟรี", "ระบบออโต้", "ไม่มีขั้นต่ำ"],
    "Link Requests": ["คลิกลิงก์", "กดลิงก์", "ตรวจสอบที่", "ตรวจสอบเลย", "ติดต่อด่วน", "ติดต่อเจ้าหน้าที่", "แอดไลน์", "คลิกยืนยัน", "เพื่อตรวจสอบ"],
    "Delivery Scams": ["พัสดุ", "ขนส่ง", "จัดส่ง", "เลขแทรกกิ้ง", "ติดต่อผู้รับไม่ได้", "ยืนยันการจัดส่ง", "ไม่สามารถจัดส่ง", "เช็กสถานะ"],
    "Urgency": ["ด่วน", "เร่งด่วน", "ภายใน 24 ชั่วโมง", "ทันที", "วันนี้เท่านั้น", "หมดอายุวันนี้", "ครั้งสุดท้าย", "สุดท้าย", "จะถูกระงับ", "ถูกระงับ", "ระงับบัญชี", "ระงับบริการ", "ถูกปิดใช้งาน", "ลงทะเบียนด่วน"],
    "Identity Threat": ["บัญชีของคุณ", "บัญชีของท่าน", "ยืนยันตัวตน", "ตรวจสอบตัวตน", "รหัส OTP", "ยืนยันความปลอดภัย", "ระบบตรวจพบ", "การเข้าถึงผิดปกติ", "บัญชีถูกแฮก", "ระงับบัญชีชั่วคราว"]
  };
  
  // Category weights from NLP scam_keywords.py - determines risk impact
  const CATEGORY_WEIGHTS = {
    "Promotional Bait": 30,      // Highest - most deceptive
    "Identity Threat": 25,        // Very high - directly exploits account access
    "Authority": 20,              // High - impersonation risk
    "Financial Pressure": 20,     // High - financial loss risk
    "Delivery Scams": 20,         // High - delivery fraud risk
    "Link Requests": 15,          // Medium - clicking risk
    "OTP Request": 25,            // Very high - account compromise
    "Urgency": 10                 // Lower weight but common tactic
  };
  
  // Regex pattern weights from NLP _regex.py - additional risk signals
  const REGEX_WEIGHTS = {
    "Suspicious URL": 20,          // URL regex weight
    "Money Mentions": 10,          // Money regex weight  
    "Time Pressure": 10,           // Time pressure regex weight
    "OTP Request": 25              // OTP regex weight
  };

  const focusSnippet = (cat, text) => {
    const keywords = CATEGORY_KEYWORDS[cat];
    if (!keywords || !text) return text;
    const hit = keywords.find((kw) => text.includes(kw));
    return hit || text;
  };
  
  // Get weight indicator for category - shows visual importance based on NLP weights
  const getWeightIndicator = (category) => {
    // Check in category weights first
    let weight = CATEGORY_WEIGHTS[category];
    
    // If not found, check in regex weights
    if (weight === undefined) {
      weight = REGEX_WEIGHTS[category] || 0;
    }
    
    if (weight >= 30) return "🔴"; // Critical (Promotional Bait)
    if (weight >= 25) return "🔴"; // Very High (Identity Threat, OTP)
    if (weight >= 20) return "🟠"; // High (Authority, Financial, Delivery, URL)
    if (weight >= 15) return "🟡"; // Medium (Link Requests)
    if (weight >= 10) return "🟡"; // Medium-Low (Money, Time Pressure)
    return "🟢"; // Lower
  };
  
  const shouldSkipSnippet = (text) => {
    if (!text) return true;
    const trimmed = text.trim();
    // Ignore platform status lines like "Active 4 minutes ago" in Thai
    if (/^ใช้งานเมื่อ\s+\d+\s+นาที\s+ที่แล้ว/i.test(trimmed)) return true;
    return false;
  };

  // Parse flags first: they already contain category labels and snippets
  if (result.flags && result.flags.length > 0) {
    result.flags.forEach((flag) => {
      if (flag.includes(' → ')) {
        const parts = flag.split(' → ');
        const categoryPart = parts[0];
        let snippet = parts[1] || '';
        // Remove quotes from snippet if present
        snippet = snippet.replace(/^"|"$/g, '');
        const categories = categoryPart.split(',').map((c) => c.trim()).filter(Boolean);
        categories.forEach((cat) => {
          const normalizedCat = cat === 'Time Pressure' ? 'Urgency' : cat;
          if (!categoriesMap[normalizedCat]) {
            categoriesMap[normalizedCat] = { name: normalizedCat, messages: [], messageSet: new Set(), count: 0 };
          }
          const focused = snippet.includes(',') ? snippet : focusSnippet(normalizedCat, snippet);
          if (!shouldSkipSnippet(focused) && !categoriesMap[normalizedCat].messageSet.has(focused)) {
            categoriesMap[normalizedCat].messageSet.add(focused);
            categoriesMap[normalizedCat].messages.push(focused);
          }
          categoriesMap[normalizedCat].count += 1;
        });
      } else if (flag.includes(': detected in')) {
        const match = flag.match(/^(.+?):\s+detected in (\d+) message\(s\)$/);
        if (match) {
          const cat = match[1] === 'Time Pressure' ? 'Urgency' : match[1];
          const cnt = parseInt(match[2], 10);
          if (!categoriesMap[cat]) {
            categoriesMap[cat] = { name: cat, messages: [], messageSet: new Set(), count: 0 };
          }
          categoriesMap[cat].count = Math.max(categoriesMap[cat].count, cnt || 0);
        }
      }
    });
  }

  // If no snippets captured via flags, fall back to message summaries (rare)
  if (Object.keys(categoriesMap).length === 0) {
    const messageSummaries = (result.analysis && result.analysis.message_summaries) || [];
    messageSummaries.forEach((summary) => {
      const text = summary.text || '';
      (summary.categories || []).forEach((cat) => {
        const normalizedCat = cat === 'Time Pressure' ? 'Urgency' : cat;
        if (!categoriesMap[cat]) {
          categoriesMap[normalizedCat] = { name: normalizedCat, messages: [], messageSet: new Set(), count: 0 };
        }
        const focused = focusSnippet(normalizedCat, text);
        if (!shouldSkipSnippet(focused) && !categoriesMap[normalizedCat].messageSet.has(focused)) {
          categoriesMap[normalizedCat].messageSet.add(focused);
          categoriesMap[normalizedCat].messages.push(focused);
        }
        categoriesMap[normalizedCat].count += 1;
      });
    });
  }

  const categoryKeys = Object.keys(categoriesMap);
  
  // Check for blacklist information from OCR
  let blacklistDetected = false;
  if (result.ocr_results && result.ocr_results.blacklist_score > 0) {
    blacklistDetected = true;
    const blacklistInfo = result.ocr_results.blacklist_info;
    categoriesMap['Blacklist'] = {
      name: 'Blacklisted Account',
      messages: [`${blacklistInfo.name} (${blacklistInfo.report_count} reports)`],
      messageSet: new Set([`${blacklistInfo.name} (${blacklistInfo.report_count} reports)`]),
      count: 1
    };
  }

  if (categoryKeys.length === 0 && !blacklistDetected) {
    const noneDiv = document.createElement('div');
    noneDiv.className = 'category-item';
    const p = document.createElement('p');
    p.className = 'category-name';
    p.textContent = 'No suspicious factors detected';
    noneDiv.appendChild(p);
    categoriesContainer.appendChild(noneDiv);
  } else {
    // Re-get category keys after potentially adding blacklist
    const allCategoryKeys = Object.keys(categoriesMap);
    allCategoryKeys.forEach((key) => {
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

        categoryData.messages.forEach((msg) => {
          const li = document.createElement('li');
          const wrapper = document.createElement('div');
          wrapper.className = 'message-wrapper';

          const msgText = document.createElement('span');
          msgText.className = 'message-text full';
          msgText.textContent = msg;
          wrapper.appendChild(msgText);

          li.appendChild(wrapper);
          messagesList.appendChild(li);
        });

        categoryDiv.appendChild(messagesList);
      }

      categoriesContainer.appendChild(categoryDiv);
    });
  }
  
  // Remove old blacklist display code (replaced by categoriesMap integration above)
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

// Scan image UI removed: popup uses auto-analysis only