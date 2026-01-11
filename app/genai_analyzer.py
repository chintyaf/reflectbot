import os
from typing import List, Dict
import google.generativeai as genai
from dotenv import load_dotenv

load_dotenv()

class GeminiAnalyzer:
    def __init__(self, api_key: str = None, model: str = "gemini-1.0-pro"):
        self.api_key = api_key or os.getenv("GEMINI_API_KEY")
        if not self.api_key:
            print("Warning: GEMINI_API_KEY tidak ditemukan. Menggunakan mock analysis.")
            self.api_key = None
            return

        try:
            genai.configure(api_key=self.api_key)
            self.model = genai.GenerativeModel(model)
            self.model_name = model
        except Exception as e:
            print(f"Warning: Could not initialize Gemini: {e}. Using mock analysis.")
            self.api_key = None

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
            if self.api_key is None:
                return self._mock_summary(conversation_text, key_phrases, rule_scores)
                
            response = self.model.generate_content(prompt)
            return response.text.strip()
        except Exception as e:
            return self._mock_summary(conversation_text, key_phrases, rule_scores)
        
    def _mock_summary(self, conversation_text, key_phrases, rule_scores):
        """Generate mock summary when AI is not available"""
        secure_pct = int(rule_scores.get('secure', 0) * 100)
        anxious_pct = int(rule_scores.get('anxious', 0) * 100) 
        avoidant_pct = int(rule_scores.get('avoidant', 0) * 100)
        
        return f"""## 1. Ringkasan Emosional
Dari percakapan ini, terlihat adanya perasaan kesepian dan kebutuhan akan dukungan emosional dari pasangan.

## 2. Pola Kelekatan
Berdasarkan analisis, pola kelekatan yang terdeteksi menunjukkan kecenderungan { 'aman' if secure_pct > anxious_pct and secure_pct > avoidant_pct else 'cemas' if anxious_pct > avoidant_pct else 'menghindar' } dalam hubungan.

## 3. Dinamika Hubungan
Pola ini dapat mempengaruhi bagaimana individu mengekspresikan kebutuhan emosional dan merespons dukungan dari pasangan.

## 4. Rekomendasi
- Komunikasikan kebutuhan secara terbuka dengan pasangan
- Cari dukungan dari teman atau keluarga
- Pertimbangkan konseling jika diperlukan

*Catatan: Ini adalah analisis otomatis berdasarkan pola teks. Untuk analisis yang lebih mendalam, konsultasikan dengan profesional.*"""
        
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
            response = self.model.generate_content(prompt)
            return response.text.strip()
        except Exception as e:
            return f"Maaf, penjelasan tidak tersedia. Error: {e}"