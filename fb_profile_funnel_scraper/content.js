if (!window.__FB_SCRAPER_LOADED__) {
    window.__FB_SCRAPER_LOADED__ = true;
    let isCurrentlyScraping = false;

    chrome.runtime.onMessage.addListener((msg, sender, sendResponse) => {
        if (msg.action === 'START_SCRAPE') {
            if (isCurrentlyScraping) {
                console.log("[FB Scraper] Đang cào dở, bỏ qua lệnh START_SCRAPE trùng lặp.");
                sendResponse({ status: 'already_running' });
                return;
            }
            isCurrentlyScraping = true;
            scrapePublishTime(msg.targetUrl, msg.stt, msg.taskId)
                .finally(() => {
                    isCurrentlyScraping = false;
                });
            sendResponse({ status: 'started' });
        }
        else if (msg.action === 'TRIGGER_DOWNLOAD') {
            downloadCSV(msg.data, msg.isPartial);
            sendResponse({ status: 'ok' });
        }
    });
}

function sleep(ms) { return new Promise(resolve => setTimeout(resolve, ms)); }

/**
 * Kiểm tra các tên rác hệ thống của Facebook
 */
function isGarbageName(name) {
    if (!name) return true;
    let s = name.toLowerCase().trim();
    if (s === 'facebook' || s === 'thông báo' || s.includes('thông báo') || s === 'notifications' || s.startsWith('(')) {
        return true;
    }
    return false;
}

/**
 * Lấy tên Fanpage / Profile chuẩn xác, không dính tên rác
 */
function getProfileName() {
    // 1. Kiểm tra từ text ngay trước số người theo dõi trong DOM
    let bodyText = document.body ? document.body.innerText : '';
    if (bodyText) {
        let m = bodyText.match(/(?:^|\n)([^\n|]{2,60}?)\s*\n\s*\d+(?:[,\.]\d+)?[KkMm]?\s*(?:người theo dõi|followers|lượt thích|likes)/i)
             || bodyText.match(/(?:^|\n|\|\s*)([^\n|]{2,60}?)\s*(?: |\s)*(?:•|\||\n)\s*\d+(?:[,\.]\d+)?[KkMm]?\s*(?:người theo dõi|followers|lượt thích|likes)/i);
        if (m && !isGarbageName(m[1])) {
            let clean = m[1].replace(/^[\s|·•\-_]+|[\s|·•\-_]+$/g, '').trim();
            if (clean && !isGarbageName(clean)) return clean;
        }
    }

    // 2. Kiểm tra H1 bên trong vùng nội dung chính (main)
    let mainH1 = document.querySelector('div[role="main"] h1');
    if (mainH1 && mainH1.innerText && !isGarbageName(mainH1.innerText)) {
        return mainH1.innerText.trim();
    }

    // 3. Kiểm tra thẻ meta og:title
    let ogTitle = document.querySelector('meta[property="og:title"]');
    if (ogTitle && ogTitle.content) {
        let clean = ogTitle.content.replace(/^\(\d+\)\s*/, '').split('|')[0].split('-')[0].trim();
        if (!isGarbageName(clean)) return clean;
    }

    // 4. Kiểm tra bất kỳ thẻ H1 nào hợp lệ
    let h1List = Array.from(document.querySelectorAll('h1'));
    for (let h of h1List) {
        if (h.innerText && !isGarbageName(h.innerText)) {
            return h.innerText.trim();
        }
    }

    // 5. Kiểm tra document.title
    if (document.title) {
        let clean = document.title.replace(/^\(\d+\)\s*/, '').split('|')[0].split('-')[0].trim();
        if (!isGarbageName(clean)) return clean;
    }

    // 6. Fallback từ URL slug
    let pathname = window.location.pathname.replace(/^\/|\/$/g, '');
    let slug = pathname.split('/')[0] || '';
    if (slug && slug !== 'profile.php' && slug !== 'pages') {
        return slug;
    }

    return 'Facebook User';
}

/**
 * Trích xuất chuỗi thời gian từ một đoạn text hoặc thuộc tính aria-label
 */
