import re

with open('c:/Users/ASUS/Downloads/Marketing_Pet&Grass/intent_detector_extension/dashboard.js', 'r', encoding='utf-8') as f:
    content = f.read()

# Fix the broken function
new_reset = """function triggerScriptInjection(tabId) {
  if (!activeTabs.has(tabId)) return;
  const state = activeTabs.get(tabId);
  
  if (state.isProcessingStep) return;
  state.isProcessingStep = true;
  
  const statusTd = document.getElementById(`status-${state.item.index}`);
  if (state.step === 0) {
     statusTd.innerHTML = `<span class="status loading">Đang từ từ cuộn đọc trang chủ...</span>`;
  } else {
     statusTd.innerHTML = `<span class="status loading">Đang lướt đọc trang con (${state.step}/${state.subpages.length})...</span>`;
  }

  // Chờ 1 giây để trang load thêm JS
  setTimeout(() => {
    chrome.scripting.executeScript({
      target: { tabId: tabId },
      files: ['content.js']
    }, () => {
      if (chrome.runtime.lastError) {
        finishTab(tabId, false, "Không thể truy cập (Lỗi Web/SSL/DNS)");
        return;
      }
      
      // Kích hoạt việc cuộn trang và đọc data
      chrome.tabs.sendMessage(tabId, { action: "scan_page_step" }, (response) => {
        if (!activeTabs.has(tabId)) return; // Nếu đã bị timeout
        state.isProcessingStep = false;
        
        if (chrome.runtime.lastError) {
          finishTab(tabId, false, "Không có phản hồi từ web (Có thể web sập)");
          return;
        }
        
        if (response && response.success) {
          handleStepResult(tabId, state, response.data);
        } else {
          finishTab(tabId, false, response?.error || "Lỗi kịch bản cuộn");
        }
      });
    });
  }, 1500);
}

function resetTabTimeout(tabId, ms) {
  const state = activeTabs.get(tabId);
  if (!state) return;
  if (state.timeoutId) clearTimeout(state.timeoutId);
  if (state.forceReadId) clearTimeout(state.forceReadId);
  
  // Ép đọc trang sau 12 giây nếu trang web load quá lâu không chịu complete
  state.forceReadId = setTimeout(() => {
    if (activeTabs.has(tabId)) {
      triggerScriptInjection(tabId);
    }
  }, 12000);

  state.timeoutId = setTimeout(() => {
    if (activeTabs.has(tabId)) {
      finishTab(tabId, false, "Timeout: Web tải quá chậm");
    }
  }, ms);
}
"""

# Find the broken block and replace it
# The broken block starts with "function triggerScriptInjection(tabId)" and ends before chrome.tabs.onUpdated
pattern = re.compile(r'function triggerScriptInjection\(tabId\).*?(?=// Lắng nghe khi tab tải xong để bơm script)', re.DOTALL)
if pattern.search(content):
    content = pattern.sub(new_reset + '\n', content)
    with open('c:/Users/ASUS/Downloads/Marketing_Pet&Grass/intent_detector_extension/dashboard.js', 'w', encoding='utf-8') as f:
        f.write(content)
    print('Patch applied successfully')
else:
    print('Pattern not found')
