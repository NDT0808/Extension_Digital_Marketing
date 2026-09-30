document.addEventListener("DOMContentLoaded", () => {
    const statusText = document.getElementById("status-text");
    const barAdult = document.getElementById("bar-adult");
    const barPuppy = document.getElementById("bar-puppy");
    const barNone = document.getElementById("bar-none");
    const pctAdult = document.getElementById("pct-adult");
    const pctPuppy = document.getElementById("pct-puppy");
    const pctNone = document.getElementById("pct-none");
    const toggleBtn = document.getElementById("toggle-btn");

    let isRunning = true;

    // Lấy trạng thái hiện tại ngay khi mở popup
    chrome.tabs.query({ active: true, currentWindow: true }, function (tabs) {
        if (tabs.length > 0) {
            chrome.tabs.sendMessage(tabs[0].id, { action: "requestStatus" }, (response) => {
                if (chrome.runtime.lastError) {
                    // Không kết nối được tới content script (không ở trang FB Reels)
                    statusText.innerText = "Chưa nhận diện được. Hãy mở trang Facebook Reels.";
                    return;
                }
                if (response) {
                    updateUI(response);
                }
            });
        }
    });

    // Lắng nghe cập nhật thời gian thực từ content.js
    chrome.runtime.onMessage.addListener((msg, sender, sendResponse) => {
        if (msg.action === "updatePopup") {
            updateUI(msg);
        }
    });

    function updateUI(data) {
        if (data.statusMsg) statusText.innerText = data.statusMsg;
        if (data.scores) {
            barAdult.style.width = `${data.scores.adult}%`;
            pctAdult.innerText = `${data.scores.adult}%`;

            barPuppy.style.width = `${data.scores.puppy}%`;
            pctPuppy.innerText = `${data.scores.puppy}%`;

            barNone.style.width = `${data.scores.non}%`;
            pctNone.innerText = `${data.scores.non}%`;
        }
        if (data.isRunning !== undefined) {
            isRunning = data.isRunning;
            toggleBtn.innerText = isRunning ? "TẠM DỪNG BOT" : "TIẾP TỤC CHẠY";
            toggleBtn.className = isRunning ? "btn" : "btn off";
        }
    }

    // Gửi lệnh Pause/Resume xuống content.js
    toggleBtn.addEventListener("click", () => {
        chrome.tabs.query({ active: true, currentWindow: true }, function (tabs) {
            if (tabs.length > 0) {
                chrome.tabs.sendMessage(tabs[0].id, { action: "toggleBot" });
            }
        });
    });
});
