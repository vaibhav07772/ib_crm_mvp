"""
Free LLM Drafter using Groq
"""

from groq import Groq
from typing import Dict
from config.settings import (
    GROQ_API_KEY,
    GROQ_MODEL,
    STUDENT_NAME,
    STUDENT_UNIVERSITY,
    STUDENT_MAJOR,
    STUDENT_GRADUATION_YEAR,
    STUDENT_LINKEDIN,
    STUDENT_EMAIL,
)


class LLMDrafter:
    def __init__(self):
        if not GROQ_API_KEY:
            raise ValueError("GROQ_API_KEY not set in .env")
        self.client = Groq(api_key=GROQ_API_KEY)
        self.model = GROQ_MODEL

    def draft_cold_email(self, contact: Dict) -> Dict[str, str]:
        first_name = contact.get("first_name") or "there"
        title = contact.get("title") or "Investment Banking professional"
        company = contact.get("company") or "your firm"

        system_prompt = f"""You are an expert cold email writer for finance networking.
Write short, professional, human-sounding emails (maximum 110 words).
Never sound salesy or desperate. Focus on genuine relationship building.
Always end with a soft CTA (quick chat / coffee chat / advice).

Student details:
- Name: {STUDENT_NAME}
- University: {STUDENT_UNIVERSITY}
- Major: {STUDENT_MAJOR}
- Graduation: {STUDENT_GRADUATION_YEAR}
- LinkedIn: {STUDENT_LINKEDIN}
"""

        user_prompt = f"""Write a cold networking email to:
- First name: {first_name}
- Title: {title}
- Company: {company}

Goal: Build a relationship so the student can request informational interviews and future opportunities in Investment Banking.

Return ONLY in this exact format:
Subject: <subject line>
Body:
<body text>
"""

        response = self.client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            temperature=0.7,
            max_tokens=400,
        )

        content = response.choices[0].message.content.strip()

        subject = "Networking Request"
        body = content

        if "Subject:" in content:
            parts = content.split("Body:", 1)
            subject_line = parts[0].replace("Subject:", "").strip()
            subject = subject_line.split("\n")[0].strip()
            if len(parts) > 1:
                body = parts[1].strip()

        return {"subject": subject, "body": body}

    def draft_followup(self, contact: Dict, followup_number: int = 1) -> Dict[str, str]:
        first_name = contact.get("first_name") or "there"
        company = contact.get("company") or "your firm"

        prompt = f"""Write a short polite follow-up email (max 80 words) to {first_name} at {company}.
This is follow-up number {followup_number}.
Student: {STUDENT_NAME}, {STUDENT_UNIVERSITY}, graduating {STUDENT_GRADUATION_YEAR}.
Keep it light and respectful. Ask if they had a chance to see the previous email.

Return ONLY:
Subject: <subject>
Body:
<body>
"""

        response = self.client.chat.completions.create(
            model=self.model,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.6,
            max_tokens=300,
        )

        content = response.choices[0].message.content.strip()
        subject = f"Following up – {STUDENT_NAME}"
        body = content

        if "Subject:" in content:
            parts = content.split("Body:", 1)
            subject = parts[0].replace("Subject:", "").strip().split("\n")[0]
            if len(parts) > 1:
                body = parts[1].strip()

        return {"subject": subject, "body": body}