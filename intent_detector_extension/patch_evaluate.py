with open('c:/Users/ASUS/Downloads/Marketing_Pet&Grass/intent_detector_extension/dashboard.js', 'r', encoding='utf-8') as f:
    content = f.read()

new_evaluate = """function evaluateFinalResult(tabId, state) {
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
"""

start_str = "function evaluateFinalResult(tabId, state) {"
end_str = "function getBadge(isYes) {"

if start_str in content and end_str in content:
    before = content[:content.find(start_str)]
    after = content[content.find(end_str):]
    
    with open('c:/Users/ASUS/Downloads/Marketing_Pet&Grass/intent_detector_extension/dashboard.js', 'w', encoding='utf-8') as f:
        f.write(before + new_evaluate + "\n  " + after)
    print('Patch evaluateFinalResult applied successfully')
else:
    print('String anchors not found')
