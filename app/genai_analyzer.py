import os
from typing import List, Dict
from google import genai
from dotenv import load_dotenv

load_dotenv()

class GeminiAnalyzer:
    def __init__(self, api_key: str = None, model: str = "gemini-2.0-flash-exp"):
        self.api_key = api_key or os.getenv("GEMINI_API_KEY")
        if not self.api_key:
            raise ValueError("GEMINI_API_KEY tidak ditemukan")

        self.client = genai.Client(api_key=self.api_key)
        self.model = model

    def summarize_conversation(
        self,
        conversation_text: str,
        key_phrases: List[str],
        rule_scores: Dict[str, float],
    ) -> str:
        """
        Generate empathetic and insightful summary for chat display
        Format optimized for chat bubble rendering
        """

        prompt = f"""Kamu adalah psikolog attachment theory yang empatis dan profesional.

            PERCAKAPAN USER:
            {conversation_text}

            FRASA KUNCI TERDETEKSI:
            {', '.join(key_phrases[:15])}

            SKOR ATTACHMENT STYLE:
            - Secure: {rule_scores.get('secure', 0):.0%}
            - Anxious: {rule_scores.get('anxious', 0):.0%}
            - Avoidant: {rule_scores.get('avoidant', 0):.0%}

            TUGAS:
            Berikan analisis yang mendalam namun mudah dipahami dalam format berikut. Gunakan bahasa Indonesia yang natural dan empatik.

            Format:

            ## 1. Ringkasan Emosional
            [2-3 kalimat tentang perasaan dan emosi yang terlihat dalam percakapan]

            ## 2. Pola Kelekatan
            [Jelaskan pola attachment yang terdeteksi dengan contoh spesifik dari percakapan]

            ## 3. Dinamika Hubungan
            [Analisis bagaimana pola ini mempengaruhi hubungan mereka]

            ## 4. Rekomendasi
            [2-3 saran praktis dan konkret untuk perbaikan]

            PENTING:
            - Gunakan markdown sederhana (**, ##, -)
            - Maksimal 400 kata
            - Hindari jargon psikologi yang rumit
            - Fokus pada insight yang actionable
            - Tone: empatis, supportive, non-judgmental"""

        try:
            response = self.client.models.generate_content(
                model=self.model,
                contents=prompt,
            )
            return response.text.strip()
        except Exception as e:
            return f"Maaf, analisis AI tidak tersedia. Error: {e}"
        
    def explain_phrase(
        self,
        phrase: str,
        context: str,
        attachment_style: str,
    ) -> str:
        """
        Explain a specific phrase in the context of attachment theory
        """

        prompt = f"""Sebagai psikolog attachment theory, jelaskan frasa berikut secara mendalam namun mudah dipahami.

                FRASA: "{phrase}"

                KONTEKS PERCAKAPAN:
                {context[:500]}...

                ATTACHMENT STYLE TERDETEKSI: {attachment_style}

                TUGAS:
                Jelaskan dalam 3 paragraf pendek:

                1. **Makna Psikologis**: Apa yang frasa ini ungkapkan tentang kebutuhan emosional dan pola pikir orang ini?

                2. **Hubungan dengan {attachment_style.title()} Attachment**: Bagaimana frasa ini mencerminkan karakteristik attachment style mereka?

                3. **Insight untuk Perbaikan**: Apa yang bisa dipelajari atau diperbaiki dari pola ini?

                Format: Gunakan markdown sederhana, maksimal 250 kata, tone empatis."""

        try:
            response = self.client.models.generate_content(
                model=self.model,
                contents=prompt,
            )
            return response.text.strip()
        except Exception as e:
            return f"Maaf, penjelasan tidak tersedia. Error: {e}"