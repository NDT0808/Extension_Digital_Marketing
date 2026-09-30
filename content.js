let lastScores = { adult: 0, non: 0, puppy: 0 };
let lastStatus = "Đang khởi động...";
let model = null;
let isBotRunning = true;

function updateStatus(msg, isError = false) {
    console.log("[FB Dog Bot]", msg);
    lastStatus = msg;
    sendUpdateToPopup();
}

function sendUpdateToPopup() {
    chrome.runtime.sendMessage({
        action: "updatePopup",
        statusMsg: lastStatus,
        scores: lastScores,
        isRunning: isBotRunning
    }).catch(() => {});
}

// Lắng nghe yêu cầu từ Popup UI
chrome.runtime.onMessage.addListener((request, sender, sendResponse) => {
    if (request.action === "requestStatus") {
        sendResponse({
            statusMsg: lastStatus,
            scores: lastScores,
            isRunning: isBotRunning
        });
    } else if (request.action === "toggleBot") {
        isBotRunning = !isBotRunning;
        updateStatus(isBotRunning ? "Bot đã tiếp tục chạy." : "Đã TẠM DỪNG Bot.");
        sendUpdateToPopup();
    }
});

// 1. Tải Model AI
async function loadAIModel() {
    updateStatus("Đang thiết lập AI... (Nạp model ONNX tự train)");
    try {
        ort.env.wasm.wasmPaths = chrome.runtime.getURL('');
        const modelUrl = chrome.runtime.getURL('dog-model.onnx');
        model = await ort.InferenceSession.create(modelUrl, { executionProviders: ['wasm'] });
        updateStatus("✅ Model YOLO ONNX đã sẵn sàng! Đang quét video...");
    } catch (e) {
        updateStatus("Lỗi nạp model: " + e.message, true);
    }
}

// 2. Chụp khung hình Video đang phát và nhận diện
async function scanVideoForDog() {
    const videos = document.querySelectorAll('video');
    let video = null;
    for (let v of videos) {
        const rect = v.getBoundingClientRect();
        if (rect.width > 0 && rect.height > 0 && rect.top > -100 && rect.bottom > 0) {
            video = v;
            break;
        }
    }
    
    if (!video || !model) {
        return { isDog: false, label: "ĐANG TÌM KIẾM VIDEO..." };
    }

    try {
        const canvas = document.createElement('canvas');
        canvas.width = 224;
        canvas.height = 224;
        const ctx = canvas.getContext('2d', { willReadFrequently: true });
        
        ctx.fillStyle = 'black';
        ctx.fillRect(0, 0, 224, 224);
        
        const vW = video.videoWidth || video.clientWidth;
        const vH = video.videoHeight || video.clientHeight;
        
        const sX = vW * 0.10;
        const sY = vH * 0.20;
        const sW = vW * 0.80;
        const sH = vH * 0.55;
        
        const scale = Math.min(224 / sW, 224 / sH);
        const w = sW * scale;
        const h = sH * scale;
        const x = (224 - w) / 2;
        const y = (224 - h) / 2;
        
        ctx.drawImage(video, sX, sY, sW, sH, x, y, w, h);
        const imgData = ctx.getImageData(0, 0, 224, 224).data;

        const floatData = new Float32Array(3 * 224 * 224);
        for (let i = 0; i < 224 * 224; i++) {
            floatData[i] = imgData[i * 4] / 255.0;
            floatData[224 * 224 + i] = imgData[i * 4 + 1] / 255.0;
            floatData[2 * 224 * 224 + i] = imgData[i * 4 + 2] / 255.0;
        }
        
        const tensor = new ort.Tensor('float32', floatData, [1, 3, 224, 224]);
        
        const results = await model.run({ images: tensor });
        const output = results[Object.keys(results)[0]].data;
        
        let maxIndex = 0;
        let maxValue = output[0];
        for (let i = 1; i < output.length; i++) {
            if (output[i] > maxValue) {
                maxValue = output[i];
                maxIndex = i;
            }
        }
        
        lastScores = {
            adult: (output[0]*100).toFixed(1),
            non: (output[1]*100).toFixed(1),
            puppy: (output[2]*100).toFixed(1)
        };
        sendUpdateToPopup();
        
        console.log("Dự đoán YOLO - Adult:", lastScores.adult + "%, Non-dog:", lastScores.non + "%, Puppy:", lastScores.puppy + "%");
        
        let labelName = "RÁC (NON-DOG)";
        if (maxIndex === 0) labelName = "CHÓ LỚN (ADULT DOG)";
        if (maxIndex === 2) labelName = "CHÓ CON (PUPPY)";

        // Chốt kết quả: Nếu % cao nhất thuộc về chó (Adult hoặc Puppy)
        // Lưu ý: Đã khôi phục lại chốt chặn > 60% vì model mới của bạn chưa train xong!
        if ((maxIndex === 0 || maxIndex === 2) && maxValue > 0.60) {
            return { isDog: true, label: labelName };
        }
        return { isDog: false, label: labelName };
    } catch(e) {
        console.log("Lỗi quét video:", e);
        return { isDog: false, label: "ERROR" };
    }
}