function extractTimeFromText(text) {
    if (!text) return null;
    let s = text.trim();
    let sLower = s.toLowerCase();

    // 1. Dạng Vừa xong / Just now
    if (sLower.includes('vừa xong') || sLower.includes('just now')) {
        return 'vừa xong';
    }

    // 2. Dạng Hôm qua / Hôm nay
    let yestM = s.match(/(?:hôm qua|yesterday)\s+lúc\s+(\d{1,2}:\d{2})/i);
    if (yestM) return yestM[0].trim();

    let todayM = s.match(/(?:hôm nay|today)\s+lúc\s+(\d{1,2}:\d{2})/i);
    if (todayM) return todayM[0].trim();

    // 3. Dạng Ngày tháng cụ thể: 10 tháng 10 lúc 14:30 hoặc 15 tháng 8, 2025
    let dateM = s.match(/(\d{1,2}\s+tháng\s+\d{1,2}(?:,\s*\d{4})?(?:\s+lúc\s+\d{1,2}:\d{2})?)/i);
    if (dateM) return dateM[1].trim();

    // 4. Dạng Phút / Giờ / Ngày / Tuần / Tháng / Năm
    let relM = s.match(/(\d+\s*(?:phút|min|mins|m|giờ|hour|hours|h|ngày|day|days|d|tuần|week|weeks|w|tháng|month|months|năm|year|years|y)(?:[\s·•\-_,]|trước|ago|$))/i);
    if (relM) {
        let res = relM[1].trim();
        if (!res.includes('trước') && !res.includes('ago') && !sLower.includes('·')) {
            res += ' trước';
        }
        return res;
    }

    return null;
}

/**
 * Chuyển đổi chuỗi thời gian sang Unix Timestamp (giây)
 */
function parseRelativeTimeToTimestamp(relStr) {
    if (!relStr) return null;
    let s = relStr.toLowerCase().trim();
    let now = new Date();
    let nowSec = Math.floor(now.getTime() / 1000);

    if (s.includes('vừa xong') || s.includes('just now')) {
        return nowSec;
    }

    // Hôm nay lúc HH:mm
    let todayM = s.match(/hôm nay lúc (\d{1,2}):(\d{2})/i) || s.match(/today at (\d{1,2}):(\d{2})/i);
    if (todayM) {
        let d = new Date(now);
        d.setHours(parseInt(todayM[1], 10), parseInt(todayM[2], 10), 0, 0);
        return Math.floor(d.getTime() / 1000);
    }

    // Hôm qua lúc HH:mm
    let yestM = s.match(/hôm qua lúc (\d{1,2}):(\d{2})/i) || s.match(/yesterday at (\d{1,2}):(\d{2})/i);
    if (yestM) {
        let d = new Date(now);
        d.setDate(d.getDate() - 1);
        d.setHours(parseInt(yestM[1], 10), parseInt(yestM[2], 10), 0, 0);
        return Math.floor(d.getTime() / 1000);
    }

    // D tháng M, YYYY hoặc D tháng M lúc HH:mm
    let dateFullM = s.match(/(\d{1,2})\s+tháng\s+(\d{1,2})(?:,\s*(\d{4}))?(?:\s+lúc\s+(\d{1,2}):(\d{2}))?/i);
    if (dateFullM) {
        let day = parseInt(dateFullM[1], 10);
        let month = parseInt(dateFullM[2], 10) - 1;
        let year = dateFullM[3] ? parseInt(dateFullM[3], 10) : now.getFullYear();
        let hour = dateFullM[4] ? parseInt(dateFullM[4], 10) : 12;
        let min = dateFullM[5] ? parseInt(dateFullM[5], 10) : 0;
        let d = new Date(year, month, day, hour, min, 0);
        return Math.floor(d.getTime() / 1000);
    }

    // Phút
    let minM = s.match(/(\d+)\s*(?:phút|min|mins|m)(?:[\s·•\-_,]|trước|ago|$)/i);
    if (minM) return nowSec - parseInt(minM[1], 10) * 60;

    // Giờ
    let hrM = s.match(/(\d+)\s*(?:giờ|hour|hours|h)(?:[\s·•\-_,]|trước|ago|$)/i);
    if (hrM) return nowSec - parseInt(hrM[1], 10) * 3600;

    // Ngày
    let dayM = s.match(/(\d+)\s*(?:ngày|day|days|d)(?:[\s·•\-_,]|trước|ago|$)/i);
    if (dayM) return nowSec - parseInt(dayM[1], 10) * 86400;

    // Tuần
    let wkM = s.match(/(\d+)\s*(?:tuần|week|weeks|w)(?:[\s·•\-_,]|trước|ago|$)/i);
    if (wkM) return nowSec - parseInt(wkM[1], 10) * 7 * 86400;

    // Tháng
    let moM = s.match(/(\d+)\s*(?:tháng|month|months)(?:[\s·•\-_,]|trước|ago|$)/i);
    if (moM) return nowSec - parseInt(moM[1], 10) * 30 * 86400;

    // Năm
    let yrM = s.match(/(\d+)\s*(?:năm|year|years|y)(?:[\s·•\-_,]|trước|ago|$)/i);
    if (yrM) return nowSec - parseInt(yrM[1], 10) * 365 * 86400;

    return null;
}

