"""
Email Finder - Free tier friendly (Hunter + Manual)
"""

import requests
from typing import Optional, Dict
from tenacity import retry, stop_after_attempt, wait_exponential
from config.settings import HUNTER_API_KEY, APOLLO_API_KEY


class EmailFinder:
    def __init__(self):
        self.hunter_key = HUNTER_API_KEY
        self.apollo_key = APOLLO_API_KEY

    @retry(stop=stop_after_attempt(2), wait=wait_exponential(multiplier=1, min=2, max=6))
    def find_with_hunter(self, first_name: str, last_name: str, domain: str = None, company: str = None) -> Optional[Dict]:
        if not self.hunter_key:
            return None

        url = "https://api.hunter.io/v2/email-finder"
        params = {
            "api_key": self.hunter_key,
            "first_name": first_name,
            "last_name": last_name,
        }
        if domain:
            params["domain"] = domain
        if company:
            params["company"] = company

        try:
            resp = requests.get(url, params=params, timeout=20)
            resp.raise_for_status()
            data = resp.json().get("data", {})
            if data.get("email"):
                return {
                    "first_name": data.get("first_name") or first_name,
                    "last_name": data.get("last_name") or last_name,
                    "email": data.get("email"),
                    "title": data.get("position"),
                    "company": data.get("company") or company,
                    "linkedin_url": data.get("linkedin_url"),
                    "source": "hunter",
                    "score": data.get("score"),
                }
        except Exception as e:
            print(f"Hunter error: {e}")
        return None

    def find_email(self, first_name: str, last_name: str, domain: str = None, company: str = None) -> Optional[Dict]:
        # Free priority: Hunter
        result = self.find_with_hunter(first_name, last_name, domain, company)
        if result:
            return result
        return None