// 3. Tự động thả tim và Follow
async function likeAndFollowReel() {
    updateStatus("❤️ Đang thả tim và Follow...");
    
    function isElementInViewport(el) {
        const rect = el.getBoundingClientRect();
        return rect.width > 0 && rect.height > 0 && rect.top >= 0 && rect.bottom <= (window.innerHeight || document.documentElement.clientHeight) + 100;
    }
    
    async function simulateClick(el, isFollow = false) {
        if (!el) return;
        
        let cursor = document.getElementById('fb-dog-bot-cursor');
        if (!cursor) {
            cursor = document.createElement('div');
            cursor.id = 'fb-dog-bot-cursor';
            cursor.style.cssText = `
                position: fixed; width: 24px; height: 24px;
                background-color: rgba(255, 0, 0, 0.8);
                border: 3px solid white; border-radius: 50%;
                pointer-events: none; z-index: 99999999;
                transition: all 0.4s ease-out; opacity: 0;
                box-shadow: 0 0 10px rgba(0,0,0,0.5);
                top: 50%; left: 50%; transform: translate(-50%, -50%);
            `;
            document.body.appendChild(cursor);
        }
        
        const rect = el.getBoundingClientRect();
        
        // Thủ thuật: Nút Follow thường nằm ở bên phải tên tác giả.
        // Ta sẽ click lệch về bên PHẢI của khung bao (cách mép phải 15px) để chắc chắn trúng nút thay vì trúng Tên!
        let targetX = rect.left + rect.width / 2;
        if (isFollow && rect.width > 50) {
            targetX = rect.left + rect.width - 15;
        }
        const targetY = rect.top + rect.height / 2;
        
        cursor.style.opacity = '1';
        cursor.style.top = `${targetY}px`;
        cursor.style.left = `${targetX}px`;
        
        await new Promise(r => setTimeout(r, 450));
        
        cursor.style.transform = 'translate(-50%, -50%) scale(0.6)';
        cursor.style.backgroundColor = isFollow ? 'rgba(0, 255, 0, 0.9)' : 'rgba(255, 20, 147, 0.9)';
        await new Promise(r => setTimeout(r, 150));
        
        // Bắn Full bộ sự kiện Mouse và Pointer (Bypass cơ chế chống Bot của React 18)
        try { el.click(); } catch(e){} // Kích hoạt click native trước
        
        ['pointerover', 'mouseover', 'pointerdown', 'mousedown', 'pointerup', 'mouseup', 'click'].forEach(evType => {
            el.dispatchEvent(new MouseEvent(evType, { 
                bubbles: true, 
                cancelable: true, 
                view: window,
                clientX: targetX,
                clientY: targetY,
                pointerId: 1
            }));
        });
        
        cursor.style.transform = 'translate(-50%, -50%) scale(1.3)';
        await new Promise(r => setTimeout(r, 200));
        cursor.style.opacity = '0';
    }
    
    // 3.1. Tìm và bấm nút Like (Thả tim) của video ĐANG CHIẾU
    const buttons = document.querySelectorAll('div[role="button"]');
    for (let btn of buttons) {
        let label = btn.getAttribute('aria-label') || "";
        if ((label === "Bỏ thích" || label === "Unlike" || label === "Remove Like") && isElementInViewport(btn)) {
            break;
        }
        if ((label === "Thích" || label === "Like") && isElementInViewport(btn)) {
            await simulateClick(btn, false);
            break;
        }
    }
    
    // 3.2. Tìm và bấm nút Follow (Theo dõi / Đăng ký)
    // Săn lùng bằng cả chữ hiển thị (innerText) và chữ ẩn (aria-label)
    const allTags = document.querySelectorAll('div[role="button"], span, div[aria-label]');
    let hasFollowed = false;
    
    // Quét 1 vòng kiểm tra xem đã Follow chưa
    for (let el of allTags) {
        let text = (el.innerText || "").trim().toLowerCase();
        let aria = (el.getAttribute('aria-label') || "").trim().toLowerCase();
        let combined = text + " " + aria;
        
        if (combined.length > 100) continue; 
        
        if (combined.includes("following") || combined.includes("đang theo dõi") || combined.includes("subscribed") || combined.includes("đã đăng ký")) {
            console.log("Kênh này đã Follow từ trước! Bỏ qua...");
            hasFollowed = true;
            break;
        }
    }
    
    // Nếu chưa Follow thì đi tìm nút để bấm
    if (!hasFollowed) {
        for (let el of allTags) {
            let text = (el.innerText || "").trim().toLowerCase();
            let aria = (el.getAttribute('aria-label') || "").trim().toLowerCase();
            let combined = text + " " + aria;
            
            if (combined.length > 80 || combined.trim() === "") continue;
            
            if ((combined.includes("follow") || combined.includes("theo dõi") || combined.includes("subscribe") || combined.includes("đăng ký")) && isElementInViewport(el)) {
                if (combined.includes("following") || combined.includes("đang theo dõi") || combined.includes("subscribed") || combined.includes("đã đăng ký")) continue;
                
                el.style.border = "4px solid red";
                el.style.borderRadius = "5px";
                
                await simulateClick(el, true);
                
                let parentBtn = el.closest('div[role="button"]');
                if (parentBtn && parentBtn !== el) {
                    ['mouseover', 'mousedown', 'mouseup', 'click'].forEach(ev => parentBtn.dispatchEvent(new MouseEvent(ev, { bubbles: true, cancelable: true })));
                }
                console.log("Đã bấm Follow thành công vào:", combined);
                break;
            }
        }
    }
}

