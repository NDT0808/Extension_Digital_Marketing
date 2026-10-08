(() => {
  if (window.__fbFollowingScraperLoaded) return;
  window.__fbFollowingScraperLoaded = true;

  let isRunning = false;
  let isAutoMode = false;
  let statusText = '';
  const extractedUsers = new Map();

  const sleep = (ms) => new Promise((r) => setTimeout(r, ms));
  const rand = (min, max) => Math.floor(Math.random() * (max - min + 1)) + min;

  const RESERVED = new Set([
    'friends', 'groups', 'watch', 'photo', 'photos', 'stories', 'marketplace',
    'gaming', 'reel', 'reels', 'events', 'pages', 'notifications', 'messages',
    'bookmarks', 'help', 'policies', 'settings', 'login', 'hashtag', 'search',
    'videos', 'posts', 'permalink.php', 'share', 'ads', 'business', 'privacy',
    'about', 'recover', 'places', 'fundraisers', 'saved', 'memories', 'ai'
  ]);

  // ============================================================
  // Từ khóa nhận diện Breeder / Người bán chuyên nghiệp
  // ============================================================
  const BREEDER_KEYWORDS = [
    'kennel', 'kennels', 'breeder', 'breeders', 'breeding',
    'frenchie', 'frenchies', 'bulldog', 'bulldogs', 'bullies', 'bully',
    'pug', 'pugs', 'doodle', 'doodles', 'retriever', 'retrievers',
    'shepherd', 'shepherds', 'poodle', 'poodles', 'labrador', 'labradors',
    'golden', 'goldens', 'puppy', 'puppies', 'pup', 'pups',
    'farm', 'farms', 'ranch', 'rescue', 'shelter',
    'vet', 'veterinary', 'clinic', 'animal', 'k9', 'canine',
    'aussie', 'aussies', 'collie', 'collies', 'spaniel', 'spaniels',
    'mastiff', 'mastiffs', 'boxer', 'boxers', 'hound', 'hounds',
    'akc', 'registered', 'litter', 'whelp', 'stud', 'dam', 'sire',
    'cattery', 'cateries', 'terrier', 'terriers', 'setter', 'setters'
  ];

  function classifyAudience(name) {
    const nameLower = String(name || '').toLowerCase();
    for (const kw of BREEDER_KEYWORDS) {
      if (nameLower.includes(kw)) return 'BREEDER_PRO';
    }
    return 'DOG_LOVER_AUDIENCE';
  }

  function normalizeProfileUrl(href) {
    let u;
    try { u = new URL(href); } catch { return null; }
    if (!/(^|\.)facebook\.com$/.test(u.hostname)) return null;

    const segs = u.pathname.split('/').filter(Boolean);
    if (segs.length === 1 && segs[0] === 'profile.php') {
      const id = u.searchParams.get('id');
      return id ? `https://www.facebook.com/profile.php?id=${id}` : null;
    }
    if (segs.length === 1 && !RESERVED.has(segs[0].toLowerCase())) {
      return `https://www.facebook.com/${segs[0]}`;
    }
    return null;
  }

  function findAvatar(a) {
    let node = a;
    for (let i = 0; i < 6 && node; i++, node = node.parentElement) {
      const img = node.querySelector('img');
      if (img && img.src) return img.src;
      const svgImg = node.querySelector('image');
      if (svgImg) {
        const src = svgImg.getAttribute('xlink:href') || svgImg.getAttribute('href');
        if (src) return src;
      }
    }
    return '';
  }

  function scrapeDOM() {
    const main = document.querySelector('div[role="main"]') || document.body;
    const before = extractedUsers.size;

    main.querySelectorAll('a[role="link"][href]').forEach((a) => {
      // Bỏ qua các link nằm trong bài viết (timeline post) hoặc bảng tin để tránh cào nhầm khi hết danh sách
      if (a.closest('[role="article"]') || a.closest('[role="feed"]')) return;

      const url = normalizeProfileUrl(a.href);
      if (!url || extractedUsers.has(url)) return;

      const name = (a.innerText || '').split('\n')[0].trim();
      if (!name) return;

      const label = classifyAudience(name);
      extractedUsers.set(url, { name, url, avatar: findAvatar(a), audience_label: label });
    });

    return extractedUsers.size - before;
  }

  function pushState() {
    if (isAutoMode) return; 
    try {
      chrome.runtime.sendMessage({ action: 'STATE', state: getState() }, () => {
        void chrome.runtime.lastError;
      });
    } catch (_) {}
  }

  function getState() {
    return { running: isRunning, count: extractedUsers.size, status: statusText };
  }

  function scrollToBottom() {
    const el = document.scrollingElement || document.documentElement;
    window.scrollTo({ top: el.scrollHeight, behavior: 'smooth' });
  }

  // Nhận diện các tiêu đề báo hiệu đã qua khỏi danh sách Theo dõi
  // Lưu ý: KHAI TỌ 'followers' và 'người theo dõi' vì chúng xuất hiện
  // trong tab-nav đầu trang khi đang cào trang /followers
  function isEndSectionPresent() {
    const endWords = new Set([
      'check in', 'check-ins', 'địa điểm', 'bài đánh giá', 'reviews', 
      'thích', 'likes', 'sự kiện', 'events',
      'âm nhạc', 'music', 'phim', 'movies', 'chương trình tv', 
      'tv shows', 'sách', 'books', 'thể thao', 'sports'
    ]);
    // GHI CHÚ: Đã xóa 'nhóm', 'groups', 'người theo dõi', 'followers'
    // vì chúng xuất hiện trong sidebar/menu khi đang cào trang followers của Page
    
    const els = document.querySelectorAll('span[dir="auto"], h2, h3, h4');
    for (let el of els) {
      if (el.closest('[role="tablist"]') || el.closest('[role="navigation"]') || 
          el.closest('[role="article"]') || el.closest('[role="feed"]') ||
          el.closest('[role="banner"]') || el.closest('nav') ||
          el.closest('[data-pagelet]')) {
        continue;
      }
      const text = (el.innerText || '').trim().toLowerCase();
      if (endWords.has(text)) {
        const style = window.getComputedStyle(el);
        // Header thường có font >= 18px mới tính (tăng ngưỡng lên để tránh false positive)
        if (parseInt(style.fontSize) >= 18 && parseInt(style.fontWeight) >= 600) {
          return true;
        }
      }
    }
    return false;
  }

  // ===========================================================
  // HỆ THỐNG CHECKPOINT - Lưu và khôi phục dữ liệu cào
  // ===========================================================
  const CHECKPOINT_KEY = 'scraper_checkpoint';
  let lastSavedCount = 0;

  async function saveCheckpoint() {
    const data = Array.from(extractedUsers.values());
    if (data.length === lastSavedCount) return; // Không có gì mới
    return new Promise((resolve) => {
      chrome.storage.local.set({
        [CHECKPOINT_KEY]: {
          data: data,
          pageUrl: window.location.href,
          savedAt: new Date().toISOString(),
          count: data.length
        }
      }, () => {
        lastSavedCount = data.length;
        console.log(`[Checkpoint] Đã lưu ${data.length} người.`);
        resolve();
      });
    });
  }

  async function loadCheckpoint() {
    return new Promise((resolve) => {
      chrome.storage.local.get([CHECKPOINT_KEY], (res) => {
        const cp = res[CHECKPOINT_KEY];
        if (cp && cp.data && cp.data.length > 0) {
          // Nạp dữ liệu cũ vào Map
          cp.data.forEach(u => extractedUsers.set(u.url, u));
          lastSavedCount = cp.data.length;
          console.log(`[Checkpoint] Đã khôi phục ${cp.data.length} người từ lần cào trước.`);
          resolve(cp.count);
        } else {
          resolve(0);
        }
      });
    });
  }

  async function clearCheckpoint() {
    return new Promise((resolve) => {
      chrome.storage.local.remove([CHECKPOINT_KEY], resolve);
    });
  }

  async function startAutoScroll() {
    let stalledRounds = 0;
    let maxRounds = 9999; // Không giới hạn - Cào đến tận đáy danh sách
    
    // Khôi phục dữ liệu từ checkpoint nếu có
    const restoredCount = await loadCheckpoint();
    if (restoredCount > 0) {
      statusText = `Ðã khôi phục ${restoredCount} người từ lần trước. Tiếp tục cào...`;
      pushState();
      await sleep(1500); // Hiển thị thông báo 1.5 giây
    }

    // Lần cào đầu tiên ngay khi vừa vào trang
    scrapeDOM();

    // Nếu trang hoàn toàn không có ai ngay từ đầu (0 following), thoát ngay lập tức
    if (extractedUsers.size === 0) {
      statusText = 'Không theo dõi ai -> Bỏ qua ngay!';
      isRunning = false;
      pushState();
      if (isAutoMode) {
        chrome.runtime.sendMessage({ action: 'AUTO_FINISHED', data: [] });
      }
      return;
    }

    while (isRunning && maxRounds > 0) {
      maxRounds--;
      const beforeCount = extractedUsers.size;
      
      statusText = `Đang cào... (${beforeCount} người)`;
      pushState();

      scrollToBottom();
      await sleep(rand(1000, 2000)); // Cuộn nhanh hơn (1-2s)
      
      const added = scrapeDOM();

      if (isEndSectionPresent()) {
        statusText = 'Hoàn tất: Đã chạm đến phần Check-in/Thích...';
        isRunning = false;
        break;
      }

      if (added < 2) {
        stalledRounds++;
        window.scrollBy(0, 100);
        await sleep(500);
        
        // Chờ 3 vòng (chắc chắn hết người) thì mới dừng
        if (stalledRounds >= 3) { 
          statusText = 'Hoàn tất: đã đến cuối danh sách.';
          isRunning = false;
        }
      } else {
        stalledRounds = 0; 
      }

      // Auto-save checkpoint cứ mỗi 50 người mới
      if (extractedUsers.size - lastSavedCount >= 50) {
        await saveCheckpoint();
      }

      // Không có giới hạn số người - cào đến khi chạm đáy tự nhiên
      // Cập nhật thống kê phân loại để hiển thị trong popup
      const breederCount = Array.from(extractedUsers.values()).filter(u => u.audience_label === 'BREEDER_PRO').length;
      statusText = `Đang cào... (${extractedUsers.size} người | 🏠 ${breederCount} Breeder | 🐾 ${extractedUsers.size - breederCount} Dog Lover)`;
    }

    // Lưu checkpoint cuối cùng khi dừng
    await saveCheckpoint();
    const finalBreeder = Array.from(extractedUsers.values()).filter(u => u.audience_label === 'BREEDER_PRO').length;
    statusText = (statusText || 'Hoàn tất / Đã dừng') + ` | 💾 Đã lưu ${extractedUsers.size} người (🏠 ${finalBreeder} Breeder)`;
    pushState();

    if (isAutoMode) {
      chrome.runtime.sendMessage({
        action: 'AUTO_FINISHED',
        data: Array.from(extractedUsers.values())
      });
    }
  }

  async function exportToCSV(dataList, isPartial = false) {
    const data = dataList || Array.from(extractedUsers.values());
    if (data.length === 0) return;

    let csvParts = ['\uFEFFSTT,Họ và Tên,Profile URL,Avatar URL,Nguồn (Seed A),Phân Loại Tệp\n'];
    
    // Tính thống kê phân loại
    const breederList = data.filter(u => u.audience_label === 'BREEDER_PRO');
    const loverList = data.filter(u => u.audience_label === 'DOG_LOVER_AUDIENCE');
    chrome.runtime.sendMessage({ action: 'PROGRESS', message: `📊 Tổng: ${data.length} người | 🏠 Breeder/Pro: ${breederList.length} | 🐾 Dog Lover: ${loverList.length}` }).catch(()=>{});
    await sleep(1500);
    
    // Báo cáo bắt đầu tạo file
    chrome.runtime.sendMessage({ action: 'PROGRESS', message: `Đang ghép file CSV: 0% (${data.length} dòng)...` }).catch(()=>{});

    const chunkSize = 10000;
    for (let i = 0; i < data.length; i += chunkSize) {
      const chunk = data.slice(i, i + chunkSize);
      let chunkStr = '';
      chunk.forEach((u, idx) => {
        const esc = (s) => `"${String(s || '').replace(/"/g, '""')}"`;
        chunkStr += [i + idx + 1, esc(u.name), esc(u.url), esc(u.avatar), esc(u.sourceProfile || ''), esc(u.audience_label || 'DOG_LOVER_AUDIENCE')].join(',') + '\n';
      });
      csvParts.push(chunkStr);
      
      const percent = Math.round(((i + chunk.length) / data.length) * 100);
      chrome.runtime.sendMessage({ action: 'PROGRESS', message: `Đang ghép CSV: ${percent}% (${i + chunk.length}/${data.length})` }).catch(()=>{});
      
      // Nhường CPU 1 chút để trình duyệt không bị treo (Anti-freeze)
      await sleep(10);
    }

    chrome.runtime.sendMessage({ action: 'PROGRESS', message: `Đang tải file xuống máy tính...` }).catch(()=>{});

    const blob = new Blob(csvParts, { type: 'text/csv;charset=utf-8;' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    let fileName = `fb_following_auto_${Date.now()}.csv`;
    if (isPartial) fileName = `fb_following_BACKUP_TAM_${Date.now()}.csv`;
    a.download = fileName;
    document.body.appendChild(a);
    a.click();
    a.remove();
    setTimeout(() => URL.revokeObjectURL(url), 1000);
    
    chrome.runtime.sendMessage({ action: 'PROGRESS', message: `✅ Đã tải xong file thành công!` }).catch(()=>{});
  }

  chrome.runtime.onMessage.addListener((req, _sender, sendResponse) => {
    if (req.action === 'START') {
      if (!isRunning) {
        isAutoMode = false;
        isRunning = true;
        statusText = 'Đang cào...';
        startAutoScroll();
      }
    } else if (req.action === 'START_AUTO_MODE') {
      if (!isRunning) {
        isAutoMode = true;
        isRunning = true;
        extractedUsers.clear(); 
        statusText = 'Đang cào (Auto)...';
        startAutoScroll();
      }
    } else if (req.action === 'STOP') {
      isRunning = false;
      statusText = 'Đã dừng';
    } else if (req.action === 'EXPORT') {
      exportToCSV();
    } else if (req.action === 'FORCE_DOWNLOAD') {
      exportToCSV(req.data, req.isPartial);
    } else if (req.action === 'FORCE_DOWNLOAD_FROM_STORAGE') {
      chrome.storage.local.get(['allData'], (res) => {
        if (res.allData && res.allData.length > 0) {
          exportToCSV(res.allData, req.isPartial);
        } else {
          alert("Dữ liệu kẹt trong bộ nhớ tạm hiện đang trống!");
        }
      });
    }
    // Phản hồi rỗng để tránh background báo lỗi
    sendResponse({});
    return true;
  });
})();