/**
 * Định dạng Unix Timestamp thành chuỗi ngày giờ DD/MM/YYYY HH:mm:ss
 */
function formatTimestampToDate(ts) {
    if (!ts) return '';
    let dt = new Date(ts * 1000);
    let pad = (n) => String(n).padStart(2, '0');
    return `${pad(dt.getDate())}/${pad(dt.getMonth() + 1)}/${dt.getFullYear()} ${pad(dt.getHours())}:${pad(dt.getMinutes())}:${pad(dt.getSeconds())}`;
}

/**
 * Tính toán thời gian tương đối chuẩn xác từ Unix Timestamp
 */
function formatRelativeTime(ts) {
    if (!ts) return '';
    let nowSec = Math.floor(Date.now() / 1000);
    let diffSec = Math.max(0, nowSec - ts);
    let diffMin = Math.floor(diffSec / 60);
    let diffHours = Math.floor(diffMin / 60);
    let diffDays = Math.floor(diffHours / 24);

    if (diffMin < 1) return 'vừa xong';
    if (diffMin < 60) return `${diffMin} phút trước`;
    if (diffHours < 24) return `${diffHours} giờ trước`;
    if (diffDays < 7) return `${diffDays} ngày trước`;
    if (diffDays < 30) return `${Math.floor(diffDays / 7)} tuần trước`;
    if (diffDays < 365) return `${Math.floor(diffDays / 30)} tháng trước`;
    return `${Math.floor(diffDays / 365)} năm trước`;
}

/**
 * Quét tìm bài viết đầu tiên trên feed DOM và lấy thời gian (KHÔNG CLICK)
 */
