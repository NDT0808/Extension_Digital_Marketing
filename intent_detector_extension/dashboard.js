const keywords = {
  selling_dogs: [
      "puppies for sale", "available puppies", "upcoming litters", "buy a puppy",
      "reserve a puppy", "puppy application", "health guarantee", "akc registered",
      "place a deposit", "adopt a puppy", "our dogs", "sires and dams",
      "puppies expected", "stud service", "adoption fee", "planned litters"
  ],
  forms: [
      "puppy application", "waitlist application", "adoption form", 
      "apply for a puppy", "contact form", "questionnaire", 
      "fill out the form", "application form"
  ],
  take_home_kit: [
      "take home kit", "puppy pack", "starter kit", "blanket with mom's scent",
      "mom's scent", "food sample", "bag of food", "puppy supplies",
      "microchipped", "first round of shots", "vet checked", "dewormed"
  ],
  rescue: [
      "rescue", "foster", "donate", "shelter", "501(c)(3)", "non-profit", "adoption center", "adopt a pet", "volunteer"
  ],
  club: [
      "kennel club", "breed club", "member club", "akc club", "national club", "specialty show", "obedience club", "dog show"
  ],
  breeder: [
      "breeder", "sire", "sires", "dam", "dams", "kennel", "our dogs", "upcoming litters", "champion bloodlines", "litter", "litters", "pedigree", "whelp"
  ],
  pet_service: [
      "daycare", "grooming", "boarding", "dog training", "pet hotel", "pet spa", "dog walker", "training classes", "behavioral training"
  ]
};

// Hàm tính điểm (xác suất) dựa trên số lần lặp lại từ khóa
function getKeywordScore(text, kwList) {
  return kwList.reduce((sum, kw) => {
    const regex = new RegExp("\\b" + kw.replace(/[-\/\\^$*+?.()|[\]{}]/g, '\\$&') + "\\b", "gi");
    const matches = text.match(regex);
    return sum + (matches ? matches.length : 0);
  }, 0);
}

const priority_subpages = ['contact', 'apply', 'application', 'puppies', 'available', 'litters', 'about', 'adopt', 'form', 'inquir', 'resource'];

let queue = [];
let activeCount = 0;
let doneCount = 0;
let totalCount = 0;
const MAX_CONCURRENT = 3; // Giảm xuống 3 để tránh lag khi nó cuộn trang thực sự
const results = [];
let isRunning = false;

// Lưu trữ trạng thái quét của từng tab
const activeTabs = new Map(); 

const startBtn = document.getElementById('start-btn');
const exportBtn = document.getElementById('export-btn');
const urlInput = document.getElementById('url-input');
const tbody = document.getElementById('results-body');

startBtn.addEventListener('click', () => {
  if (isRunning) return;
  
  const rawUrls = urlInput.value.split(/[\n,]+/).map(u => u.trim()).filter(u => u.length > 0);
  if (rawUrls.length === 0) {
    alert("Vui lòng nhập ít nhất 1 URL");
    return;
  }

  isRunning = true;
  startBtn.disabled = true;
  startBtn.textContent = "Đang Quét Tự Động...";
  exportBtn.style.display = 'none';
  
  queue = rawUrls.map(u => u.startsWith('http') ? u : 'https://' + u);
  totalCount = queue.length;
  doneCount = 0;
  activeCount = 0;
  results.length = 0;
  tbody.innerHTML = '';
  
  document.getElementById('stat-total').textContent = totalCount;
  document.getElementById('stat-done').textContent = doneCount;
  document.getElementById('stat-active').textContent = activeCount;

  queue.forEach((url, index) => {
    const tr = document.createElement('tr');
    tr.id = `row-${index}`;
    tr.innerHTML = `
      <td>${url}</td>
      <td id="dogs-${index}">-</td>
      <td id="form-${index}">-</td>
      <td id="kit-${index}">-</td>
      <td id="status-${index}"><span class="status loading">Đang chờ</span></td>
    `;
    tbody.appendChild(tr);
    queue[index] = { url, index };
  });

  processNext();
});

function processNext() {
  document.getElementById('stat-active').textContent = activeCount;
  document.getElementById('stat-done').textContent = doneCount;

  if (doneCount === totalCount) {
    isRunning = false;
    startBtn.disabled = false;
    startBtn.textContent = "Bắt Đầu Quét Tự Động";
    exportBtn.style.display = 'inline-block';
    alert("Đã quét xong toàn bộ danh sách!");
    return;
  }

  while (activeCount < MAX_CONCURRENT && queue.length > 0) {
    const item = queue.shift();
    startScanning(item);
  }
}

