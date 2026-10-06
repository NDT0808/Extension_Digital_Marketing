document.addEventListener('DOMContentLoaded', () => {
    const fileInput = document.getElementById('csv-file');
    const startBtn = document.getElementById('btn-start');
    const stopBtn = document.getElementById('btn-stop');
    const exportBtn = document.getElementById('btn-export');
    const clearBtn = document.getElementById('btn-clear');
    const statusText = document.getElementById('status-text');

    function updateUI(s) {
        let text = s.status || 'Ready.';
        if (s.queue && s.queue.length > 0) {
            text += ` (${s.index || 0}/${s.queue.length})`;
        }
        statusText.innerText = text;
        startBtn.disabled = s.running;
        stopBtn.disabled = !s.running;
        
        if (s.results && s.results.length > 0) {
            exportBtn.style.display = 'block';
            exportBtn.innerText = `EXPORT CSV (${s.results.length})`;
        } else {
            exportBtn.style.display = 'none';
        }
    }

    async function loadState() {
        const s = await chrome.storage.local.get(['queue', 'index', 'results', 'running', 'status']);
        updateUI(s);
    }

    loadState();
    setInterval(loadState, 1000);

    // Simple CSV parser for standard fields enclosed in quotes
    function parseCSV(text) {
        let lines = text.split('\n');
        let urls = [];
        for (let line of lines) {
            line = line.trim();
            if (!line) continue;
            // A simple regex to extract the URL: assuming URL is https://www.facebook.com/...
            let match = line.match(/https?:\/\/(www\.)?facebook\.com\/[^\s",]+/i);
            if (match) {
                let url = match[0];
                // Clean URL
                try {
                    let u = new URL(url);
                    u.searchParams.delete('sk');
                    u.searchParams.delete('mibextid');
                    u.pathname = u.pathname.replace(/\/reels_tab\/?$/i, '/').replace(/\/reels\/?$/i, '/');
                    urls.push(u.href);
                } catch(e) {}
            }
        }
        return urls;
    }

    fileInput.addEventListener('change', (e) => {
        const file = e.target.files[0];
        if (!file) return;
        const reader = new FileReader();
        reader.onload = async (evt) => {
            const urls = parseCSV(evt.target.result);
            if (urls.length === 0) {
                alert("No valid Facebook URLs found in CSV!");
                return;
            }
            const s = await chrome.storage.local.get(['queue']);
            let q = s.queue || [];
            urls.forEach(u => {
                if (!q.includes(u)) q.push(u);
            });
            await chrome.storage.local.set({ queue: q, status: 'Data loaded.' });
            alert(`Loaded ${urls.length} URLs!`);
            loadState();
        };
        reader.readAsText(file);
    });

    startBtn.addEventListener('click', async () => {
        const s = await chrome.storage.local.get(['queue', 'index']);
        if (s.queue && s.queue.length > 0 && (s.index || 0) < s.queue.length) {
            await chrome.storage.local.set({ running: true, status: 'Running...' });
            chrome.runtime.sendMessage({ action: 'RUN' });
            loadState();
        } else {
            alert("Queue is empty or finished. Please upload a CSV.");
        }
    });

    stopBtn.addEventListener('click', async () => {
        await chrome.storage.local.set({ running: false, status: 'Stopped.' });
        loadState();
    });

    clearBtn.addEventListener('click', async () => {
        if (confirm("Are you sure you want to clear all data?")) {
            await chrome.storage.local.set({ queue: [], results: [], index: 0, status: 'Cleared', running: false });
            fileInput.value = '';
            loadState();
        }
    });

    exportBtn.addEventListener('click', async () => {
        const s = await chrome.storage.local.get(['results']);
        if (!s.results || s.results.length === 0) return;
        
        const head = [
            'STT', 'Link Profile', 'Tên khách hàng', 'FN', 'LN', 'Loại trang', 
            'Người theo dõi', 'Lượt thích', 'Bạn bè', 'Số lượng đánh giá', 'Giới thiệu',
            'Website', 'Email', 'Điện thoại', 'Instagram', 'Tiktok', 'Youtube', 'Zip', 'Country', 'State'
        ];
        const esc = (v) => `"${String(v ?? '').replace(/"/g, '""')}"`;
        let csv = '\uFEFF' + head.join(',') + '\n';
        s.results.forEach((r, i) => {
            csv += [
                i + 1, r.finalUrl || r.sourceUrl, r.name, r.fn, r.ln, r.category,
                r.followers, r.likes, r.friends, r.reviews, r.bio,
                r.website, r.email, r.phone, r.instagram || '', r.tiktok || '', r.youtube || '',
                r.zip, r.country, r.st
            ].map(esc).join(',') + '\n';
        });
        const url = URL.createObjectURL(new Blob([csv], { type: 'text/csv;charset=utf-8;' }));
        const a = document.createElement('a');
        a.href = url;
        a.download = `fb_contacts_${Date.now()}.csv`;
        document.body.appendChild(a);
        a.click();
        a.remove();
        setTimeout(() => URL.revokeObjectURL(url), 1000);
    });
});
