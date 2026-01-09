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
  
  // Log QR detection
  if (result.qr_results && result.qr_results.decoded_payloads && result.qr_results.decoded_payloads.length > 0) {
    console.log('🔍 QR Codes Detected:', result.qr_results.decoded_payloads);
    console.log('🎯 QR Risk Score:', result.qr_results.risk_score);
    console.log('🚩 QR Flags:', result.qr_results.flags);
  }
  
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

  // Track if we have any QR detections
  let hasQRDetection = false;

  // Check for QR-specific results and display them first
  if (result.qr_results && result.qr_results.decoded_payloads && result.qr_results.decoded_payloads.length > 0) {
    console.log('[Unscamable] Displaying QR results');
    hasQRDetection = true;
    const qrDiv = document.createElement('div');
    qrDiv.className = 'category-item';
    
    const qrName = document.createElement('p');
    qrName.className = 'category-name';
    qrName.textContent = 'Blacklist Detected';
    qrDiv.appendChild(qrName);
    
    const qrCountDiv = document.createElement('div');
    qrCountDiv.className = 'message-count';
    qrCountDiv.textContent = `Detected in 1 QR code(s)`;
    qrDiv.appendChild(qrCountDiv);
    
    categoriesContainer.appendChild(qrDiv);
  }

  // Build categories map focused on the snippets tied to each category
  const categoriesMap = {};

  // Robustly collect matched keywords from multiple possible response locations
  const collectMatchedKeywords = () => {
    const buckets = [];
    if (result.analysis) buckets.push(result.analysis.matched_keywords, result.analysis.chat_report && result.analysis.chat_report.matched_keywords);
    if (result.chat_report) buckets.push(result.chat_report.matched_keywords);
    if (result.matched_keywords) buckets.push(result.matched_keywords);
    const merged = {};
    buckets.forEach((bk) => {
      if (!bk) return;
      Object.entries(bk).forEach(([cat, kws]) => {
        if (!merged[cat]) merged[cat] = new Set();
        (kws || []).forEach((kw) => {
          const cleanKw = (kw || '').trim();
          if (cleanKw) merged[cat].add(cleanKw);
        });
      });
    });
    return Object.fromEntries(Object.entries(merged).map(([cat, set]) => [cat, Array.from(set)]));
  };

  const matchedKeywords = collectMatchedKeywords();

  // Prefer server-provided matched keywords to show exact triggers
  Object.entries(matchedKeywords).forEach(([cat, keywords]) => {
    if (!categoriesMap[cat]) {
      categoriesMap[cat] = { name: cat, messages: [], messageSet: new Set(), count: 0 };
    }
    (keywords || []).forEach((kw) => {
      const cleanKw = (kw || '').trim();
      if (!cleanKw) return;
      if (!categoriesMap[cat].messageSet.has(cleanKw)) {
        categoriesMap[cat].messageSet.add(cleanKw);
        categoriesMap[cat].messages.push(cleanKw);
      }
      categoriesMap[cat].count += 1;
    });
  });
  const CATEGORY_KEYWORDS = {
     "Urgency": ["ด่วน", "เร่งด่วน", "ภายใน 24 ชั่วโมง", "ทันที", "วันนี้เท่านั้น", "หมดอายุวันนี้", "ครั้งสุดท้าย", "สุดท้าย", "จะถูกระงับ", "ถูกระงับ", "ระงับบัญชี", "ระงับบริการ", "ถูกปิดใช้งาน", "ลงทะเบียนด่วน"],
     "Identity Threat": ["บัญชีของคุณ", "บัญชีของท่าน", "ยืนยันตัวตน", "ตรวจสอบตัวตน", "รหัส OTP", "ยืนยันความปลอดภัย", "ระบบตรวจพบ", "การเข้าถึงผิดปกติ", "บัญชีถูกแฮก", "ระงับบัญชีชั่วคราว"],
     "Financial Pressure": ["ยอดค้างชำระ", "ค้างชำระ", "ค่าปรับ", "ค่าธรรมเนียม", "หนี้ค้าง", "ชำระเงิน", "โอนเงิน", "จ่ายบิล", "โอนเงินผิดปกติ", "คืนเงิน", "โอนเงินคืน", "ใบสั่งออนไลน์", "ชำระค่าปรับ", "วงเงินเหลือ", "ค่าไฟฟ้า", "ค่าปรับจราจร"],
     "Authority": ["ตำรวจ", "เจ้าหน้าที่", "กรม", "กระทรวง", "ฝ่ายความปลอดภัย", "ศาล", "หมายศาล", "คดีความ", "ปปง.", "เงินเยียวยา", "สิทธิ์รัฐ", "ธนาคาร", "ศูนย์บริการ", "ฝ่ายกฎหมาย", "ฝ่าย กฎหมาย"],
     "Delivery Scams": ["พัสดุ", "ขนส่ง", "จัดส่ง", "เลขแทรกกิ้ง", "ติดต่อผู้รับไม่ได้", "ยืนยันการจัดส่ง", "ไม่สามารถจัดส่ง", "เช็กสถานะ"],
     "Promotional Bait": ["ได้รับรางวัล", "iPhone", "โปรโมชั่น", "โปรเด็ด", "โปรพิเศษ", "ฝาก100รับ200", "เงินคืน", "กำไรการันตี", "ลงทุนน้อย", "งานพาร์ทไทม์", "รายได้ดี", "รับของรางวัล", "แบบสอบถาม", "ฟรี", "ระบบออโต้", "ไม่มีขั้นต่ำ"],
     "Link Requests": ["คลิกลิงก์", "กดลิงก์", "ตรวจสอบที่", "ตรวจสอบเลย", "ติดต่อด่วน", "ติดต่อเจ้าหน้าที่", "แอดไลน์", "คลิกยืนยัน", "เพื่อตรวจสอบ"],
     "Suspicious URL": [],
     "Money Mentions": []
  };

  const focusSnippet = (cat, text) => {
    const keywords = CATEGORY_KEYWORDS[cat];
    if (!keywords || !text) return text;
    
    // Remove quotes if present
    const cleanText = text.replace(/^["']|["']$/g, '');
    
    // Find and return the first matching keyword only
    for (const kw of keywords) {
      if (cleanText.includes(kw)) {
        return kw;
      }
    }
    
    // If no keyword found, return the original text (shouldn't happen)
    return cleanText;
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
        const snippet = parts[1] || '';
        const categories = categoryPart.split(',').map((c) => c.trim()).filter(Boolean);
        categories.forEach((cat) => {
          if (!categoriesMap[cat]) {
            categoriesMap[cat] = { name: cat, messages: [], messageSet: new Set(), count: 0 };
          }
          const focused = focusSnippet(cat, snippet);
          if (!shouldSkipSnippet(focused) && !categoriesMap[cat].messageSet.has(focused)) {
            categoriesMap[cat].messageSet.add(focused);
            categoriesMap[cat].messages.push(focused);
          }
          categoriesMap[cat].count += 1;
        });
      } else if (flag.includes(': detected in')) {
        const match = flag.match(/^(.+?):\s+detected in (\d+) message\(s\)$/);
        if (match) {
          const cat = match[1];
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
        if (!categoriesMap[cat]) {
          categoriesMap[cat] = { name: cat, messages: [], messageSet: new Set(), count: 0 };
        }
        const focused = focusSnippet(cat, text);
        if (!shouldSkipSnippet(focused) && !categoriesMap[cat].messageSet.has(focused)) {
          categoriesMap[cat].messageSet.add(focused);
          categoriesMap[cat].messages.push(focused);
        }
        categoriesMap[cat].count += 1;
      });
    });
  }

  const categoryKeys = Object.keys(categoriesMap);

  // Only show "No suspicious factors detected" if there are no categories AND no QR detections
  if (categoryKeys.length === 0 && !hasQRDetection) {
    const noneDiv = document.createElement('div');
    noneDiv.className = 'category-item';
    const p = document.createElement('p');
    p.className = 'category-name';
    p.textContent = 'No suspicious factors detected';
    noneDiv.appendChild(p);
    categoriesContainer.appendChild(noneDiv);
  } else if (categoryKeys.length > 0) {
    categoryKeys.forEach((key) => {
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

      // Count info removed per user request
      // const countDiv = document.createElement('div');
      // countDiv.className = 'message-count';
      // countDiv.textContent = categoryData.count > 0
      //   ? `Detected in ${categoryData.count} message(s)`
      //   : 'Detected';
      // categoryDiv.appendChild(countDiv);

      categoriesContainer.appendChild(categoryDiv);
    });
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
            console.log('[Unscamable] Requesting screenshot from service worker with tab ID:', tab.id);
            
            // Ask service worker to capture screenshot with specific tab ID
            let screenshotData = '';
            try {
              screenshotData = await new Promise((resolve, reject) => {
                chrome.runtime.sendMessage({ action: 'captureScreenshot', tabId: tab.id }, (response) => {
                  if (chrome.runtime.lastError) {
                    console.warn('[Unscamable] Screenshot request error:', chrome.runtime.lastError.message);
                    reject(chrome.runtime.lastError);
                  } else if (response && response.screenshot) {
                    console.log('[Unscamable] Screenshot received:', response.screenshot.length, 'bytes');
                    resolve(response.screenshot);
                  } else {
                    console.warn('[Unscamable] No screenshot in response');
                    resolve('');
                  }
                });
              });
            } catch (captureError) {
              console.warn('[Unscamable] Failed to get screenshot from service worker:', captureError?.message || captureError);
              screenshotData = '';
            }

            console.log('[Unscamable] Sending analysis request with image:', screenshotData ? screenshotData.length + ' bytes' : 'empty');
            const serverResponse = await fetch('http://localhost:5000/analyze', {
              method: 'POST',
              headers: { 'Content-Type': 'application/json' },
              body: JSON.stringify({ text: response.text, image: screenshotData })
            });

            const result = await serverResponse.json();
            console.log('[Unscamable] Backend response:', result);
            
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