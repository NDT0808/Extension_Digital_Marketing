chrome.runtime.onMessage.addListener((request, sender, sendResponse) => {
  if (request.action === "scan_page_step") {
    performScan()
      .then(data => sendResponse({ success: true, data }))
      .catch(e => sendResponse({ success: false, error: e.toString() }));
  }
  return true;
});

async function performScan() {
  // Cuộn xuống từ từ để kích hoạt lazy loading và cho người dùng thấy trang đang được phân tích
  await new Promise((resolve) => {
    let totalHeight = 0;
    let distance = 400; // Mỗi bước cuộn 400px
    let timer = setInterval(() => {
      let scrollHeight = document.body.scrollHeight;
      window.scrollBy(0, distance);
      totalHeight += distance;

      // Dừng lại khi chạm đáy, hoặc đã cuộn quá 5000px (để tránh vô tận)
      if (totalHeight >= scrollHeight - window.innerHeight || totalHeight > 5000) {
        clearInterval(timer);
        resolve();
      }
    }, 250); // Dừng 250ms giữa các lần cuộn để nó cuộn chậm lại
  });

  // Chờ 0.5s sau khi cuộn đến đáy để JS có thể render thêm 
  await new Promise(r => setTimeout(r, 500));

  // Gom chữ trên trang
  const textContent = document.body.innerText.toLowerCase();

  // Tìm form
  const formElements = document.querySelectorAll("form, iframe[src*='form'], iframe[src*='typeform'], iframe[src*='docs.google.com/forms']");
  const has_form_tag = formElements.length > 0;

  // Tìm các thẻ link (nav bar) để gửi về cho Dashboard phân tích trang con
  const links = Array.from(document.querySelectorAll("a[href]")).map(a => a.href);

  return {
    text: textContent,
    has_form: has_form_tag,
    links: links
  };
}
