import os
from typing import List, Dict
from google import genai
from dotenv import load_dotenv

load_dotenv()

class GeminiAnalyzer:

    def __init__(self, api_key: str = None, model: str = "gemini-2.5-flash"):
        self.api_key = api_key or os.getenv("GEMINI_API_KEY")
        self.client = genai.Client(api_key=self.api_key)
        self.model = model

    def summarize_conversation(
        self,
        conversation_text: str,
        key_phrases: List[str],
        rule_scores: Dict[str, float],
    ) -> str:

        prompt = f"""
            Kamu adalah psikolog attachment theory expert yang empatis dan profesional.

            PERCAKAPAN:
            {conversation_text}

            FRASA KUNCI:
            {', '.join(key_phrases[:20])}

            SKOR:
            - Secure: {rule_scores.get('secure', 0):.2%}
            - Anxious: {rule_scores.get('anxious', 0):.2%}
            - Avoidant: {rule_scores.get('avoidant', 0):.2%}

            Berikan analisis dalam 4 bagian:
            1. Ringkasan Emosional
            2. Pola Kelekatan
            3. Dinamika Hubungan
            4. Insight & Rekomendasi
            """

        try:
            response = self.client.models.generate_content(
                model=self.model,
                contents=prompt,
            )
            return response.text
        except Exception as e:
            return f"[Gemini ERROR] {e}"
        
    def summarize_conversation(
        self,
        conversation_text: str,
        key_phrases: List[str],
        rule_scores: Dict[str, float],
    ) -> str:

        prompt = f"""
            Kamu adalah psikolog attachment theory expert yang empatis dan profesional.

            PERCAKAPAN:
            {conversation_text}

            FRASA KUNCI:
            {', '.join(key_phrases[:20])}

            SKOR:
            - Secure: {rule_scores.get('secure', 0):.2%}
            - Anxious: {rule_scores.get('anxious', 0):.2%}
            - Avoidant: {rule_scores.get('avoidant', 0):.2%}

            Berikan analisis dalam 4 bagian:
            1. Ringkasan Emosional
            2. Pola Kelekatan
            3. Dinamika Hubungan
            4. Insight & Rekomendasi
            """

        try:
            response = self.client.models.generate_content(
                model=self.model,
                contents=prompt,
            )
            return response.text
        except Exception as e:
            return f"[Gemini ERROR] {e}"
        
    def explain_phrase(
        self,
        phrase: str,
        context: str,
        attachment_style: str,
    ) -> str:

        prompt = f"""
            Sebagai psikolog attachment theory, jelaskan frasa berikut:

            FRASA: "{phrase}"

            KONTEKS:
            {context[:500]}...

            ATTACHMENT STYLE: {attachment_style}

            Jelaskan:
            1. Makna kelekatan
            2. Hubungan dengan attachment style
            3. Latar belakang psikologis
            """

        try:
            response = self.client.models.generate_content(
                model=self.model,
                contents=prompt,
            )
            return response.text
        except Exception as e:
            return f"[Gemini ERROR] {e}"
