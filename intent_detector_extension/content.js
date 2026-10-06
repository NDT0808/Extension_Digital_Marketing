chrome.runtime.onMessage.addListener((request, sender, sendResponse) => {
  if (request.action === "scan_intent") {
    try {
      const result = analyzePage();
      sendResponse({ success: true, data: result });
    } catch (error) {
      sendResponse({ success: false, error: error.message });
    }
  }
  return true; 
});

function analyzePage() {
  const keywords = {
    selling_dogs: [
        "puppies for sale", "available puppies", "upcoming litters", "buy a puppy",
        "reserve a puppy", "puppy application", "health guarantee", "akc registered",
        "place a deposit", "adopt a puppy", "our dogs", "sires and dams",
        "puppies expected", "stud service", "adoption fee"
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
    ]
  };

  // 1. Lấy toàn bộ nội dung text hiển thị trên trang hiện tại
  // Dùng document.body.innerText sẽ lấy được nội dung đã render bởi React/Vue
  const textContent = document.body.innerText.toLowerCase();
  
  // 2. Tìm xem có thẻ form nào không
  const formElements = document.querySelectorAll("form, iframe[src*='form'], iframe[src*='typeform'], iframe[src*='docs.google.com/forms']");
  let has_form_tag = formElements.length > 0;

  let sells_dogs = false;
  let has_form = false;
  let has_take_home_kit = false;

  // 3. So khớp từ khóa
  for (let kw of keywords.selling_dogs) {
    if (textContent.includes(kw)) {
      sells_dogs = true;
      break;
    }
  }

  if (has_form_tag) {
    has_form = true;
  } else {
    for (let kw of keywords.forms) {
      if (textContent.includes(kw)) {
        has_form = true;
        break;
      }
    }
  }

  for (let kw of keywords.take_home_kit) {
    if (textContent.includes(kw)) {
      has_take_home_kit = true;
      break;
    }
  }

  return {
    sells_dogs,
    has_form,
    has_take_home_kit
  };
}
