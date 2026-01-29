# API/ChatbotAI.py
import os
from groq import Groq
from dotenv import load_dotenv

load_dotenv()
GROQ_API_KEY = os.getenv("GROQ_API_KEY")

groq_client = None
if GROQ_API_KEY:
    try: groq_client = Groq(api_key=GROQ_API_KEY)
    except: pass

def chatbotai(sys_prompt: str, user_prompt: str, model_id: str = "llama-3.3-70b-versatile") -> str:
    if not groq_client: return "Lỗi: Chưa cấu hình API Key trong file .env"
    
    # Yêu cầu AI gợi ý theo format JSON-like hoặc đặc biệt để dễ tách
    force_suggestion = """
    \n[NHIỆM VỤ CUỐI CÙNG BẮT BUỘC]:
    Cuối câu trả lời, hãy gợi ý 3 câu hỏi tiếp theo cho người dùng.
    Định dạng bắt buộc: ///Câu 1|Câu 2|Câu 3///
    Không thêm bất kỳ lời dẫn nào khác vào phần này.
    """
    
    try:
        completion = groq_client.chat.completions.create(
            model=model_id,
            messages=[
                {"role": "system", "content": sys_prompt + force_suggestion},
                {"role": "user", "content": user_prompt}
            ],
            temperature=0.7,
            max_tokens=1500
        )
        return completion.choices[0].message.content
    except Exception as e:
        return f"Lỗi kết nối AI: {str(e)}"