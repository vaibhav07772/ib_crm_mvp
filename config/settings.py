import os
from pathlib import Path
from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(BASE_DIR / ".env")

# APIs
GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")
HUNTER_API_KEY = os.getenv("HUNTER_API_KEY", "")
APOLLO_API_KEY = os.getenv("APOLLO_API_KEY", "")

# SMTP
SMTP_EMAIL = os.getenv("SMTP_EMAIL", "")
SMTP_APP_PASSWORD = os.getenv("SMTP_APP_PASSWORD", "")
SMTP_HOST = os.getenv("SMTP_HOST", "smtp.gmail.com")
SMTP_PORT = int(os.getenv("SMTP_PORT", 587))

# Student
STUDENT_NAME = os.getenv("STUDENT_NAME", "Student")
STUDENT_UNIVERSITY = os.getenv("STUDENT_UNIVERSITY", "University")
STUDENT_MAJOR = os.getenv("STUDENT_MAJOR", "Finance")
STUDENT_GRADUATION_YEAR = os.getenv("STUDENT_GRADUATION_YEAR", "2027")
STUDENT_LINKEDIN = os.getenv("STUDENT_LINKEDIN", "")
STUDENT_EMAIL = os.getenv("STUDENT_EMAIL", "")

# Settings
DAILY_EMAIL_LIMIT = int(os.getenv("DAILY_EMAIL_LIMIT", 15))
GROQ_MODEL = os.getenv("GROQ_MODEL", "llama-3.1-8b-instant")

# Paths
DATA_DIR = BASE_DIR / "data"
DB_PATH = DATA_DIR / "crm.db"
DATA_DIR.mkdir(exist_ok=True)