# API/InsightEngine.py
import os
from groq import Groq
from dotenv import load_dotenv

load_dotenv(override=True)
GROQ_API_KEY = os.getenv("GROQ_API_KEY")

client = None
if GROQ_API_KEY:
    masked_key = f"...{GROQ_API_KEY[-4:]}" if GROQ_API_KEY else "NONE"
    print(f"[SYSTEM] Using GROQ API Key ending with: {masked_key}")
    try:
        client = Groq(api_key=GROQ_API_KEY)
    except Exception as e:
        print(f"[ERROR] Cannot init Groq Client: {e}")

# Danh sách các model hoạt động tốt trên Groq hiện tại
FALLBACK_MODELS = [
    "qwen/qwen3.8-27b",
    "openai/gpt-oss-120b",
    "openai/gpt-oss-20b"
]

def generate_insights(sys_prompt: str, user_prompt: str, model_id: str = None) -> str:
    """Hàm xử lý phân tích dữ liệu sử dụng Groq Engine."""
    if not client: 
        return "Lỗi: Hệ thống chưa được cấu hình tham số môi trường GROQ_API_KEY."
    
    formatting_hint = """
    \n[LƯU Ý QUAN TRỌNG]:
    1. KHÔNG sử dụng các thuật ngữ nhạy cảm như "AI", "Robot", "Model", "Trí tuệ nhân tạo".
    2. Hãy đóng vai là một Chuyên gia phân tích dữ liệu chuyên nghiệp.
    3. Cuối câu trả lời, hãy gợi ý chính xác 3 câu hỏi liên quan tiếp theo cho người dùng.
    Định dạng bắt buộc: ///Câu 1|Câu 2|Câu 3///
    Không thêm bất kỳ lời dẫn nào khác vào phần này.
    """
    
    models_to_try = [model_id] if model_id else []
    models_to_try.extend([m for m in FALLBACK_MODELS if m != model_id])

    last_error = ""
    for model in models_to_try:
        try:
            completion = client.chat.completions.create(
                model=model,
                messages=[
                    {"role": "system", "content": sys_prompt + formatting_hint},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=0.7,
                max_tokens=4096
            )
            return completion.choices[0].message.content
        except Exception as e:
            last_error = str(e)
            continue
            
    return f"Lỗi kết nối máy chủ phân tích (Groq): {last_error}"

def chat_groq_ideas(messages: list, system_prompt: str = "") -> str:
    """
    Hàm xử lý Chatbot AI gợi ý ý tưởng NCKH đọc dữ liệu từ DB.
    """
    if not client:
        return "⚠️ Hệ thống chưa được cấu hình GROQ_API_KEY trong file .env. Vui lòng liên hệ quản trị viên."

    payload = []
    if system_prompt:
        payload.append({"role": "system", "content": system_prompt})
    
    for m in messages:
        payload.append({
            "role": m.get("role", "user"),
            "content": m.get("content", "")
        })

    last_err = ""
    for model in FALLBACK_MODELS:
        try:
            completion = client.chat.completions.create(
                model=model,
                messages=payload,
                temperature=0.75,
                max_tokens=2048
            )
            content = completion.choices[0].message.content
            if content and content.strip():
                return content.strip()
        except Exception as e:
            last_err = str(e)
            continue

    return f"⚠️ Rất tiếc, AI tạm thời không phản hồi được. Lỗi kết nối Groq: {last_err}"