// 4. Lướt sang video tiếp theo
function scrollToNextReel() {
    updateStatus("⬇️ Đang lướt sang video tiếp theo...");
    
    const videos = document.querySelectorAll('video');
    let currentVideoIndex = -1;
    for (let i = 0; i < videos.length; i++) {
        const rect = videos[i].getBoundingClientRect();
        if (rect.width > 0 && rect.height > 0 && rect.top > -100 && rect.bottom > 0) {
            currentVideoIndex = i;
            break;
        }
    }
    
    if (currentVideoIndex !== -1 && currentVideoIndex + 1 < videos.length) {
        videos[currentVideoIndex + 1].scrollIntoView({ behavior: 'smooth', block: 'center' });
        console.log("Đã cuộn tới video tiếp theo bằng scrollIntoView");
        return;
    }

    const buttons = document.querySelectorAll('div[role="button"]');
    for (let btn of buttons) {
        let label = (btn.getAttribute('aria-label') || "").toLowerCase();
        if (label.includes('next video') || label.includes('video tiếp theo') || label.includes('next card') || label.includes('tiếp')) {
            btn.click();
            return;
        }
    }

    if (currentVideoIndex !== -1) {
        let el = videos[currentVideoIndex];
        while(el) {
            if (el.scrollHeight > el.clientHeight) {
                el.scrollBy({ top: 800, behavior: 'smooth' });
                return;
            }
            el = el.parentElement;
        }
    }
}

// 5. Vòng lặp chính
async function botLoop() {
    if (!isBotRunning) {
        setTimeout(botLoop, 2000);
        return;
    }
    
    // Đợi Model load xong thì mới chạy
    if (!model) {
        setTimeout(botLoop, 2000);
        return;
    }
    
    let result = await scanVideoForDog();

    if (result.isDog) {
        updateStatus(`✅ KẾT LUẬN: ĐÂY LÀ ${result.label}! Đang Like & Follow...`);
        await likeAndFollowReel();
        await new Promise(r => setTimeout(r, 2000)); 
    } else {
        updateStatus(`❌ KẾT LUẬN: ĐÂY LÀ ${result.label}. Sẽ bỏ qua...`);
        await new Promise(r => setTimeout(r, 2000));
    }

    scrollToNextReel();
    setTimeout(botLoop, 4000); 
}

// Chạy bot
loadAIModel().then(() => {
    botLoop();
});
