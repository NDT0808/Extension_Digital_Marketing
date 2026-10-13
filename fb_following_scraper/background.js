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
  try {
    chrome.storage.local.set({
      urlList: urlList,
      currentIndex: currentIndex,
      allData: allData,
      isAutoRunning: isAutoRunning,
      targetTabId: targetTabId
    }, () => {
      if (chrome.runtime.lastError) {
        console.error("Lỗi khi lưu storage (có thể do dữ liệu quá lớn):", chrome.runtime.lastError);
      }
    });
  } catch (e) {
    console.error("Lỗi Exception khi lưu state:", e);
  }
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
      exportAllData(false, msg.tabId);
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
  else if (msg.action === 'RELOAD_CURRENT_PAGE') {
    if (sender && sender.tab) {
      chrome.tabs.reload(sender.tab.id);
    } else if (targetTabId) {
      chrome.tabs.reload(targetTabId);
    }
    sendResponse({status: "reloading"});
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
    
    let waitTime = 1000;

    saveState();
    pushAutoState();
    
    setTimeout(() => {
        try {
            processNext();
        } catch(e) {
            console.error("Lỗi trong processNext:", e);
        }
    }, waitTime);
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
  try {
    chrome.runtime.sendMessage({ action: 'AUTO_STATE', state: getAutoState() }).catch((e) => {
      // Bỏ qua lỗi kết nối
    });
  } catch (e) {
    console.error("Lỗi khi pushAutoState:", e);
  }
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
  let targetUrl = originalUrl;
  
  if (originalUrl.includes("profile.php?id=")) {
    if (!originalUrl.includes('sk=following') && !originalUrl.includes('sk=followers')) {
      const joiner = originalUrl.includes('?') ? '&' : '?';
      targetUrl = originalUrl + joiner + 'sk=followers';
    }
  } else {
    if (!/\/(following|followers)(\/?)$/i.test(originalUrl)) {
      if (originalUrl.endsWith("/")) originalUrl = originalUrl.slice(0, -1);
      targetUrl = originalUrl + '/followers';
    }
  }
  
  chrome.tabs.update(targetTabId, { url: 'about:blank' }, () => {
    setTimeout(() => {
      chrome.tabs.update(targetTabId, { url: targetUrl }, (tab) => {
        setTimeout(() => {
          chrome.tabs.sendMessage(targetTabId, { action: 'START_AUTO_MODE' }, (res) => {
             if (chrome.runtime.lastError) {
                 console.log("Tab không phản hồi, bỏ qua trang...");
                 setTimeout(() => {
                     handleAutoFinished([]); 
                 }, 1000);
             }
          });
        }, 1800);
      });
    }, 500);
  });
}

function exportAllData(isPartial = false, fallbackTabId = null) {
  const tId = fallbackTabId || targetTabId;
  if (tId) {
    // Tránh gửi chuỗi JSON hàng chục MB qua sendMessage (Chrome sẽ block nếu quá 64MB)
    // Chỉ gửi lệnh, Content Script sẽ tự đọc từ Local Storage
    chrome.tabs.sendMessage(tId, { action: 'FORCE_DOWNLOAD_FROM_STORAGE', isPartial: isPartial }).catch(()=>{});
  }
}
