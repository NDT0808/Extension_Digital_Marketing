from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import uvicorn
import base64
import json
import os
import torch
from transformers import Qwen2VLForConditionalGeneration, AutoProcessor
from qwen_vl_utils import process_vision_info

app = FastAPI()

# Bật CORS để Chrome Extension (chạy trên trang facebook.com) có thể gọi được API local
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)
print("Đang nạp mô hình Qwen2-VL-2B-Instruct vào GPU (Bản siêu nhẹ chống tràn RAM)...")
model = Qwen2VLForConditionalGeneration.from_pretrained(
    "Qwen/Qwen2-VL-2B-Instruct",
    torch_dtype="auto", 
    device_map="auto"
)
processor = AutoProcessor.from_pretrained("Qwen/Qwen2-VL-2B-Instruct")

# Model nhận Data từ Extension
class ImageData(BaseModel):
    base64_str: str

@app.post("/analyze_post")
async def analyze_post(data: ImageData):
    try:
        # Xử lý chuỗi base64 từ Chrome Extension (bỏ phần data:image/jpeg;base64, đi)
        base64_data = data.base64_str.split(",")[1] if "," in data.base64_str else data.base64_str
        image_bytes = base64.b64decode(base64_data)
        
        import time
        # Tạo thư mục screenshots nếu chưa có
        if not os.path.exists("screenshots"):
            os.makedirs("screenshots")
            
        timestamp = int(time.time() * 1000)
        temp_img_path = f"screenshots/screenshot_{timestamp}.jpg"
        
        with open(temp_img_path, "wb") as f:
            f.write(image_bytes)

        system_prompt = "Bạn là một AI trích xuất dữ liệu. Hãy phân tích bức ảnh chụp màn hình bài đăng mạng xã hội này và trả về JSON."
        user_prompt = """
        Hãy trích xuất các thông tin sau từ bài viết và trả về JSON:
        {
          "post_date": "Ngày đăng bài",
          "likes": "Số lượt thích",
          "comments": "Số lượt bình luận",
          "shares": "Số lượt chia sẻ"
        }
        Chỉ trả về JSON hợp lệ.
        """

        messages = [
            {"role": "user", "content": [{"type": "image", "image": temp_img_path}, {"type": "text", "text": f"{system_prompt}\n{user_prompt}"}]}
        ]

        text = processor.apply_chat_template(messages, tokenize=False, add_generation_prompt=True)
        image_inputs, video_inputs = process_vision_info(messages)
        
        inputs = processor(text=[text], images=image_inputs, videos=video_inputs, padding=True, return_tensors="pt").to(model.device)

        generated_ids = model.generate(**inputs, max_new_tokens=256)
        generated_ids_trimmed = [out_ids[len(in_ids):] for in_ids, out_ids in zip(inputs.input_ids, generated_ids)]
        output_text = processor.batch_decode(generated_ids_trimmed, skip_special_tokens=True, clean_up_tokenization_spaces=False)[0]

        clean_json = output_text.replace("```json", "").replace("```", "").strip()
        result = json.loads(clean_json)
        return result

    except Exception as e:
        print("Lỗi:", str(e))
        return {"post_date": None, "likes": 0, "comments": 0, "shares": 0}

if __name__ == "__main__":
    # Khởi chạy server ở cổng 8000
    uvicorn.run(app, host="127.0.0.1", port=8000)