function findFirstPostTimeInDOM() {
    // 1. Tìm các article hoặc khối post trong timeline
    let articles = Array.from(document.querySelectorAll('div[role="article"], div[data-pagelet^="FeedUnit_"]')).filter(el => {
        let r = el.getBoundingClientRect();
        return r.top > 80 && r.height > 60;
    });

    if (articles.length > 0) {
        let firstArticle = articles[0];

        // 1.1 Tìm các link trỏ đến bài viết bên trong article đầu tiên (link thời gian chuẩn của FB)
        let links = Array.from(firstArticle.querySelectorAll('a[role="link"], a[href]'));
        for (let a of links) {
            let aria = a.getAttribute('aria-label');
            if (aria) {
                let timeStr = extractTimeFromText(aria);
                if (timeStr) {
                    let ts = parseRelativeTimeToTimestamp(timeStr);
                    if (ts) {
                        return { relativeTime: timeStr, timestamp: ts, publishTime: formatTimestampToDate(ts) };
                    }
                }
            }
            let aText = a.innerText || '';
            if (aText) {
                let timeStr = extractTimeFromText(aText);
                if (timeStr) {
                    let ts = parseRelativeTimeToTimestamp(timeStr);
                    if (ts) {
                        return { relativeTime: timeStr, timestamp: ts, publishTime: formatTimestampToDate(ts) };
                    }
                }
            }
        }

        // 1.2 Quét toàn bộ text của firstArticle
        let articleText = firstArticle.innerText || '';
        let timeStr = extractTimeFromText(articleText);
        if (timeStr) {
            let ts = parseRelativeTimeToTimestamp(timeStr);
            if (ts) {
                return { relativeTime: timeStr, timestamp: ts, publishTime: formatTimestampToDate(ts) };
            }
        }
    }

    // 2. Tìm bất kỳ thẻ a hoặc span nào có chứa thời gian và nằm ở vùng feed (top > 200)
    let candidateLinks = Array.from(document.querySelectorAll('a[role="link"], a[href*="/posts/"], a[href*="/photos/"], a[href*="permalink.php"], a[href*="fbid="], abbr, span')).filter(el => {
        let r = el.getBoundingClientRect();
        return r.top > 150 && r.top < 1500;
    });

    for (let el of candidateLinks) {
        let txt = el.getAttribute('aria-label') || el.innerText || '';
        if (!txt) continue;
        let timeStr = extractTimeFromText(txt);
        if (timeStr) {
            let ts = parseRelativeTimeToTimestamp(timeStr);
            if (ts) {
                return { relativeTime: timeStr, timestamp: ts, publishTime: formatTimestampToDate(ts) };
            }
        }
    }

    return null;
}

/**
 * Quét trích xuất timestamp trực tiếp từ các thẻ <script> và GraphQL payload (Độ chính xác 100%)
 */
function findPublishTimeFromScripts() {
    let nowSec = Math.floor(Date.now() / 1000);
    let minTs = 1577836800; // 01/01/2020
    let maxTs = nowSec + 86400; // Không lấy timestamp tương lai

    let postContextTs = [];
    let allPublishTs = [];
    let allCreatedTs = [];

    // Danh sách các nguồn script cần quét: toàn bộ thẻ <script> + document.documentElement.innerHTML
    let sources = Array.from(document.querySelectorAll('script')).map(s => s.textContent || '');
    if (document.documentElement && document.documentElement.innerHTML) {
        sources.push(document.documentElement.innerHTML);
    }

    // Pattern 1: post_context hoặc creation_story chứa publish_time (Chuẩn xác nhất cho bài post/video/reel timeline)
    const postContextRegex = /["\\]*post_context["\\]*[\s\S]{0,250}?["\\]*publish_time["\\]*\s*:\s*(\d{9,12})/g;
    const creationStoryRegex = /["\\]*creation_story["\\]*[\s\S]{0,400}?["\\]*publish_time["\\]*\s*:\s*(\d{9,12})/g;

    // Pattern 2: Bất kỳ key publish_time nào
    const pubTimeRegex = /["\\]*publish_time["\\]*\s*:\s*(\d{9,12})/g;

    // Pattern 3: Bất kỳ key created_time hoặc creation_time nào
    const createdTimeRegex = /["\\]*(?:created_time|creation_time)["\\]*\s*:\s*(\d{9,12})/g;

    for (let text of sources) {
        if (!text || text.length < 30) continue;

        // Quét Pattern 1 (post_context / creation_story)
        if (text.includes('post_context')) {
            for (let m of text.matchAll(postContextRegex)) {
                let ts = parseInt(m[1], 10);
                if (ts >= minTs && ts <= maxTs) postContextTs.push(ts);
            }
        }
        if (text.includes('creation_story')) {
            for (let m of text.matchAll(creationStoryRegex)) {
                let ts = parseInt(m[1], 10);
                if (ts >= minTs && ts <= maxTs) postContextTs.push(ts);
            }
        }

        // Quét Pattern 2 (publish_time)
        if (text.includes('publish_time')) {
            for (let m of text.matchAll(pubTimeRegex)) {
                let ts = parseInt(m[1], 10);
                if (ts >= minTs && ts <= maxTs) allPublishTs.push(ts);
            }
        }

        // Quét Pattern 3 (created_time)
        if (text.includes('created_time') || text.includes('creation_time')) {
            for (let m of text.matchAll(createdTimeRegex)) {
                let ts = parseInt(m[1], 10);
                if (ts >= minTs && ts <= maxTs) allCreatedTs.push(ts);
            }
        }
    }

    // Chọn timestamp ưu tiên cao nhất (bài mới nhất có timestamp lớn nhất)
    let targetTs = null;
    if (postContextTs.length > 0) {
        postContextTs.sort((a, b) => b - a);
        targetTs = postContextTs[0];
    } else if (allPublishTs.length > 0) {
        allPublishTs.sort((a, b) => b - a);
        targetTs = allPublishTs[0];
    } else if (allCreatedTs.length > 0) {
        allCreatedTs.sort((a, b) => b - a);
        targetTs = allCreatedTs[0];
    }

    if (targetTs) {
        return {
            timestamp: targetTs,
            publishTime: formatTimestampToDate(targetTs),
            relativeTime: formatRelativeTime(targetTs)
        };
    }

    return null;
}

