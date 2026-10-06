document.getElementById('scan-btn').addEventListener('click', async () => {
  const btn = document.getElementById('scan-btn');
  const resultsDiv = document.getElementById('results');
  const errorDiv = document.getElementById('error-msg');
  
  btn.classList.add('loading');
  resultsDiv.classList.add('hidden');
  errorDiv.classList.add('hidden');

  try {
    const [tab] = await chrome.tabs.query({ active: true, currentWindow: true });
    
    // Tiêm content script vào tab hiện tại
    chrome.scripting.executeScript({
      target: { tabId: tab.id },
      files: ['content.js']
    }, () => {
      // Gửi message báo hiệu bắt đầu quét
      chrome.tabs.sendMessage(tab.id, { action: "scan_intent" }, (response) => {
        btn.classList.remove('loading');
        
        if (chrome.runtime.lastError) {
          errorDiv.textContent = "Không thể quét trang này (có thể là trang cài đặt Chrome hoặc Store).";
          errorDiv.classList.remove('hidden');
          return;
        }

        if (response && response.success) {
          updateBadge('res-dogs', response.data.sells_dogs);
          updateBadge('res-form', response.data.has_form);
          updateBadge('res-kit', response.data.has_take_home_kit);
          resultsDiv.classList.remove('hidden');
        } else {
          errorDiv.textContent = response?.error || "Không có phản hồi từ trang web.";
          errorDiv.classList.remove('hidden');
        }
      });
    });
  } catch (error) {
    btn.classList.remove('loading');
    errorDiv.textContent = error.message;
    errorDiv.classList.remove('hidden');
  }
});

function updateBadge(elementId, isYes) {
  const badge = document.querySelector(`#${elementId} .badge`);
  badge.textContent = isYes ? "CÓ" : "KHÔNG";
  badge.className = `badge ${isYes ? 'yes' : 'no'}`;
}
