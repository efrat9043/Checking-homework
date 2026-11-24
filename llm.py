"""
יצירת המודל במקום אחד.
כל הצמתים מקבלים את המודל רק מכאן, כך שהחלפת ספק (Gemini <-> GPT)
דורשת רק שינוי של משתנה סביבה ב-.env, בלי לגעת בשאר הקוד.
"""
import os

import truststore
from dotenv import load_dotenv

# Python ישתמש במאגר התעודות של Windows (נדרש כשיש סינון אינטרנט / אנטי-וירוס
# שבודק תעבורה מוצפנת). חייב לרוץ לפני כל פנייה ל-OpenAI או ל-LangSmith.
truststore.inject_into_ssl()

# טעינת המפתחות וההגדרות מקובץ .env
load_dotenv()


def get_judge_llm():
    """המודל של השופט בהערכה (LLM-as-judge). נפרד מהמודל של הסוכן, לפי JUDGE_MODEL שב-.env."""
    return get_llm(model=os.getenv("JUDGE_MODEL", "gpt-6-luna"))


def get_llm(model: str | None = None):
    """מחזירה אובייקט מודל לפי LLM_PROVIDER, LLM_MODEL ו-LLM_TEMPERATURE שב-.env.
    אפשר להעביר model כדי לקבל מודל אחר (משמש את השופט)."""
    provider = os.getenv("LLM_PROVIDER", "openai").lower()
    model = model or os.getenv("LLM_MODEL")
    # gpt-6-luna תומך רק ב-temperature=1. במודל שתומך, ערך 0 נותן ציונים עקביים יותר.
    temperature = float(os.getenv("LLM_TEMPERATURE", "1"))

    # הייבוא בתוך התנאי: כך לא צריך להתקין ספריות של ספק שלא בשימוש
    if provider == "openai":
        # דורש OPENAI_API_KEY ב-.env
        from langchain_openai import ChatOpenAI
        return ChatOpenAI(model=model or "gpt-6.2-sol", temperature=temperature)

    if provider == "gemini":
        # דורש GOOGLE_API_KEY ב-.env
        from langchain_google_genai import ChatGoogleGenerativeAI
        return ChatGoogleGenerativeAI(model=model or "gemini-2.5-flash", temperature=temperature)

    raise ValueError(f"ספק מודל לא מוכר: {provider}")
