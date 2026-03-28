# API/InsightEngine.py
import os
from groq import Groq
from dotenv import load_dotenv

# Ép buộc nạp biến môi trường từ tệp .env (ghi đè biến hệ thống)
load_dotenv(override=True)
GROQ_API_KEY = os.getenv("GROQ_API_KEY")

# Khởi tạo client Groq
client = None
if GROQ_API_KEY:
    # In log fingerprint để người dùng tự kiểm tra (4 ký tự cuối)
    masked_key = f"...{GROQ_API_KEY[-4:]}" if GROQ_API_KEY else "NONE"
    print(f"[HỆ THỐNG] Đang sử dụng GROQ API Key kết thúc bằng: {masked_key}")
    try:
        client = Groq(api_key=GROQ_API_KEY)
    except Exception as e:
        print(f"[LỖI] Không thể khởi tạo Groq Client: {e}")

def generate_insights(sys_prompt: str, user_prompt: str, model_id: str = "llama-3.3-70b-versatile") -> str:
    """Hàm xử lý phân tích dữ liệu sử dụng Groq Engine (Llama 3.3)."""
    if not client: 
        return "Lỗi: Hệ thống chưa được cấu hình tham số môi trường GROQ_API_KEY."
    
    # Giao thức định dạng phản hồi tóm tắt
    formatting_hint = """
    \n[LƯU Ý QUAN TRỌNG]:
    1. KHÔNG sử dụng các thuật ngữ nhạy cảm như "AI", "Robot", "Model", "Trí tuệ nhân tạo".
    2. Hãy đóng vai là một Chuyên gia phân tích dữ liệu chuyên nghiệp.
    3. Cuối câu trả lời, hãy gợi ý chính xác 3 câu hỏi liên quan tiếp theo cho người dùng.
    Định dạng bắt buộc: ///Câu 1|Câu 2|Câu 3///
    Không thêm bất kỳ lời dẫn nào khác vào phần này.
    """
    
    try:
        completion = client.chat.completions.create(
            model=model_id,
            messages=[
                {"role": "system", "content": sys_prompt + formatting_hint},
                {"role": "user", "content": user_prompt}
            ],
            temperature=0.7,
            max_tokens=4096
        )
        return completion.choices[0].message.content
        
    except Exception as e:
        err_str = str(e).lower()
        if "api_key" in err_str or "unauthorized" in err_str or "401" in err_str:
            return "Lỗi: API Key Groq không hợp lệ hoặc đã hết hạn. Vui lòng kiểm tra lại tệp .env."
        return f"Lỗi kết nối máy chủ phân tích (Groq): {str(e)}"