let currentTabId = null;
let lastRenderedState = {};
const $ = (id) => document.getElementById(id);
const btnStart = $('btnStart');
const btnStop = $('btnStop');
const btnExport = $('btnExport');
const btnAutoStart = $('btnAutoStart');
const btnResume = $('btnResume');
const btnClear = $('btnClear');
const btnDiscardSession = $('btnDiscardSession');
const urlListText = $('urlList');
const statusText = $('statusText');

function render(state = {}) {
  state = { ...lastRenderedState, ...state };
  lastRenderedState = state;
  const count = state.count || state.savedCount || 0;
  const running = Boolean(state.running || state.autoRunning);
  $('currentCount').textContent = count.toLocaleString('vi-VN');
  $('runState').textContent = running ? 'Đang chạy' : (state.hasCheckpoint ? 'Đã lưu' : 'Sẵn sàng');
  $('sessionBadge').textContent = state.hasCheckpoint ? `Đã lưu ${count} profile` : 'Chưa có phiên lưu';
  btnStart.disabled = running;
  btnStart.textContent = state.hasCheckpoint ? 'Tiếp tục phiên này' : 'Bắt đầu cào';
  btnStop.disabled = !running;
  btnExport.disabled = count === 0;
  btnExport.textContent = `Xuất CSV (${count.toLocaleString('vi-VN')})`;
  btnDiscardSession.style.display = state.hasCheckpoint && !running ? 'block' : 'none';

  const hasBatch = Boolean(state.hasSavedData);
  btnResume.style.display = hasBatch && !state.autoRunning ? 'block' : 'none';
  btnClear.style.display = hasBatch && !state.autoRunning ? 'block' : 'none';
  if (hasBatch) btnResume.textContent = `Tiếp tục link ${(state.savedIndex || 0) + 1}/${state.savedTotal || 0}`;

  if (state.autoRunning) {
    statusText.textContent = `Đang cào hàng loạt: ${state.currentIndex || 0}/${state.totalUrls || 0} link • ${count} profile • khoảng 300–350/trang.`;
  } else {
    statusText.textContent = state.status || (state.hasCheckpoint
      ? `Phiên tạm đã sẵn sàng. Bấm “Tiếp tục phiên này” để chạy từ vị trí đã lưu.`
      : 'Sẵn sàng. Dữ liệu sẽ tự động lưu sau mỗi batch.');
  }
}

function sendTab(action, cb, allowInject = true) {
  if (currentTabId == null) return;
  chrome.tabs.sendMessage(currentTabId, { action }, (res) => {
    const messageError = chrome.runtime.lastError;
    if (!messageError) {
      if (cb) cb(res || {});
      return;
    }

    if (!allowInject) {
      statusText.textContent = 'Không thể kết nối. Hãy kiểm tra tab hiện tại đang mở facebook.com.';
      return;
    }

    statusText.textContent = 'Đang kết nối extension với trang Facebook...';
    chrome.scripting.executeScript({
      target: { tabId: currentTabId },
      files: ['content.js']
    }, () => {
      if (chrome.runtime.lastError) {
        statusText.textContent = 'Không thể chạy trên tab này. Hãy mở facebook.com rồi thử lại.';
        return;
      }
      setTimeout(() => sendTab(action, cb, false), 150);
    });
  });
}

function sendBackground(action, data = {}, cb) {
  chrome.runtime.sendMessage({ action, ...data, tabId: currentTabId }, (res) => {
    if (cb) cb(res || {});
  });
}

chrome.tabs.query({ active:true, currentWindow:true }, (tabs) => {
  if (!tabs[0]) return;
  currentTabId = tabs[0].id;
  sendTab('GET_STATE', (contentState) => {
    sendBackground('GET_BACKGROUND_STATE', {}, (batchState) => render({ ...contentState, ...batchState,
      count: contentState.count || batchState.count || 0,
      status: contentState.status,
      hasCheckpoint: contentState.hasCheckpoint
    }));
  });
});

btnStart.addEventListener('click', () => sendTab('START', render));
btnStop.addEventListener('click', () => {
  sendBackground('STOP_AUTO');
  sendTab('STOP', render);
});
btnExport.addEventListener('click', () => {
  if ((lastRenderedState.totalUrls || 0) > 0 && (lastRenderedState.count || 0) > 0) {
    sendBackground('RESCUE_DATA', {}, render);
  } else {
    sendTab('EXPORT');
  }
});
btnDiscardSession.addEventListener('click', () => {
  if (confirm('Xóa dữ liệu tạm của trang hiện tại?')) sendTab('CLEAR_CHECKPOINT', render);
});
const linkFile = $("linkFile");
linkFile.addEventListener("change", async () => {
  const file = linkFile.files && linkFile.files[0];
  if (!file) return;
  const text = await file.text();
  const urls = [...new Set(text.split(/\r?\n/).map((u) => u.trim()).filter((u) => /^https?:\/\/(www\.)?facebook\.com\//i.test(u)))];
  urlListText.value = urls.join("\n");
  statusText.textContent = `Đã nạp ${urls.length.toLocaleString("vi-VN")} link từ ${file.name}.`;
});

btnAutoStart.addEventListener('click', () => {
  const urls = [...new Set(urlListText.value.split('\n').map((u) => u.trim()).filter(Boolean))];
  if (!urls.length) return alert('Vui lòng nhập ít nhất một link.');
  if (confirm('Bắt đầu danh sách mới sẽ thay thế phiên hàng loạt cũ. Tiếp tục?')) {
    statusText.textContent = 'Đang chuẩn bị phiên hàng loạt...';
    sendBackground('START_AUTO', { urls }, render);
  }
});
btnResume.addEventListener('click', () => sendBackground('RESUME_AUTO', {}, render));
btnClear.addEventListener('click', () => {
  if (confirm('Xóa toàn bộ phiên hàng loạt đang lưu?')) sendBackground('CLEAR_DATA', {}, render);
});

chrome.runtime.onMessage.addListener((msg) => {
  if (msg.action === 'STATE' || msg.action === 'AUTO_STATE') render(msg.state);
  if (msg.action === 'PROGRESS') statusText.textContent = msg.message;
});
