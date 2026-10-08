let isAutoRunning = false;
let urlList = [];
let currentIndex = 0;
let allData = [];
let targetTabId = null;

async function loadState() {
  return new Promise(resolve => {
    chrome.storage.local.get(['urlList', 'currentIndex', 'allData', 'isAutoRunning', 'targetTabId'], (result) => {
      if (result.urlList && result.urlList.length > 0) {
        urlList = result.urlList;
        currentIndex = result.currentIndex || 0;
        allData = result.allData || [];
        isAutoRunning = result.isAutoRunning || false;
        targetTabId = result.targetTabId || null;
      }
      resolve();
    });
  });
}

function saveState() {
  chrome.storage.local.set({
    urlList: urlList,
    currentIndex: currentIndex,
    allData: allData,
    isAutoRunning: isAutoRunning,
    targetTabId: targetTabId
  });
}

// Chạy loadState một lần khi script khởi động
loadState().then(() => {
  // Tự động chạy tiếp vòng lặp nếu trạng thái là đang chạy (VD: Vừa tải lại tiện ích)
  if (isAutoRunning && targetTabId) {
    processNext();
  }
});

chrome.runtime.onMessage.addListener((msg, sender, sendResponse) => {
  if (msg.action === 'START_AUTO') {
    urlList = msg.urls;
    currentIndex = 0;
    allData = [];
    isAutoRunning = true;
    targetTabId = msg.tabId;
    
    saveState();
    pushAutoState();
    processNext();
    sendResponse(getAutoState());
  } 
  else if (msg.action === 'RESUME_AUTO') {
    loadState().then(() => {
      targetTabId = msg.tabId;
      isAutoRunning = true;
      saveState();
      pushAutoState();
      processNext();
      sendResponse(getAutoState());
    });
    return true; // Báo hiệu gọi sendResponse bất đồng bộ
  }
  else if (msg.action === 'STOP_AUTO') {
    loadState().then(() => {
      isAutoRunning = false;
      saveState();
      pushAutoState();
      sendResponse(getAutoState());
    });
    return true;
  }
  else if (msg.action === 'CLEAR_DATA') {
    urlList = [];
    currentIndex = 0;
    allData = [];
    isAutoRunning = false;
    chrome.storage.local.clear();
    sendResponse(getAutoState());
  }
  else if (msg.action === 'GET_BACKGROUND_STATE') {
    loadState().then(() => {
      sendResponse(getAutoState());
    });
    return true;
  }
  else if (msg.action === 'RESCUE_DATA') {
    loadState().then(() => {
      exportAllData(false);
    });
    return true;
  }
  else if (msg.action === 'AUTO_FINISHED') {
    // Rất quan trọng: Nếu cào quá lâu (>30s), Chrome sẽ tự động cho Background ngủ (Ngủ đông)
    // Dẫn đến toàn bộ biến lưu trên RAM bị xóa sạch.
    // Phải load lại state từ ổ cứng (Local Storage) trước khi xử lý tiếp
    loadState().then(() => {
      // Khôi phục targetTabId từ tab đã gửi tin nhắn nếu bị mất
      if (!targetTabId && sender && sender.tab) {
        targetTabId = sender.tab.id;
      }
      handleAutoFinished(msg.data);
    });
    return true;
  }
});

function handleAutoFinished(data) {
    if (!isAutoRunning) return;
    if (data) {
      data.forEach(item => {
        item.sourceProfile = urlList[currentIndex];
        allData.push(item);
      });
    }
    currentIndex++;
    
    if (currentIndex % 30 === 0) {
        exportAllData(true); 
    }

    saveState();
    pushAutoState();
    
    const waitTime = Math.floor(Math.random() * (6000 - 3000 + 1)) + 3000;
    setTimeout(processNext, waitTime);
}

function getAutoState() {
  return {
    autoRunning: isAutoRunning,
    currentIndex: currentIndex,
    totalUrls: urlList.length,
    count: allData.length,
    hasSavedData: urlList.length > 0 && currentIndex < urlList.length,
    savedIndex: currentIndex,
    savedTotal: urlList.length
  };
}

function pushAutoState() {
  chrome.runtime.sendMessage({ action: 'AUTO_STATE', state: getAutoState() }).catch(() => {});
}

function processNext() {
  if (!isAutoRunning) return;

  if (currentIndex >= urlList.length) {
    isAutoRunning = false;
    saveState();
    pushAutoState();
    exportAllData(false);
    return;
  }

  let originalUrl = urlList[currentIndex].trim();
  let targetUrl = "";
  
  if (originalUrl.includes("profile.php?id=")) {
    // Tài khoản cá nhân dạng ?id=xxx
    targetUrl = originalUrl + "&sk=following";
  } else if (
    originalUrl.endsWith("/following") || 
    originalUrl.endsWith("/followers") ||
    originalUrl.includes("/followers/") ||
    originalUrl.includes("/following/")
  ) {
    // URL đã chỉ định rõ trang following/followers rồi -> dùng thẳng
    targetUrl = originalUrl;
  } else {
    // Tài khoản cá nhân dạng /username -> thêm /following
    if (originalUrl.endsWith("/")) originalUrl = originalUrl.slice(0, -1);
    targetUrl = originalUrl + "/following";
  }
  
  chrome.tabs.update(targetTabId, { url: targetUrl }, (tab) => {
    setTimeout(() => {
      chrome.tabs.sendMessage(targetTabId, { action: 'START_AUTO_MODE' }, (res) => {
         if (chrome.runtime.lastError) {
             console.log("Tab không phản hồi, bỏ qua trang...");
             setTimeout(() => {
                 handleAutoFinished([]); 
             }, 2000);
         }
      });
    }, 5500);
  });
}

function exportAllData(isPartial = false) {
  if (targetTabId) {
    // Tránh gửi chuỗi JSON hàng chục MB qua sendMessage (Chrome sẽ block nếu quá 64MB)
    // Chỉ gửi lệnh, Content Script sẽ tự đọc từ Local Storage
    chrome.tabs.sendMessage(targetTabId, { action: 'FORCE_DOWNLOAD_FROM_STORAGE', isPartial: isPartial }).catch(()=>{});
  }
}
