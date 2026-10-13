let urlList = [];
let currentIndex = 0;
let startIndex = 0;
let endIndex = -1;
let allData = [];
let isAutoRunning = false;
let isPaused = false;
let targetTabId = null;
let statusMessage = "Sẵn sàng";

// Khóa chống trùng lặp và đa luồng
let currentTaskId = null;
let isProcessing = false;
let nextTimer = null;

function clearNextTimer() {
  if (nextTimer) {
    clearTimeout(nextTimer);
    nextTimer = null;
  }
}

function scheduleNext(delayMs = 1500) {
  clearNextTimer();
  nextTimer = setTimeout(() => {
    processNext();
  }, delayMs);
}

function saveState() {
  chrome.storage.local.set({
    fb_publish_state: {
      urlList,
      currentIndex,
      startIndex,
      endIndex,
      allData,
      isAutoRunning,
      isPaused,
      statusMessage
    }
  });
  broadcastState();
}

function loadState(cb) {
  chrome.storage.local.get(['fb_publish_state'], (res) => {
    if (res.fb_publish_state) {
      const s = res.fb_publish_state;
      urlList = s.urlList || [];
      currentIndex = s.currentIndex !== undefined ? s.currentIndex : 0;
      startIndex = s.startIndex !== undefined ? s.startIndex : 0;
      endIndex = s.endIndex !== undefined ? s.endIndex : -1;
      allData = s.allData || [];
      isAutoRunning = s.isAutoRunning || false;
      isPaused = s.isPaused || false;
      statusMessage = s.statusMessage || "Sẵn sàng";
    }
    if (cb) cb();
  });
}

function broadcastState() {
  chrome.runtime.sendMessage({
    action: 'STATE_UPDATED',
    state: {
      urlList,
      currentIndex,
      startIndex,
      endIndex,
      allData,
      isAutoRunning,
      isPaused,
      statusMessage
    }
  }).catch(() => {});
}

chrome.runtime.onMessage.addListener((msg, sender, sendResponse) => {
  if (msg.action === 'GET_STATE') {
    sendResponse({
      urlList,
      currentIndex,
      startIndex,
      endIndex,
      allData,
      isAutoRunning,
      isPaused,
      statusMessage
    });
  }
  else if (msg.action === 'START_AUTO') {
    clearNextTimer();
    isProcessing = false;
    currentTaskId = null;

    urlList = msg.urls;
    startIndex = (msg.startIndex !== undefined && msg.startIndex >= 0) ? msg.startIndex : 0;
    endIndex = (msg.endIndex !== undefined && msg.endIndex >= 0 && msg.endIndex < urlList.length)
      ? msg.endIndex
      : (urlList.length - 1);

    currentIndex = startIndex;
    allData = []; // Bắt đầu mới, reset dữ liệu
    targetTabId = msg.tabId;
    isAutoRunning = true;
    isPaused = false;
    statusMessage = `Đang bắt đầu cào từ dòng ${startIndex + 1} đến ${endIndex + 1}...`;
    saveState();
    sendResponse({ status: 'ok' });
    processNext();
  }
  else if (msg.action === 'RESUME_AUTO') {
    clearNextTimer();
    isProcessing = false;
    currentTaskId = null;

    if (endIndex < 0 || endIndex >= urlList.length) {
      endIndex = urlList.length - 1;
    }

    if (currentIndex > endIndex || currentIndex >= urlList.length) {
      statusMessage = "Danh sách đã cào xong. Vui lòng chọn khoảng mới hoặc Bắt đầu cào mới.";
      isAutoRunning = false;
      isPaused = false;
      saveState();
      sendResponse({ status: 'finished' });
      return;
    }

    if (msg.tabId) targetTabId = msg.tabId;
    isAutoRunning = true;
    isPaused = false;
    statusMessage = `Tiếp tục chạy từ dòng ${currentIndex + 1} đến ${endIndex + 1}...`;
    saveState();
    sendResponse({ status: 'ok' });
    processNext();
  }
  else if (msg.action === 'STOP_AUTO') {
    clearNextTimer();
    isProcessing = false;
    currentTaskId = null;
    isAutoRunning = false;
    isPaused = true;
    statusMessage = `Đã tạm dừng tại dòng ${currentIndex + 1}/${urlList.length}. Bấm "Tiếp tục" để chạy từ dòng ${currentIndex + 1} hoặc "Xuất file CSV".`;
    saveState();
    sendResponse({ status: 'ok' });
  }
  else if (msg.action === 'CLEAR_DATA') {
    clearNextTimer();
    isProcessing = false;
    currentTaskId = null;
    allData = [];
    currentIndex = 0;
    startIndex = 0;
    endIndex = -1;
    isAutoRunning = false;
    isPaused = false;
    statusMessage = "Đã làm mới dữ liệu.";
    saveState();
    sendResponse({ status: 'ok' });
  }
  else if (msg.action === 'EXPORT_DATA') {
    exportCSV(true);
    sendResponse({ status: 'ok' });
  }
  else if (msg.action === 'PROFILE_RESULT') {
    if (isAutoRunning) {
      let item = msg.data || {};

      // KHÓA CHỐNG TRÙNG LẶP #1: Chỉ chấp nhận tin nhắn khớp đúng currentTaskId hiện tại
      if (!currentTaskId || item.taskId !== currentTaskId) {
        console.warn(`[BG] Bỏ qua kết quả trùng lặp/quá hạn (item: ${item.taskId}, current: ${currentTaskId})`);
        sendResponse({ status: 'ignored' });
        return;
      }

      // Hủy currentTaskId ngay lập tức để không tin nhắn trùng nào lọt qua được
      currentTaskId = null;
      isProcessing = false;
      item.stt = currentIndex + 1;
      allData.push(item);

      let timePreview = item.publishTime
        ? `${item.publishTime} (${item.relativeTime || ''})`
        : 'Không tìm thấy bài viết';
      statusMessage = `[Dòng ${currentIndex + 1}] ${item.name || 'Profile'}: ${timePreview}`;

      currentIndex++;
      saveState();

      // Nghỉ 1.5s trước khi mở link tiếp theo
      scheduleNext(1500);
    }
    sendResponse({ status: 'ok' });
  }
  return true;
});

