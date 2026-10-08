let currentTabId = null;

const btnStart = document.getElementById('btnStart');
const btnStop = document.getElementById('btnStop');
const btnExport = document.getElementById('btnExport');
const btnAutoStart = document.getElementById('btnAutoStart');
const btnResume = document.getElementById('btnResume');
const btnClear = document.getElementById('btnClear');
const btnRescue = document.getElementById('btnRescue');
const urlListText = document.getElementById('urlList');
const statusDiv = document.getElementById('status');

function render(state) {
  btnStart.disabled = state.running || state.autoRunning;
  btnStop.disabled = !(state.running || state.autoRunning);
  btnExport.disabled = state.count === 0 && !state.autoRunning;
  btnExport.innerText = `Xuất CSV (${state.count || 0})`;
  
  if (state.autoRunning) {
    statusDiv.innerText = `ĐANG CÀO TỰ ĐỘNG: Hoàn thành ${state.currentIndex}/${state.totalUrls} profiles.`;
    statusDiv.style.color = 'green';
  } else {
    statusDiv.innerText = 'Trạng thái: ' + (state.status || (state.running ? 'Đang cào...' : 'Sẵn sàng'));
    statusDiv.style.color = '#555';
  }

  // Xử lý hiển thị nút Resume nếu có dữ liệu lưu tạm
  if (state.hasSavedData && !state.autoRunning) {
      btnResume.style.display = 'block';
      btnClear.style.display = 'block';
      btnResume.innerText = `Tiếp tục cào (Link ${state.savedIndex + 1}/${state.savedTotal})`;
  } else {
      btnResume.style.display = 'none';
      btnClear.style.display = 'none';
  }
}

function send(action, data = {}, cb) {
  if (currentTabId == null) return;
  if (action === 'START_AUTO' || action === 'RESUME_AUTO') {
      chrome.runtime.sendMessage({ action: action, urls: data.urls, tabId: currentTabId }, (res) => {
          if(cb) cb(res);
      });
      return;
  }
  
  chrome.tabs.sendMessage(currentTabId, { action }, (res) => {
    if (chrome.runtime.lastError) {
      statusDiv.innerText = 'Lỗi: hãy mở facebook.com và F5 trang lại.';
      return;
    }
    if (cb) cb(res);
  });
}

chrome.tabs.query({ active: true, currentWindow: true }, (tabs) => {
  if (!tabs[0]) return;
  currentTabId = tabs[0].id;
  
  chrome.runtime.sendMessage({action: 'GET_BACKGROUND_STATE'}, (bState) => {
      if (bState && (bState.autoRunning || bState.hasSavedData)) {
          render(bState);
      } else {
          send('GET_STATE', {}, (res) => res && render(res));
      }
  });
});

btnStart.addEventListener('click', () => send('START', {}, (res) => res && render(res)));
btnStop.addEventListener('click', () => {
    chrome.runtime.sendMessage({action: 'STOP_AUTO'}); 
    send('STOP', {}, (res) => res && render(res));
});
btnExport.addEventListener('click', () => send('EXPORT'));

btnAutoStart.addEventListener('click', () => {
    const urls = urlListText.value.split('\n').map(u => u.trim()).filter(u => u !== '');
    if (urls.length === 0) {
        alert("Vui lòng nhập ít nhất 1 link!");
        return;
    }
    if(confirm("Hành động này sẽ XÓA dữ liệu cũ và bắt đầu lại từ link số 1. Bạn có chắc không?")) {
        statusDiv.innerText = "Chuẩn bị cào tự động hàng loạt...";
        send('START_AUTO', {urls: urls}, (res) => render(res));
    }
});

btnResume.addEventListener('click', () => {
    statusDiv.innerText = "Đang khôi phục dữ liệu...";
    send('RESUME_AUTO', {}, (res) => render(res));
});

btnClear.addEventListener('click', () => {
    if(confirm("Bạn có chắc muốn xóa bộ nhớ tạm? Dữ liệu chưa xuất sẽ bị mất!")) {
        chrome.runtime.sendMessage({action: 'CLEAR_DATA'}, (res) => render(res));
    }
});

btnRescue.addEventListener('click', () => {
    statusDiv.innerText = "Đang lấy dữ liệu kẹt trong ổ cứng...";
    send('FORCE_DOWNLOAD_FROM_STORAGE');
});

chrome.runtime.onMessage.addListener((msg) => {
  if (msg.action === 'STATE') render(msg.state);
  if (msg.action === 'AUTO_STATE') render(msg.state);
  if (msg.action === 'PROGRESS') {
      statusDiv.innerText = msg.message;
      if (msg.message.includes('thành công')) {
          statusDiv.style.color = '#4CAF50';
      } else {
          statusDiv.style.color = '#9c27b0';
      }
  }
});
