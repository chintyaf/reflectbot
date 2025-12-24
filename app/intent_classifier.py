import re
import random
from dataclasses import dataclass
from typing import List, Dict
from datetime import datetime


@dataclass
class Intent:
    """Intent definition with patterns and responses"""
    name: str
    patterns: List[str]
    responses: List[str]
    follow_ups: List[str]
    required_turns: int = 1


class IntentClassifier:
    """Multi-intent classifier dengan priority handling"""
    
    def __init__(self):
        self.intents = self._initialize_intents()
    
    def _initialize_intents(self) -> Dict[str, Intent]:
        """Define all conversation intents - DIPERBANYAK"""
        
        return {
            "greeting": Intent(
                name="greeting",
                patterns=[
                    r"\b(hai|halo|hi|hey|selamat|assalamualaikum)\b",
                    r"^(pagi|siang|sore|malam)",
                ],
                responses=[
                    "Hai! 👋 Saya ReflectBot, teman refleksi Anda.",
                    "Halo! Senang bertemu dengan Anda.",
                    "Selamat datang! Saya di sini untuk mendengarkan Anda.",
                ],
                follow_ups=[
                    "Bagaimana perasaan Anda hari ini?",
                    "Ada yang ingin Anda ceritakan?",
                    "Apa yang sedang ada di pikiran Anda sekarang?",
                ],
                required_turns=0
            ),
            
            "sharing_emotion": Intent(
                name="sharing_emotion",
                patterns=[
                    r"\b(merasa|rasa|perasaan)\s+\w+",
                    r"\b(sedih|senang|marah|cemas|takut|khawatir|bahagia|kecewa)\b",
                    r"\b(stress|depresi|down|galau)\b",
                ],
                responses=[
                    "Terima kasih sudah terbuka dengan saya. Perasaan Anda valid.",
                    "Saya dengar Anda. Tidak apa-apa merasakan ini.",
                    "Wajar untuk merasa seperti itu. Anda tidak sendirian.",
                ],
                follow_ups=[
                    "Bisa ceritakan lebih detail apa yang membuat Anda merasa seperti itu?",
                    "Kapan pertama kali Anda merasa seperti ini?",
                    "Apa yang biasanya membuat perasaan ini muncul?",
                ],
                required_turns=1
            ),
            
      
            
            "attachment_anxious": Intent(
                name="attachment_anxious",
                patterns=[
                    r"\b(takut|khawatir)\s+(ditinggal|dihiraukan|diabaikan)",
                    r"\b(insecure|tidak percaya diri)\b",
                    r"\bkenapa\s+(dia|kamu)\s+(tidak|nggak)\b",
                    r"\b(butuh|perlu)\s+perhatian\b",
                ],
                responses=[
                    "Kekhawatiran akan ditinggalkan adalah perasaan yang sangat manusiawi.",
                    "Saya mendengar kebutuhan Anda untuk merasa aman dalam hubungan.",
                ],
                follow_ups=[
                    "Apakah Anda sering merasa cemas saat pasangan tidak responsif?",
                    "Bagaimana Anda biasanya mengekspresikan kebutuhan emosional Anda?",
                ],
                required_turns=3
            ),
            
            "attachment_avoidant": Intent(
                name="attachment_avoidant",
                patterns=[
                    r"\b(butuh|perlu)\s+space\b",
                    r"\b(terlalu|over)\s+(clingy|lengket)",
                    r"\b(mandiri|independen)\b.*\b(tidak butuh|nggak perlu)",
                    r"\bsulit\s+terbuka\b",
                ],
                responses=[
                    "Kemandirian adalah hal yang baik, tapi koneksi juga penting.",
                    "Menjaga jarak emosional kadang terasa lebih aman.",
                ],
                follow_ups=[
                    "Apakah Anda merasa tidak nyaman saat seseorang terlalu dekat secara emosional?",
                    "Bagaimana Anda biasanya merespons saat seseorang menunjukkan kebutuhan emosional?",
                ],
                required_turns=3
            ),
            
            "self_reflection": Intent(
                name="self_reflection",
                patterns=[
                    r"\bkenapa\s+saya\s+(selalu|sering)\b",
                    r"\b(pola|pattern)\s+yang sama\b",
                    r"\b(salah|masalah)\s+saya\b",
                ],
                responses=[
                    "Kesadaran diri adalah langkah pertama menuju perubahan.",
                    "Anda mulai melihat pola - itu sangat penting.",
                ],
                follow_ups=[
                    "Apakah Anda melihat pola ini berulang di berbagai hubungan?",
                    "Menurut Anda, apa yang membuat pola ini terus terjadi?",
                ],
                required_turns=4
            ),
            
            "closure": Intent(
                name="closure",
                patterns=[
                    r"\b(terima kasih|thanks|makasih)\b",
                    r"\b(cukup|sudah|oke)\b.*\b(bantu|jelas)",
                    r"\b(bye|selesai|cukup)\b",
                ],
                responses=[
                    "Terima kasih sudah berbagi dengan saya hari ini. 🙏",
                    "Saya senang bisa menemani refleksi Anda.",
                ],
                follow_ups=[
                    "Jika Anda ingin menganalisis percakapan kita, tekan tombol 'Analisis Percakapan'.",
                    "Sampai jumpa! Saya selalu di sini jika Anda butuh berbicara lagi.",
                ],
                required_turns=6
            ),
            
            "general": Intent(
                name="general",
                patterns=[],
                responses=[
                    "Menarik. Bisa ceritakan lebih banyak?",
                    "Saya mendengarkan. Silakan lanjutkan.",
                    "Apa yang Anda rasakan tentang itu?",
                ],
                follow_ups=[
                    "Bagaimana perasaan Anda saat itu?",
                    "Apa yang membuat situasi ini penting bagi Anda?",
                ],
                required_turns=1
            ),
        }
    
    def classify(self, text: str, turn_count: int) -> str:
        """Classify intent with priority"""
        text_lower = text.lower()
        
        # Priority urutan
        priority = [
            "greeting",
            "closure",
            "attachment_anxious",
            "attachment_avoidant",
            "self_reflection",
            "sharing_emotion",
            "general"
        ]
        
        for intent_name in priority:
            intent = self.intents[intent_name]
            
            # Check required turns
            if turn_count < intent.required_turns:
                continue
            
            # Match patterns
            for pattern in intent.patterns:
                if re.search(pattern, text_lower):
                    return intent_name
        
        return "general"


