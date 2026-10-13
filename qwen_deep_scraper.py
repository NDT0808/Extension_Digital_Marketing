import torch
import json
from transformers import Qwen2VLForConditionalGeneration, AutoProcessor
from qwen_vl_utils import process_vision_info

print("Đang nạp mô hình Qwen2-VL-7B-Instruct vào GPU...")
# Bước 1: Load mô hình và bộ xử lý
model = Qwen2VLForConditionalGeneration.from_pretrained(
    "Qwen/Qwen2-VL-7B-Instruct",
    torch_dtype="auto", 
    device_map="auto" # Tự động nhận diện GPU/CPU
)
processor = AutoProcessor.from_pretrained("Qwen/Qwen2-VL-7B-Instruct")

def extract_post_stats(image_path):
    """
    Hàm này nhận ảnh chụp màn hình bài đăng Facebook
    Và trả về dict chứa: Ngày đăng, Likes, Comments, Shares
    """
    
    # Ép mô hình trả về định dạng JSON nghiêm ngặt
    system_prompt = "Bạn là một AI trích xuất dữ liệu. Hãy phân tích bức ảnh chụp màn hình bài đăng mạng xã hội này và trả về dữ liệu định dạng JSON chính xác."
    user_prompt = """
    Hãy trích xuất các thông tin sau từ bài viết và trả về dưới dạng JSON với các keys sau:
    {
      "post_date": "Ngày đăng bài (ví dụ: '1 ngày trước', '10 tháng 4', v.v. Không có trả về null)",
      "likes": "Số lượt thích dưới dạng số nguyên (ví dụ: 1200, 15, 0)",
      "comments": "Số lượt bình luận dưới dạng số nguyên (ví dụ: 5, 0)",
      "shares": "Số lượt chia sẻ dưới dạng số nguyên (ví dụ: 2, 0)"
    }
    Chỉ trả về chuỗi JSON hợp lệ, không kèm theo văn bản nào khác.
    """

    messages = [
        {
            "role": "user",
            "content": [
                {"type": "image", "image": image_path},
                {"type": "text", "text": f"{system_prompt}\n{user_prompt}"},
            ],
        }
    ]

    # Chuẩn bị đầu vào
    text = processor.apply_chat_template(messages, tokenize=False, add_generation_prompt=True)
    image_inputs, video_inputs = process_vision_info(messages)
    
    inputs = processor(
        text=[text],
        images=image_inputs,
        videos=video_inputs,
        padding=True,
        return_tensors="pt"
    ).to(model.device)

    # Chạy Inference (Suy luận)
    generated_ids = model.generate(**inputs, max_new_tokens=256)
    generated_ids_trimmed = [
        out_ids[len(in_ids):] for in_ids, out_ids in zip(inputs.input_ids, generated_ids)
    ]
    
    output_text = processor.batch_decode(
        generated_ids_trimmed, skip_special_tokens=True, clean_up_tokenization_spaces=False
    )[0]

    # Xử lý chuỗi JSON model nhả ra
    try:
        # Lọc nếu model lỡ in thêm markdown ```json ... ```
        clean_json_str = output_text.replace("```json", "").replace("```", "").strip()
        data = json.loads(clean_json_str)
        return data
    except json.JSONDecodeError:
        print(f"Lỗi parse JSON. Output gốc: {output_text}")
        return {"post_date": None, "likes": 0, "comments": 0, "shares": 0}

# ================================
# CÁCH CHẠY THỬ
# ================================
if __name__ == "__main__":
    # Thay bằng file ảnh screenshot 1 bài viết Facebook thật của bạn
    test_image = r"c:\Users\ASUS\Downloads\Marketing_Pet&Grass\Downloaded_Images\test_post.jpg" 
    
    print(f"\nĐang phân tích bài đăng: {test_image}...")
    result = extract_post_stats(test_image)
    
    print("\nKết quả JSON trả về cho File Excel của bạn:")
    print(json.dumps(result, indent=4, ensure_ascii=False))
