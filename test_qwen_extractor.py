import torch
from transformers import Qwen2VLForConditionalGeneration, AutoProcessor
import json
import time

print("[*] 1. Khởi tạo mô hình Qwen2-VL-2B-Instruct từ cache nội bộ...")
t0 = time.time()
model_id = "Qwen/Qwen2-VL-2B-Instruct"

# Sử dụng bfloat16 hoặc float16 trên RTX 3050 Laptop
model = Qwen2VLForConditionalGeneration.from_pretrained(
    model_id,
    torch_dtype=torch.float16,
    device_map="auto"
)
processor = AutoProcessor.from_pretrained(model_id)
print(f"[✓] Đã nạp Qwen2-VL-2B lên GPU trong {time.time() - t0:.2f}s!")

# Đoạn văn bản thu thập được từ website https://www.hohai.ltd
sample_text = """
HOHAI COMMERCIAL - Creating real value for customers.
Phone: +84 847131400
HoHai Design, Development and Manufacturing
Office Address: TM29 Florita, Đ. D4, Khu dân cư Him Lam, Tân Hưng, Hồ Chí Minh 700000
Factory Address: ND 026 Phu, An Commune,Ben Cat, Binh Duong,Vietnam
WhatsApp: +84 84 713 1400
Email: triho_j@enjoymediavn.com
Copyright 2026 HOHAI, Ltd. All Rights Reserved.
HOHAI is based in Binh Duong Province, Vietnam, with over 15 years of experience in the design and manufacturing of metal products.
Founder & Director: Tri Ho
"""

prompt = f"""Dưới đây là nội dung trang web:
\"\"\"{sample_text}\"\"\"

Hãy đóng vai chuyên gia bóc tách dữ liệu doanh nghiệp và trích xuất thông tin theo định dạng JSON chuẩn xác với các trường sau:
- "owner_name": Tên chủ doanh nghiệp / người sáng lập / giám đốc (hoặc null nếu không có)
- "phone": Số điện thoại liên hệ chính thức
- "email": Địa chỉ email
- "address": Địa chỉ cụ thể
- "city": Tỉnh / Thành phố
- "country": Quốc gia

Chỉ trả về chuỗi JSON duy nhất, không giải thích thêm:"""

messages = [
    {
        "role": "user",
        "content": [
            {"type": "text", "text": prompt}
        ]
    }
]

text = processor.apply_chat_template(messages, tokenize=False, add_generation_prompt=True)
inputs = processor(text=[text], padding=True, return_tensors="pt").to("cuda")

print("[*] 2. Đang suy luận trích xuất thông tin bằng Transformer...")
t_gen = time.time()
with torch.no_grad():
    generated_ids = model.generate(**inputs, max_new_tokens=256)
    generated_ids_trimmed = [
        out_ids[len(in_ids):] for in_ids, out_ids in zip(inputs.input_ids, generated_ids)
    ]
    response = processor.batch_decode(
        generated_ids_trimmed, skip_special_tokens=True, clean_up_tokenization_spaces=False
    )[0]

print(f"[✓] Thời gian suy luận: {time.time() - t_gen:.2f}s")
print("\n[KẾT QUẢ TRANSFORMER QWEN2-VL]:")
print(response)