class ConversationEngine:
    """Main conversation management"""
    
    def __init__(self):
        self.intent_classifier = IntentClassifier()
        self.conversation_history = []
        self.turn_count = 0
        self.user_name = None
    
    def start_conversation(self) -> str:
        """Start the conversation"""
        greeting = random.choice(
            self.intent_classifier.intents["greeting"].responses
        )
        follow_up = random.choice(
            self.intent_classifier.intents["greeting"].follow_ups
        )
        return f"{greeting}\n\n{follow_up}"
    
    def respond(self, user_message: str) -> str:
        """Generate contextual response"""
        self.turn_count += 1
        
        # Classify intent
        intent_name = self.intent_classifier.classify(
            user_message, 
            self.turn_count
        )
        intent = self.intent_classifier.intents[intent_name]
        
        # Save to history
        self.conversation_history.append({
            "turn": self.turn_count,
            "user_message": user_message,
            "intent": intent_name,
            "timestamp": datetime.now()
        })
        
        # Generate response
        response = random.choice(intent.responses)
        
        # Add follow-up jika belum turn 10
        if self.turn_count <= 10 and intent.follow_ups:
            follow_up = random.choice(intent.follow_ups)
            response = f"{response}\n\n{follow_up}"
        
        # Save bot response
        self.conversation_history[-1]["bot_response"] = response
        
        return response