async function startScanning(item) {
  activeCount++;
  document.getElementById('stat-active').textContent = activeCount;
  
  const statusTd = document.getElementById(`status-${item.index}`);
  statusTd.innerHTML = `<span class="status loading">Đang mở trang chủ...</span>`;
  
  try {
    // Mở tab (active: false để chạy ngầm, nhưng nếu user click sang vẫn thấy nó đang tự scroll)
    const tab = await chrome.tabs.create({ url: item.url, active: false });
    
    // Khởi tạo State Machine cho tab này
    activeTabs.set(tab.id, {
      item: item,
      step: 0,
      subpages: [],
      combinedText: "",
      has_form: false,
      isProcessingStep: false,
      timeoutId: null
    });

    resetTabTimeout(tab.id, 30000); // 30s cho mỗi trang

  } catch (err) {
    activeCount--;
    statusTd.innerHTML = `<span class="status error">Lỗi tạo tab</span>`;
    doneCount++;
    processNext();
  }
}


function triggerScriptInjection(tabId) {
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

// Lắng nghe khi tab tải xong để bơm script
chrome.tabs.onUpdated.addListener((tabId, changeInfo, tab) => {
  if (changeInfo.status === 'complete' && activeTabs.has(tabId)) {
    triggerScriptInjection(tabId);
  }
});


function handleStepResult(tabId, state, data) {
  state.combinedText += " " + data.text;
  if (data.has_form) state.has_form = true;
  
  // Nếu là trang chủ (step 0), tìm ra các trang con để đi tiếp
  if (state.step === 0) {
      const baseHostname = new URL(state.item.url).hostname.replace('www.', '');
      let validLinks = new Set();
      
      for (let href of data.links) {
          try {
              let urlObj = new URL(href);
              let linkHostname = urlObj.hostname.replace('www.', '');
              if (linkHostname === baseHostname && (urlObj.protocol === 'http:' || urlObj.protocol === 'https:')) {
                  let cleanUrl = href.split('#')[0];
                  if (cleanUrl !== state.item.url.split('#')[0]) validLinks.add(cleanUrl);
              }
          } catch(e){}
      }
      
      let sorted = Array.from(validLinks).sort((a, b) => {
          let aL = a.toLowerCase(); let bL = b.toLowerCase();
          let aMatch = priority_subpages.some(kw => aL.includes(kw));
          let bMatch = priority_subpages.some(kw => bL.includes(kw));
          if (aMatch && !bMatch) return -1;
          if (!aMatch && bMatch) return 1;
          return 0;
      }).slice(0, 10); // Tăng giới hạn lên tối đa 10 trang con
      
      state.subpages = sorted;
  }
  
  state.step++;
  
  // Reset lại timeout 30s cho từng trang con thay vì ép 45s cho cả cục website
  resetTabTimeout(tabId, 30000);

  if (state.step <= state.subpages.length) {
      let nextUrl = state.subpages[state.step - 1];
      const statusTd = document.getElementById(`status-${state.item.index}`);
      statusTd.innerHTML = `<span class="status loading">Tiếp tục chuyển sang: ${nextUrl.substring(0, 25)}...</span>`;
      
      chrome.tabs.update(tabId, { url: nextUrl });
  } else {
      evaluateFinalResult(tabId, state);
  }
}

function evaluateFinalResult(tabId, state) {
    const rescueScore = getKeywordScore(state.combinedText, keywords.rescue);
    const clubScore = getKeywordScore(state.combinedText, keywords.club);
    const breederScore = getKeywordScore(state.combinedText, keywords.breeder);
    const petServiceScore = getKeywordScore(state.combinedText, keywords.pet_service);
    const sellDogScore = getKeywordScore(state.combinedText, keywords.selling_dogs);
    const formScore = getKeywordScore(state.combinedText, keywords.forms);
    const kitScore = getKeywordScore(state.combinedText, keywords.take_home_kit);
  
    // Mặc định có bán chó nếu xuất hiện các cụm từ này dù chỉ 1 lần
    let has_strong_sales_intent = /available pupp(y|ies)|pupp(y|ies) for sale/i.test(state.combinedText);

    // Cần ít nhất 2 lần lặp lại từ khóa để được coi là "CÓ"
    let sells_dogs = has_strong_sales_intent || (sellDogScore >= 2);
    let has_form = state.has_form || formScore >= 1;
    let has_take_home_kit = kitScore >= 1;
  
    let site_type = "Không rõ";
    
    // So sánh điểm số để xác định loại hình web chính xác nhất
    const scores = [
      { type: "Dịch Vụ Thú Cưng (Spa/Hotel)", score: petServiceScore },
      { type: "Trạm Cứu Trợ (Rescue)", score: rescueScore },
      { type: "Câu Lạc Bộ (AKC Club)", score: clubScore },
      { type: "Trại Nhân Giống (Breeder)", score: breederScore + sellDogScore + (has_strong_sales_intent ? 5 : 0) }
    ];
  
    scores.sort((a, b) => b.score - a.score); // Sắp xếp giảm dần
  
    // Nếu điểm cao nhất lớn hơn hoặc bằng 2 (xuất hiện ít nhất 2 lần), gán loại trang
    if (scores[0].score >= 2) {
      site_type = scores[0].type;
    }
  
    // --- Logic ưu tiên (Priority Overrides) ---
    // Nếu một trang vừa có dịch vụ huấn luyện (Spa/Hotel) hoặc Không rõ, nhưng điểm Breeder cao (>= 3), thì ưu tiên Breeder.
    // KHÔNG áp dụng ghi đè này cho Trạm Cứu Trợ (Rescue) hoặc Câu Lạc Bộ (Club) vì họ cũng hay nhắc tới chó/nhận nuôi chó.
    if (site_type !== "Trạm Cứu Trợ (Rescue)" && site_type !== "Câu Lạc Bộ (AKC Club)") {
        if ((breederScore + sellDogScore) >= 3 || has_strong_sales_intent) {
            site_type = "Trại Nhân Giống (Breeder)";
        } else if (sells_dogs && site_type === "Không rõ") {
            site_type = "Trại Nhân Giống (Breeder)";
        }
    }
  
    // --- Logic loại trừ (Negative Prompt / Overrides) ---
    if (site_type === "Dịch Vụ Thú Cưng (Spa/Hotel)" || site_type === "Trạm Cứu Trợ (Rescue)" || site_type === "Câu Lạc Bộ (AKC Club)") {
      // Nếu là dịch vụ thú cưng, các form tìm được thường là Đặt lịch (Booking/Contact) chứ không phải Form đăng ký mua chó.
      // Và họ không bán chó (có thể chỉ nhận nuôi hoặc huấn luyện).
      sells_dogs = false;
      has_form = false;
      has_take_home_kit = false;
    } else if (site_type === "Trại Nhân Giống (Breeder)") {
      // Nếu điểm Breeder cao thì chắc chắn đây là trại giống, dù hiện tại họ hết lứa chó con (ẩn nút mua) thì vẫn mang bản chất bán chó.
      sells_dogs = true;
    }
  
    finishTab(tabId, true, { sells_dogs, has_form, has_take_home_kit, site_type });
}

  function getBadge(isYes) {
  return `<span class="status ${isYes ? 'yes' : 'no'}">${isYes ? 'CÓ' : 'KHÔNG'}</span>`;
}

function finishTab(tabId, success, dataOrError) {
  const state = activeTabs.get(tabId);
  if (!state) return;
  
  if (state.timeoutId) clearTimeout(state.timeoutId);
  activeTabs.delete(tabId);
  activeCount--;
  doneCount++;
  
  try { chrome.tabs.remove(tabId); } catch (e) {}

  const tr = document.getElementById(`row-${state.item.index}`);
  const resData = {
    url: state.item.url,
    sells_dogs: false,
    has_form: false,
    has_kit: false,
    site_type: "",
    status: success ? "Thành công" : dataOrError
  };

  if (success) {
    document.getElementById(`dogs-${state.item.index}`).innerHTML = getBadge(dataOrError.sells_dogs);
    document.getElementById(`form-${state.item.index}`).innerHTML = getBadge(dataOrError.has_form);
    document.getElementById(`kit-${state.item.index}`).innerHTML = getBadge(dataOrError.has_take_home_kit);
    document.getElementById(`status-${state.item.index}`).innerHTML = `<span class="status yes">${dataOrError.site_type}</span>`;
    
    resData.sells_dogs = dataOrError.sells_dogs;
    resData.has_form = dataOrError.has_form;
    resData.has_kit = dataOrError.has_take_home_kit;
    resData.site_type = dataOrError.site_type;
  } else {
    document.getElementById(`status-${state.item.index}`).innerHTML = `<span class="status error">${dataOrError}</span>`;
    resData.site_type = "Lỗi";
  }
  
  results.push(resData);
  processNext();
}

exportBtn.addEventListener('click', () => {
  if (results.length === 0) return;
  let csv = 'Website,Ban_Cho,Co_Form,Take_Home_Kit,Loai_Trang,Trang_Thai\n';
  results.forEach(r => {
    csv += `"${r.url}",${r.sells_dogs ? 'CO' : 'KHONG'},${r.has_form ? 'CO' : 'KHONG'},${r.has_kit ? 'CO' : 'KHONG'},"${r.site_type}","${r.status}"\n`;
  });
  
  const blob = new Blob(["\ufeff" + csv], { type: 'text/csv;charset=utf-8;' });
  const url = URL.createObjectURL(blob);
  const link = document.createElement("a");
  link.setAttribute("href", url);
  link.setAttribute("download", "ket_qua_quet_website.csv");
  document.body.appendChild(link);
  link.click();
  document.body.removeChild(link);
});
