(() => {
  if (window.__fbFollowingScraperLoaded) return;
  window.__fbFollowingScraperLoaded = true;

  let isRunning = false;
  let isAutoMode = false;
  let statusText = '';
  let restoredBaseCount = 0;
  let resumeOnReload = false;
  let recoveryCycles = 0;
  let facebookInterrupted = false;
  let recoveryReloadTimer = null;
  let ignoreCheckpointOnce = false;
  let lastSeenAnchor = null;
  let autoPageLimit = 0;
  const AUTO_PAGE_MIN = 1000000;
  const AUTO_PAGE_MAX = 1000000;
  const MAX_RECOVERY_CYCLES = 3;
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
    // Facebook dùng /people/Ten/ID, /pages/Ten/ID, và /p/Ten-ID cho nhiều profile/page.
    if (segs.length >= 2 && ['people', 'pages', 'p'].includes(segs[0].toLowerCase())) {
      const id = segs[segs.length - 1];
      // Nếu có ID số ở cuối, hoặc chỉ đơn giản là định dạng /p/Ten-12345
      // Ta lấy luôn nguyên bản link đó vì nó là link chuẩn
      return `https://www.facebook.com/${segs.join('/')}`;
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

  function getProfileAnchors() {
    const isPeopleListPage = /\/(followers|following)(?:\/|$)/i.test(location.pathname) ||
      /^(followers|following)$/i.test(new URL(location.href).searchParams.get('sk') || '');
      
    // Tìm trên toàn bộ document thay vì chỉ div[role="main"] 
    // vì Facebook có thể dùng React Portals để render danh sách ra ngoài main.
    return Array.from(document.querySelectorAll('a[href]')).filter((a) => {
      // Bỏ qua thanh sidebar trái, banner trên cùng, và các tab menu
      if (a.closest('[role="banner"], [role="tablist"], [role="complementary"]')) return false;
      
      // Chặn các bài đăng (trừ khi đang ở đúng trang danh sách)
      if (!isPeopleListPage && a.closest('[role="article"]')) return false;
      
      return Boolean(normalizeProfileUrl(a.href));
    });
  }

  function findProfileName(a) {
    // 1. Lấy từ thuộc tính ẩn của avatar
    let direct = (a.getAttribute('aria-label') || a.getAttribute('title') || '').trim();
    if (direct && direct.length > 1) return direct;
    
    // 2. Lấy nội dung trực tiếp của thẻ a (nếu là thẻ chữ)
    direct = (a.innerText || '').split('\n')[0].trim();
    if (direct && direct.length > 1) return direct;

    // 3. Quét ngược lên lấy nội dung nguyên dòng (row) và tách dòng
    const ignored = /^(theo dõi|follow|following|message|nhắn tin|bạn bè|friends|bỏ theo dõi|unfollow|gỡ|remove|chỉnh sửa|edit)$/i;
    let node = a.parentElement;
    for (let depth = 0; depth < 6 && node; depth++, node = node.parentElement) {
      const lines = (node.innerText || '').split('\n').map(l => l.trim()).filter(l => l.length > 1);
      for (let line of lines) {
        if (!ignored.test(line)) {
          return line;
        }
      }
    }
    return '';
  }

  function scrapeDOM() {
    const before = extractedUsers.size;
    getProfileAnchors().forEach((a) => {
      const url = normalizeProfileUrl(a.href);
      if (!url || extractedUsers.has(url)) return;
      const name = findProfileName(a);
      if (!name) return;
      const label = classifyAudience(name);
      extractedUsers.set(url, { name, url, avatar: findAvatar(a), audience_label: label });
      lastSeenAnchor = { url, name };
    });
    return extractedUsers.size - before;
  }

  function pushState() {
    try {
      chrome.runtime.sendMessage({ action: 'STATE', state: getState() }, () => {
        void chrome.runtime.lastError;
      });
    } catch (_) {}
  }

  function getState() {
    const metrics = getScrollMetrics();
    return {
      running: isRunning,
      count: extractedUsers.size,
      status: statusText,
      hasCheckpoint: extractedUsers.size > 0,
      savedCount: extractedUsers.size,
      restoredCount: restoredBaseCount,
      newCount: Math.max(0, extractedUsers.size - restoredBaseCount),
      domProfileLinks: getProfileAnchors().length,
      scrollTop: Math.round(metrics.top),
      scrollHeight: Math.round(metrics.height)
    };
  }

  function getScrollTarget() {
    const doc = document.scrollingElement || document.documentElement;
    const main = document.querySelector('div[role="main"]') || document.body;
    let best = doc;
    let bestRange = Math.max(0, doc.scrollHeight - doc.clientHeight);

    // Facebook dùng cả kiểu cuộn toàn trang lẫn một khung cuộn riêng.
    [main, ...main.querySelectorAll('div')].forEach((el) => {
      if (el === doc || el.clientHeight < 250) return;
      const style = window.getComputedStyle(el);
      if (!/(auto|scroll)/.test(style.overflowY)) return;
      const range = el.scrollHeight - el.clientHeight;
      if (range > bestRange && range > 300) {
        best = el;
        bestRange = range;
      }
    });
    return best;
  }

  function setScrollTop(target, top) {
    const isDocument = target === document.scrollingElement ||
      target === document.documentElement || target === document.body;
    if (isDocument) {
      window.scrollTo({ top, behavior: 'auto' });
    } else {
      target.scrollTo({ top, behavior: 'auto' });
      target.dispatchEvent(new Event('scroll', { bubbles: true }));
    }
  }

  function scrollForward() {
    const el = getScrollTarget();
    const isDocument = el === document.scrollingElement ||
      el === document.documentElement || el === document.body;
    const viewport = isDocument ? window.innerHeight : el.clientHeight;
    const currentTop = isDocument ? (window.scrollY || el.scrollTop || 0) : el.scrollTop;
    const visibleAnchors = getProfileAnchors()
      .filter((a) => {
        const rect = a.getBoundingClientRect();
        return rect.width > 0 && rect.height > 0;
      })
      .sort((a, b) => a.getBoundingClientRect().bottom - b.getBoundingClientRect().bottom);

    // Bám vào card profile cuối cùng để kích hoạt virtual list của Facebook.
    const last = visibleAnchors[visibleAnchors.length - 1];
    if (last) last.scrollIntoView({ block: 'end', behavior: 'auto' });

    const afterCardTop = isDocument ? (window.scrollY || el.scrollTop || 0) : el.scrollTop;
    const nextTop = Math.max(currentTop + 450, afterCardTop + Math.max(350, viewport * 0.65));
    setScrollTop(el, Math.min(el.scrollHeight, nextTop));
    return { domLinks: visibleAnchors.length, from: currentTop, requested: nextTop };
  }

  async function resumeToCheckpointAnchor(checkpoint) {
    const anchor = checkpoint?.resumeAnchor;
    if (!anchor?.url) return false;

    statusText = `Đang tìm mốc tiếp tục: ${anchor.name || anchor.url}`;
    pushState();
    for (let round = 0; round < 80 && isRunning; round++) {
      if (isFacebookErrorPage()) return false;
      const found = getProfileAnchors().find((a) => normalizeProfileUrl(a.href) === anchor.url);
      if (found) {
        found.scrollIntoView({ block: 'center', behavior: 'auto' });
        await sleep(800);
        statusText = `Đã tới mốc ${anchor.name || anchor.url} • tiếp tục cào từ đây...`;
        pushState();
        return true;
      }
      scrollForward();
      await sleep(900);
      const added = scrapeDOM();
      if (added > 0) {
        await saveCheckpoint(true);
        pushState();
      }
    }
    return false;
  }

  function getScrollMetrics() {
    const el = getScrollTarget();
    const isDocument = el === document.scrollingElement ||
      el === document.documentElement || el === document.body;
    const top = isDocument ? (window.scrollY || el.scrollTop || 0) : el.scrollTop;
    const viewport = isDocument ? (window.innerHeight || el.clientHeight || 0) : el.clientHeight;
    const height = isDocument
      ? Math.max(el.scrollHeight || 0, document.body?.scrollHeight || 0)
      : el.scrollHeight;
    return {
      el,
      top,
      viewport,
      height,
      nearBottom: top + viewport >= height - Math.max(500, viewport * 0.75)
    };
  }

  function hasVisibleLoader() {
    const el = getScrollTarget();
    const container = (el === document.scrollingElement || el === document.documentElement) ? document.body : el;
    return Array.from(container.querySelectorAll('[role=progressbar], [aria-busy=true]')).some((loader) => {
      // Bỏ qua các loader ở thanh điều hướng trên cùng hoặc cột chat bên phải
      if (loader.closest('[role="banner"], [role="complementary"]')) return false;
      const rect = loader.getBoundingClientRect();
      const style = window.getComputedStyle(loader);
      return rect.width > 0 && rect.height > 0 && style.display !== 'none' && style.visibility !== 'hidden';
    });
  }

  function isFacebookErrorPage() {
    const main = document.querySelector('div[role="main"]') || document.body;
    const text = (main?.innerText || '').toLowerCase();
    return text.includes('trang này hiện không hiển thị') ||
      text.includes("this page isn't available") ||
      text.includes('this content isn’t available right now') ||
      text.includes('nội dung này hiện không hiển thị') ||
      text.includes('hãy thử tải lại trang này');
  }

  async function pauseOnFacebookError() {
    isRunning = false;
    facebookInterrupted = true;
    resumeOnReload = recoveryCycles < MAX_RECOVERY_CYCLES;
    statusText = resumeOnReload
      ? `Facebook tạm ngắt tải. Đã lưu ${extractedUsers.size} profile — reload trang sẽ tự tiếp tục (${recoveryCycles}/${MAX_RECOVERY_CYCLES}).`
      : `Đã dừng sau ${MAX_RECOVERY_CYCLES} lần phục hồi để tránh vòng lặp và checkpoint tài khoản.`;
    await saveCheckpoint(true);
    pushState();
    if (resumeOnReload && !recoveryReloadTimer) {
      // Cho Facebook một khoảng nghỉ trước khi thử lại trang lỗi.
      recoveryReloadTimer = setTimeout(() => {
        recoveryReloadTimer = null;
        if (resumeOnReload && !isRunning) {
          chrome.runtime.sendMessage({ action: 'RELOAD_CURRENT_PAGE' }, () => { void chrome.runtime.lastError; });
        }
      }, 15000);
    }
  }

  async function waitForLazyLoad(beforeCount, beforeHeight, maxWaitMs = (isAutoMode ? 10000 : 15000)) {
    const deadline = Date.now() + maxWaitMs;
    let lastCount = beforeCount;
    let lastHeight = beforeHeight;
    let sawProgress = false;
    let quietPolls = 0;
    let noLoaderPolls = 0;

    while (isRunning && Date.now() < deadline) {
      await sleep(500);
      if (isFacebookErrorPage()) {
        return { added: extractedUsers.size - beforeCount, heightGrew: false, pageError: true };
      }
      const addedNow = scrapeDOM();
      if (addedNow > 0) {
        statusText = `Đã nhận thêm ${addedNow} profile • tổng ${extractedUsers.size} • đang chờ batch tiếp theo...`;
        await saveCheckpoint(true);
        pushState();
      }
      const metrics = getScrollMetrics();
      const changed = extractedUsers.size > lastCount || metrics.height > lastHeight + 2;

      if (changed) {
        sawProgress = true;
        quietPolls = 0;
        noLoaderPolls = 0;
        lastCount = extractedUsers.size;
        lastHeight = metrics.height;
      } else {
        quietPolls++;
        if (!hasVisibleLoader()) {
          noLoaderPolls++;
        } else {
          noLoaderPolls = 0;
        }
      }

      // Sau khi thấy batch mới, chờ DOM yên 1 giây rồi tiếp tục cuộn.
      if (sawProgress && quietPolls >= 2) break;
      // Break sớm nếu không có loader (~1.5 giây)
      if (!sawProgress && noLoaderPolls >= 3) break;
    }

    return {
      added: extractedUsers.size - beforeCount,
      heightGrew: getScrollMetrics().height > beforeHeight + 2
    };
  }

  async function nudgeLazyLoader() {
    const metrics = getScrollMetrics();
    const upBy = Math.max(350, Math.floor(metrics.viewport * 0.8));
    setScrollTop(metrics.el, Math.max(0, metrics.top - upBy));
    await sleep(500);
    scrapeDOM();
    setScrollTop(metrics.el, metrics.height);
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

  function normalizeCheckpointPageKey(value = window.location.href) {
    const url = new URL(value, window.location.origin);
    const path = url.pathname.replace(/\/+$/, '') || '/';
    const id = url.searchParams.get('id');
    const sk = url.searchParams.get('sk');
    const stableQuery = new URLSearchParams();
    if (id) stableQuery.set('id', id);
    if (sk) stableQuery.set('sk', sk);
    const query = stableQuery.toString();
    return `${url.origin.toLowerCase()}${path}${query ? `?${query}` : ''}`;
  }

  function getCheckpointPageKey() {
    return normalizeCheckpointPageKey();
  }

  function checkpointMatchesCurrentPage(cp) {
    if (!cp) return false;
    if (cp.pageKey === getCheckpointPageKey()) return true;
    try {
      return Boolean(cp.pageUrl) && normalizeCheckpointPageKey(cp.pageUrl) === getCheckpointPageKey();
    } catch (_) {
      return false;
    }
  }

  async function saveCheckpoint(force = false) {
    const data = Array.from(extractedUsers.values());
    if (!force && data.length === lastSavedCount) return;
    const scroll = getScrollMetrics();
    return new Promise((resolve) => {
      chrome.storage.local.set({
        [CHECKPOINT_KEY]: {
          data: data,
          pageUrl: window.location.href,
          pageKey: getCheckpointPageKey(),
          savedAt: new Date().toISOString(),
          count: data.length,
          scrollTop: scroll.top,
          status: isRunning ? 'running' : (facebookInterrupted ? 'interrupted' : 'paused'),
          resumeOnReload,
          recoveryCycles,
          resumeAnchor: lastSeenAnchor,
          autoMode: isAutoMode,
          autoPageLimit
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
        if (checkpointMatchesCurrentPage(cp) && cp.data && cp.data.length > 0) {
          // Nạp dữ liệu cũ vào Map
          cp.data.forEach(u => extractedUsers.set(u.url, u));
          lastSavedCount = cp.data.length;
          restoredBaseCount = Math.max(restoredBaseCount, cp.data.length);
          resumeOnReload = Boolean(cp.resumeOnReload);
          recoveryCycles = Number(cp.recoveryCycles || 0);
          if (cp.autoMode) isAutoMode = true;
          if (cp.autoPageLimit) autoPageLimit = Number(cp.autoPageLimit);
          const fallbackAnchor = cp.data[cp.data.length - 1];
          lastSeenAnchor = cp.resumeAnchor || (fallbackAnchor?.url ? { url: fallbackAnchor.url, name: fallbackAnchor.name || '' } : lastSeenAnchor);
          console.log(`[Checkpoint] Đã khôi phục ${cp.data.length} người từ lần cào trước.`);
          resolve(cp);
        } else {
          resolve(null);
        }
      });
    });
  }

  async function clearCheckpoint() {
    return new Promise((resolve) => {
      chrome.storage.local.remove([CHECKPOINT_KEY], resolve);
    });
  }

  function reachedAutoPageLimit() {
    return isAutoMode && autoPageLimit > 0 && extractedUsers.size >= autoPageLimit;
  }

  async function startAutoScroll() {
    let stalledRounds = 0;
    let loadingOnlyRounds = 0;
    // Facebook may keep skeleton cards visible for 10-20 seconds on large Pages.
    // 2 vòng lặp kiểm tra là kết thúc luôn (~3 giây)
    const STABLE_ROUNDS_TO_FINISH = isAutoMode ? 2 : 30;
    const END_SECTION_ROUNDS_TO_FINISH = isAutoMode ? 1 : 10;
    const autoPageDeadline = isAutoMode ? Date.now() + 180000 : 0;
    
    // Khôi phục dữ liệu và vị trí cuộn từ phiên trước nếu đúng URL.
    const restoredCheckpoint = ignoreCheckpointOnce ? null : await loadCheckpoint();
    ignoreCheckpointOnce = false;
    const restoredCount = restoredCheckpoint?.count || 0;
    if (restoredCount > 0) {
      statusText = `Đã khôi phục ${restoredCount} người từ bộ nhớ tạm. Tiếp tục cào...`;
      pushState();
      await sleep(1500);
    }
    // Facebook có thể render khung trang trước rồi mới nạp danh sách. Chờ tối đa
    // Chờ 2 giây để xác định trang trắng
    const initialDeadline = Date.now() + (isAutoMode ? 2500 : 20000);
    do {
      scrapeDOM();
      if (extractedUsers.size > 0) break;
      statusText = 'Đang chờ Facebook tải danh sách...';
      pushState();
      await sleep(1000);
    } while (isRunning && Date.now() < initialDeadline);

    // Nếu trang hoàn toàn không có ai ngay từ đầu (0 following), thoát ngay lập tức
    const target = getScrollTarget();
    let anchorFound = false;
    if (restoredCheckpoint?.resumeAnchor) {
      anchorFound = await resumeToCheckpointAnchor(restoredCheckpoint);
    }
    if (!anchorFound && restoredCheckpoint?.scrollTop > 0) {
      // Fallback khi Facebook không render được anchor cũ.
      setScrollTop(target, restoredCheckpoint.scrollTop);
      await sleep(1200);
      scrapeDOM();
    } else if (!anchorFound) {
      // Một phiên mới luôn bắt đầu từ đầu danh sách.
      setScrollTop(target, 0);
      await sleep(500);
      scrapeDOM();
    }

    if (extractedUsers.size === 0) {
      statusText = 'Không theo dõi ai -> Bỏ qua ngay!';
      isRunning = false;
      pushState();
      if (isAutoMode) {
        chrome.runtime.sendMessage({ action: 'AUTO_FINISHED', data: [] });
      }
      return;
    }

    if (reachedAutoPageLimit()) {
      statusText = `Đã đạt giới hạn ${autoPageLimit} profile của trang này.`;
      isRunning = false;
      resumeOnReload = false;
    }

    while (isRunning) {
      if (isAutoMode && autoPageDeadline && Date.now() >= autoPageDeadline) {
        statusText = `Trang này không tải thêm sau thời gian chờ — lưu ${extractedUsers.size} profile và chuyển link kế tiếp.`;
        isRunning = false;
        resumeOnReload = false;
        break;
      }
      if (isFacebookErrorPage()) {
        await pauseOnFacebookError();
        break;
      }

      const beforeCount = extractedUsers.size;
      const beforeMetrics = getScrollMetrics();
      
      statusText = `Đang cào... (${beforeCount} người) • vị trí ${Math.round(beforeMetrics.top)}/${Math.round(beforeMetrics.height)}`;
      pushState();

      const scrollResult = scrollForward();
      statusText = `Đã cuộn • ${scrollResult.domLinks} link DOM • chờ batch tiếp theo (${beforeCount} người)`;
      pushState();
      await sleep(rand(2200, 3800));

      const progress = await waitForLazyLoad(beforeCount, beforeMetrics.height);
      if (progress.pageError) {
        await pauseOnFacebookError();
        break;
      }
      const afterMetrics = getScrollMetrics();
      const loaderVisible = hasVisibleLoader();
      const scrollMoved = afterMetrics.top > beforeMetrics.top + 80;

      if (progress.added > 0 || progress.heightGrew || scrollMoved || !afterMetrics.nearBottom) {
        stalledRounds = 0;
        loadingOnlyRounds = 0;
      } else if (loaderVisible && loadingOnlyRounds < 8) {
        // Loader còn hiện nghĩa là Facebook chưa trả dữ liệu; không tính là một
        // lượt đứng yên. Giới hạn 8 lượt để loader bị kẹt không tạo vòng lặp vô hạn.
        loadingOnlyRounds++;
        statusText = `Facebook đang tải thêm... (${extractedUsers.size} người)`;
        await sleep(2000);
      } else {
        loadingOnlyRounds = 0;
        stalledRounds++;
        statusText = `Đang xác nhận cuối danh sách... ${stalledRounds}/${STABLE_ROUNDS_TO_FINISH} (${extractedUsers.size} người)`;
        await nudgeLazyLoader();

        const endConfirmed = isEndSectionPresent() && stalledRounds >= END_SECTION_ROUNDS_TO_FINISH;
        if (endConfirmed || stalledRounds >= STABLE_ROUNDS_TO_FINISH) {
          statusText = endConfirmed
            ? 'Hoàn tất: đã qua hết danh sách đang theo dõi.'
            : 'Hoàn tất: Facebook không còn tải thêm dữ liệu.';
          isRunning = false;
          resumeOnReload = false;
        }
      }

      // Lưu ngay sau mỗi batch mới để mất điện/tắt máy vẫn tiếp tục được.
      if (progress.added > 0) {
        if (extractedUsers.size > restoredBaseCount) recoveryCycles = 0;
        await saveCheckpoint(true);
      }

      // Không có giới hạn số người - cào đến khi chạm đáy tự nhiên
      if (reachedAutoPageLimit()) {
        statusText = `Đã đạt ${autoPageLimit} profile — chuyển sang link kế tiếp...`;
        isRunning = false;
        resumeOnReload = false;
      }

      // Cập nhật thống kê phân loại để hiển thị trong popup
      const breederCount = Array.from(extractedUsers.values()).filter(u => u.audience_label === 'BREEDER_PRO').length;
      if (isRunning) {
        const newThisRun = Math.max(0, extractedUsers.size - restoredBaseCount);
        statusText = progress.added === 0 && restoredBaseCount > 0
          ? `Đang đi qua dữ liệu cũ sau reload • đã lưu ${restoredBaseCount} • mới +${newThisRun}`
          : `Đang cào... (${extractedUsers.size} người | mới +${newThisRun} | 🏠 ${breederCount} Breeder | 🐾 ${extractedUsers.size - breederCount} Dog Lover)`;
      }
    }

    // Lưu checkpoint cuối cùng khi dừng
    await saveCheckpoint(true);
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
    if (req.action === 'GET_STATE') {
      chrome.storage.local.get([CHECKPOINT_KEY], (res) => {
        const cp = res[CHECKPOINT_KEY];
        const state = getState();
        if (checkpointMatchesCurrentPage(cp) && cp.count > 0) {
          state.hasCheckpoint = true;
          state.savedCount = cp.count;
          state.savedAt = cp.savedAt;
          if (!state.count) state.count = cp.count;
        }
        sendResponse(state);
      });
      return true;
    } else if (req.action === 'START') {
      if (!isRunning) {
        isAutoMode = false;
        autoPageLimit = 0;
        isRunning = true;
        if (recoveryReloadTimer) { clearTimeout(recoveryReloadTimer); recoveryReloadTimer = null; }
        facebookInterrupted = false;
        resumeOnReload = true;
        recoveryCycles = 0;
        statusText = 'Đang cào...';
        startAutoScroll();
      }
      sendResponse(getState());
      return false;
    } else if (req.action === 'START_AUTO_MODE') {
      if (!isRunning) {
        isAutoMode = true;
        autoPageLimit = rand(AUTO_PAGE_MIN, AUTO_PAGE_MAX);
        isRunning = true;
        facebookInterrupted = false;
        resumeOnReload = true;
        recoveryCycles = 0;
        extractedUsers.clear(); 
        restoredBaseCount = 0;
        lastSeenAnchor = null;
        ignoreCheckpointOnce = true;
        statusText = 'Đang cào (Auto)...';
        startAutoScroll();
      }
      sendResponse(getState());
      return false;
    } else if (req.action === 'STOP') {
      const wasAutoMode = isAutoMode;
      isRunning = false;
      resumeOnReload = false;
      if (recoveryReloadTimer) { clearTimeout(recoveryReloadTimer); recoveryReloadTimer = null; }
      facebookInterrupted = false;
      statusText = "Đã dừng — phiên đã được lưu tạm";
      saveCheckpoint(true).then(() => {
        if (wasAutoMode && extractedUsers.size > 0) {
          chrome.runtime.sendMessage({ action: "AUTO_PAGE_SAVED", data: Array.from(extractedUsers.values()) });
        }
        pushState();
        sendResponse(getState());
      });
      return true;
    } else if (req.action === 'CLEAR_CHECKPOINT') {
      clearCheckpoint().then(() => {
        extractedUsers.clear();
        lastSavedCount = 0;
        restoredBaseCount = 0;
        resumeOnReload = false;
        recoveryCycles = 0;
        facebookInterrupted = false;
        statusText = 'Đã xóa phiên cào tạm';
        sendResponse(getState());
      });
      return true;
    } else if (req.action === 'EXPORT') {
      if (extractedUsers.size > 0) {
        exportToCSV();
      } else {
        chrome.storage.local.get([CHECKPOINT_KEY], (res) => {
          const cp = res[CHECKPOINT_KEY];
          if (checkpointMatchesCurrentPage(cp)) exportToCSV(cp.data || []);
        });
      }
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

  // Nếu Facebook tự reload giữa phiên, content script mới tự nối lại checkpoint.
  setTimeout(() => {
    if (isRunning) return;
    chrome.storage.local.get([CHECKPOINT_KEY], (res) => {
      const cp = res[CHECKPOINT_KEY];
      if (!checkpointMatchesCurrentPage(cp) || !cp?.resumeOnReload || !cp?.data?.length) return;

      recoveryCycles = Number(cp.recoveryCycles || 0) + 1;
      if (recoveryCycles > MAX_RECOVERY_CYCLES) {
        resumeOnReload = false;
        facebookInterrupted = false;
        cp.resumeOnReload = false;
        cp.recoveryCycles = recoveryCycles;
        cp.status = 'paused';
        chrome.storage.local.set({ [CHECKPOINT_KEY]: cp });
        statusText = `Đã dừng phục hồi tự động sau ${MAX_RECOVERY_CYCLES} lần để tránh lặp vô hạn.`;
        pushState();
        if (cp.autoMode) chrome.runtime.sendMessage({ action: "AUTO_FINISHED", data: cp.data || [] });
        return;
      }

      isAutoMode = Boolean(cp.autoMode);
      autoPageLimit = Number(cp.autoPageLimit || autoPageLimit || rand(AUTO_PAGE_MIN, AUTO_PAGE_MAX));
      isRunning = true;
      facebookInterrupted = false;
      resumeOnReload = true;
      cp.resumeOnReload = true;
      cp.recoveryCycles = recoveryCycles;
      cp.status = 'running';
      statusText = `Tự phục hồi phiên ${recoveryCycles}/${MAX_RECOVERY_CYCLES} • đang nạp ${cp.count} profile đã lưu...`;
      pushState();
      chrome.storage.local.set({ [CHECKPOINT_KEY]: cp }, () => startAutoScroll());
    });
  }, 1200);
})();