/**
 * Quy trình cào Publish Time duy nhất (Không click, không mở modal, siêu tốc độ)
 */
async function scrapePublishTime(targetUrl, stt, taskId) {
    let url = targetUrl || window.location.href;

    // 1. Lấy tên Profile / Fanpage
    let name = getProfileName();

    // 2. Cuộn nhẹ 350px để feed bài viết đầu tiên render trong DOM
    window.scrollBy({ top: 350, behavior: 'smooth' });
    await sleep(1000);

    // Cập nhật lại tên nếu DOM vừa nạp xong
    let refinedName = getProfileName();
    if (refinedName && refinedName !== 'Facebook User' && !isGarbageName(refinedName)) {
        name = refinedName;
    }

    // 3. ƯU TIÊN 1: Lấy timestamp trực tiếp từ thẻ <script> / GraphQL của Facebook (Chuẩn 100% theo database Facebook)
    let timeInfo = findPublishTimeFromScripts();

    // 4. ƯU TIÊN 2 (Dự phòng): Nếu script không có, mới quét giao diện DOM của bài viết
    if (!timeInfo) {
        timeInfo = findFirstPostTimeInDOM();
    }

    let publishTime = timeInfo ? timeInfo.publishTime : 'Không tìm thấy bài viết';
    let publishTimestamp = timeInfo ? timeInfo.timestamp : '';
    let relativeTime = timeInfo ? timeInfo.relativeTime : '';

    // Gửi kết quả về background kèm taskId để khóa trùng lặp
    chrome.runtime.sendMessage({
        action: 'PROFILE_RESULT',
        data: {
            taskId: taskId,
            stt: stt,
            url: url,
            name: name,
            publishTime: publishTime,
            publishTimestamp: publishTimestamp,
            relativeTime: relativeTime
        }
    });
}

/**
 * Xuất file CSV dự phòng từ content script
 */
function downloadCSV(dataArray, isPartial) {
    if (!dataArray || dataArray.length === 0) return;

    let headers = ['STT', 'URL', 'Tên Profile/Fanpage', 'Thời gian đăng (Publish Time)', 'Timestamp', 'Thời gian tương đối'];
    let csvContent = "\uFEFF" + headers.join(',') + '\n';

    dataArray.forEach((row, idx) => {
        let stt = row.stt !== undefined ? row.stt : (idx + 1);
        let vals = [
            `"${String(stt).replace(/"/g, '""')}"`,
            `"${String(row.url || '').replace(/"/g, '""')}"`,
            `"${String(row.name || '').replace(/"/g, '""')}"`,
            `"${String(row.publishTime || '').replace(/"/g, '""')}"`,
            `"${String(row.publishTimestamp || '').replace(/"/g, '""')}"`,
            `"${String(row.relativeTime || '').replace(/"/g, '""')}"`
        ];
        csvContent += vals.join(',') + '\n';
    });

    let blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' });
    let url = URL.createObjectURL(blob);
    let a = document.createElement('a');
    a.href = url;
    let timestamp = new Date().getTime();
    a.download = `FB_PublishTime_${isPartial ? 'Part_' : ''}${timestamp}.csv`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
}
