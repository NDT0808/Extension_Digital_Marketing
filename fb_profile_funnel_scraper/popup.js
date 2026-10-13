const $ = (id) => document.getElementById(id);

let state = {};

function getValidUrls(text) {
  if (!text) return [];
  return text.split('\n')
    .map(u => u.trim())
    .filter(u => u.length > 0);
}

function updateLinkCount() {
  const urls = getValidUrls($('urlList').value);
  if (urls.length === 0) {
    $('linkCountText').textContent = '0 link';
  } else {
    $('linkCountText').textContent = `${urls.length.toLocaleString('vi-VN')} link (Không giới hạn)`;
  }

  if (!$('toLine').value && urls.length > 0 && !state.isAutoRunning) {
    $('toLine').placeholder = `Hết (${urls.length.toLocaleString('vi-VN')})`;
  }
}

function render() {
  const urls = getValidUrls($('urlList').value);
  $('currentCount').textContent = state.allData ? state.allData.length.toLocaleString('vi-VN') : '0';

  let totalRange = 1;
  let doneCount = 0;
  if (state.urlList && state.urlList.length > 0) {
    let start = state.startIndex || 0;
    let end = (state.endIndex !== undefined && state.endIndex >= 0) ? state.endIndex : (state.urlList.length - 1);
    totalRange = Math.max(1, end - start + 1);
    let cur = state.currentIndex !== undefined ? state.currentIndex : start;
    doneCount = Math.max(0, cur - start);
  }

  let pct = Math.min(100, Math.round((doneCount / totalRange) * 100));
  if (state.isAutoRunning) {
    $('progressBar').style.width = `${pct}%`;
    $('progressPercent').textContent = `${pct}%`;
    $('currentStatusTitle').textContent = `Đang chạy (Dòng ${state.currentIndex + 1}/${(state.endIndex !== undefined ? state.endIndex + 1 : state.urlList.length)})`;
    $('statusText').textContent = state.statusMessage || `Đang xử lý link dòng ${state.currentIndex + 1}...`;

    $('btnAutoStart').style.display = 'none';
    $('btnResume').style.display = 'none';
    $('btnPause').style.display = 'flex';

    $('urlList').disabled = true;
    $('fromLine').disabled = true;
    $('toLine').disabled = true;
  } else {
    $('urlList').disabled = false;
    $('fromLine').disabled = false;
    $('toLine').disabled = false;
    $('btnPause').style.display = 'none';

    if (state.isPaused) {
      $('progressBar').style.width = `${pct}%`;
      $('progressPercent').textContent = `${pct}%`;
      $('currentStatusTitle').textContent = `Đã tạm dừng (Vị trí dòng ${state.currentIndex + 1})`;
      $('statusText').textContent = state.statusMessage || `Đã dừng ở link ${state.currentIndex + 1}. Bấm Tiếp tục để chạy tiếp hoặc Xuất file CSV.`;

      $('btnAutoStart').style.display = 'flex';
      $('btnAutoStart').textContent = '▶ Bắt đầu cào mới (Từ đầu)';
      $('btnResume').style.display = 'flex';
      $('btnResume').textContent = `⏯ Tiếp tục cào (từ dòng ${state.currentIndex + 1})`;
    } else {
      $('btnAutoStart').style.display = 'flex';
      $('btnAutoStart').textContent = '▶ Bắt đầu cào';
      $('btnResume').style.display = 'none';

      if (state.statusMessage && state.statusMessage.includes('hoàn thành')) {
        $('progressBar').style.width = '100%';
        $('progressPercent').textContent = '100%';
        $('currentStatusTitle').textContent = 'Đã hoàn tất!';
        $('statusText').textContent = state.statusMessage;
      } else {
        $('currentStatusTitle').textContent = 'Trạng thái: Sẵn sàng';
        $('statusText').textContent = state.statusMessage || 'Dán link, chọn khoảng chạy rồi ấn Bắt đầu.';
      }
    }
  }
}

function updateState() {
  chrome.runtime.sendMessage({ action: 'GET_STATE' }, (res) => {
    if (res) {
      state = res;

      // Populate textarea if empty and state has urls
      if (!state.isAutoRunning && state.urlList && state.urlList.length > 0 && $('urlList').value === '') {
        $('urlList').value = state.urlList.join('\n');
      }

      // Populate range inputs if not editing
      if (!state.isAutoRunning) {
        if (state.startIndex !== undefined && document.activeElement !== $('fromLine') && !$('fromLine').value) {
          $('fromLine').value = state.startIndex + 1;
        }
        if (state.endIndex !== undefined && state.endIndex >= 0 && document.activeElement !== $('toLine') && !$('toLine').value) {
          $('toLine').value = state.endIndex + 1;
        }
      }

      updateLinkCount();
      render();
    }
  });
}

$('urlList').addEventListener('input', () => {
  updateLinkCount();
});

$('btnAutoStart').addEventListener('click', () => {
  const text = $('urlList').value;
  const urls = getValidUrls(text);
  if (urls.length === 0) return alert('Vui lòng nhập ít nhất 1 link Facebook.');

  let fromVal = parseInt($('fromLine').value, 10);
  if (isNaN(fromVal) || fromVal < 1) fromVal = 1;

  let toVal = parseInt($('toLine').value, 10);
  if (isNaN(toVal) || toVal > urls.length) toVal = urls.length;

  if (fromVal > urls.length) {
    return alert(`Dòng bắt đầu (${fromVal}) vượt quá tổng số link (${urls.length})!`);
  }
  if (fromVal > toVal) {
    return alert(`Dòng bắt đầu (${fromVal}) không thể lớn hơn dòng kết thúc (${toVal})!`);
  }

  const startIdx = fromVal - 1;
  const endIdx = toVal - 1;

  chrome.tabs.query({ active: true, currentWindow: true }, (tabs) => {
    if (!tabs[0]) return alert('Không tìm thấy tab trình duyệt đang hoạt động.');
    chrome.runtime.sendMessage({
      action: 'START_AUTO',
      urls: urls,
      startIndex: startIdx,
      endIndex: endIdx,
      tabId: tabs[0].id
    }, () => {
      updateState();
    });
  });
});

$('btnResume').addEventListener('click', () => {
  chrome.tabs.query({ active: true, currentWindow: true }, (tabs) => {
    if (!tabs[0]) return alert('Không tìm thấy tab trình duyệt đang hoạt động.');
    chrome.runtime.sendMessage({
      action: 'RESUME_AUTO',
      tabId: tabs[0].id
    }, () => {
      updateState();
    });
  });
});

$('btnPause').addEventListener('click', () => {
  chrome.runtime.sendMessage({ action: 'STOP_AUTO' }, () => {
    updateState();
  });
});

$('btnExport').addEventListener('click', () => {
  chrome.runtime.sendMessage({ action: 'EXPORT_DATA' });
});

$('btnClear').addEventListener('click', () => {
  if (confirm('Bạn có chắc muốn xóa sạch toàn bộ dữ liệu cào và danh sách đang lưu trong bộ nhớ?')) {
    chrome.runtime.sendMessage({ action: 'CLEAR_DATA' }, () => {
      $('fromLine').value = '1';
      $('toLine').value = '';
      updateState();
    });
  }
});

chrome.runtime.onMessage.addListener((msg) => {
  if (msg.action === 'STATE_UPDATED') {
    state = msg.state;
    render();
  }
});

updateState();
setInterval(updateState, 1000);
