# API/InsightEngine.py
import os
from groq import Groq
from dotenv import load_dotenv

load_dotenv()
GROQ_API_KEY = os.getenv("GROQ_API_KEY")

_client = None
if GROQ_API_KEY:
    try: _client = Groq(api_key=GROQ_API_KEY)
    except: pass

def generate_insights(sys_prompt: str, user_prompt: str, model_id: str = "llama-3.3-70b-versatile") -> str:
    """Hàm xử lý phân tích dữ liệu tự động."""
    if not _client: return "Lỗi: Hệ thống chưa được cấu hình tham số môi trường."
    
    # Giao thức định dạng phản hồi tóm tắt
    formatting_hint = """
    \n[LƯU Ý]:
    Cuối câu trả lời, hãy gợi ý 3 câu hỏi liên quan tiếp theo cho người dùng.
    Định dạng bắt buộc: ///Câu 1|Câu 2|Câu 3///
    Không thêm bất kỳ lời dẫn nào khác vào phần này.
    """
    
    try:
        completion = _client.chat.completions.create(
            model=model_id,
            messages=[
                {"role": "system", "content": sys_prompt + formatting_hint},
                {"role": "user", "content": user_prompt}
            ],
            temperature=0.7,
            max_tokens=1500
        )
        return completion.choices[0].message.content
    except Exception as e:
        return f"Lỗi kết nối máy chủ phân tích: {str(e)}"