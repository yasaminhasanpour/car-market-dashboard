from dotenv import load_dotenv
import os
from openai import OpenAI

load_dotenv()
client = OpenAI(
    api_key=os.environ.get("OPENAI_API_KEY"),
    base_url="https://api.gapgpt.app/v1"
)


def get_ai_insight(data_summary: str, question: str) -> str:
    """
    data_summary: خلاصه‌ای متنی از داده‌ها (مثلاً از یه دیتافریم)
    question: سوالی که می‌خوای از هوش مصنوعی بپرسی
    """
    prompt = f"""
داده‌های زیر مربوط به قیمت خودرو در ایران هست:

{data_summary}

{question}
"""

    response = client.chat.completions.create(
        model="gpt-4o-mini",  # مدل ارزون‌تر و سریع‌تر، برای شروع کافیه
        messages=[
            {"role": "system", "content": "تو یک تحلیلگر بازار خودرو هستی و به فارسی روون و ساده جواب میدی."},
            {"role": "user", "content": prompt}
        ],
        temperature=0.3
    )

    return response.choices[0].message.content