function processNext() {
  if (!isAutoRunning) {
    isProcessing = false;
    return;
  }

  if (currentIndex > endIndex || currentIndex >= urlList.length) {
    isAutoRunning = false;
    isPaused = false;
    isProcessing = false;
    currentTaskId = null;
    statusMessage = `Đã hoàn thành! Đã cào xong ${allData.length} link.`;
    saveState();
    exportCSV(false);
    return;
  }

  // Khóa chống nhiều luồng chạy cùng lúc
  if (isProcessing) {
    console.warn("[BG] Đang xử lý link khác, bỏ qua gọi processNext trùng.");
    return;
  }
  isProcessing = true;

  let targetUrl = urlList[currentIndex];
  let taskId = `${currentIndex}_${Date.now()}`;
  currentTaskId = taskId;

  statusMessage = `Đang mở dòng ${currentIndex + 1}/${endIndex + 1}: ${targetUrl}`;
  saveState();

  // Reset tab via about:blank rồi nạp link profile mới
  chrome.tabs.update(targetTabId, { url: 'about:blank' }, () => {
    setTimeout(() => {
      chrome.tabs.update(targetTabId, { url: targetUrl }, (tab) => {
        // Chờ 3.5s để Facebook nạp DOM đầu trang
        setTimeout(() => {
          if (!isAutoRunning || currentTaskId !== taskId) {
            isProcessing = false;
            return;
          }

          chrome.tabs.sendMessage(targetTabId, {
            action: 'START_SCRAPE',
            stt: currentIndex + 1,
            targetUrl: targetUrl,
            taskId: taskId
          }, (res) => {
            if (chrome.runtime.lastError) {
              console.log("Tab chưa sẵn sàng, thử inject script an toàn...");
              chrome.scripting.executeScript({
                target: { tabId: targetTabId },
                files: ['content.js']
              }, () => {
                setTimeout(() => {
                  if (!isAutoRunning || currentTaskId !== taskId) {
                    isProcessing = false;
                    return;
                  }

                  chrome.tabs.sendMessage(targetTabId, {
                    action: 'START_SCRAPE',
                    stt: currentIndex + 1,
                    targetUrl: targetUrl,
                    taskId: taskId
                  }).catch(() => {
                    // Nếu vẫn không phản hồi, ghi nhận lỗi 1 lần duy nhất
                    if (currentTaskId === taskId) {
                      currentTaskId = null;
                      isProcessing = false;

                      allData.push({
                        stt: currentIndex + 1,
                        url: targetUrl,
                        name: 'Lỗi nạp trang',
                        publishTime: 'Không thể truy cập',
                        publishTimestamp: '',
                        relativeTime: ''
                      });
                      currentIndex++;
                      saveState();
                      scheduleNext(1500);
                    }
                  });
                }, 1000);
              });
            }
          });
        }, 3500);
      });
    }, 300);
  });
}

function exportCSV(isPartial = false) {
  if (!allData || allData.length === 0) return;

  let headers = ['STT', 'URL', 'Tên Profile/Fanpage', 'Thời gian đăng (Publish Time)', 'Timestamp', 'Thời gian tương đối'];
  let csvRows = ["\uFEFF" + headers.join(',')];

  allData.forEach((row, idx) => {
    let stt = row.stt !== undefined ? row.stt : (idx + 1);
    let vals = [
      `"${String(stt).replace(/"/g, '""')}"`,
      `"${String(row.url || '').replace(/"/g, '""')}"`,
      `"${String(row.name || '').replace(/"/g, '""')}"`,
      `"${String(row.publishTime || '').replace(/"/g, '""')}"`,
      `"${String(row.publishTimestamp || '').replace(/"/g, '""')}"`,
      `"${String(row.relativeTime || '').replace(/"/g, '""')}"`
    ];
    csvRows.push(vals.join(','));
  });

  let csvContent = csvRows.join('\r\n');
  let base64Content = btoa(unescape(encodeURIComponent(csvContent)));
  let dataUrl = 'data:text/csv;charset=utf-8;base64,' + base64Content;
  let filename = `FB_PublishTime_${isPartial ? 'Part_' : ''}${Date.now()}.csv`;

  if (chrome.downloads && chrome.downloads.download) {
    chrome.downloads.download({
      url: dataUrl,
      filename: filename,
      saveAs: false
    }).catch(() => {
      if (targetTabId) {
        chrome.tabs.sendMessage(targetTabId, { action: 'TRIGGER_DOWNLOAD', data: allData, isPartial }).catch(() => {});
      }
    });
  } else if (targetTabId) {
    chrome.tabs.sendMessage(targetTabId, { action: 'TRIGGER_DOWNLOAD', data: allData, isPartial }).catch(() => {});
  }
}

loadState();
