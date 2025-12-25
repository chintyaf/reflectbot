import torch
import joblib
import json
import numpy as np
from transformers import AutoTokenizer, AutoModel
from Sastrawi.StopWordRemover.StopWordRemoverFactory import StopWordRemoverFactory
from Sastrawi.Stemmer.StemmerFactory import StemmerFactory
import re

class ChatbotService:
    
    def __init__(self, model_path="app/model/"):
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        
        # Load model & scalers
        self.model = joblib.load(f"{model_path}model_best.pkl")
        self.scaler_bert = joblib.load(f"{model_path}scaler_bert.pkl")
        
        try:
            self.scaler_emotion = joblib.load(f"{model_path}scaler_emotion.pkl")
        except:
            self.scaler_emotion = None
        
        try:
            self.scaler_text = joblib.load(f"{model_path}scaler_text.pkl")
        except:
            self.scaler_text = None
        
        try:
            self.phrase_tfidf = joblib.load(f"{model_path}phrase_tfidf.pkl")
        except:
            self.phrase_tfidf = None
        
        # Load feature config
        with open(f"{model_path}feature_config.json", "r") as f:
            self.feature_config = json.load(f)
        
        # Load IndoBERT
        model_name = "indobenchmark/indobert-base-p1"
        self.tokenizer = AutoTokenizer.from_pretrained(model_name)
        self.bert_model = AutoModel.from_pretrained(model_name).to(self.device)
        self.bert_model.eval()
        
        # Initialize preprocessing
        self._init_preprocessing()
        
    
    def _init_preprocessing(self):
        """Initialize text preprocessing tools"""
        stopword_factory = StopWordRemoverFactory()
        self.stopword_remover = stopword_factory.create_stop_word_remover()
        
        stemmer_factory = StemmerFactory()
        self.stemmer = stemmer_factory.create_stemmer()
        
        self.slang_dict = {
            'ga': 'tidak', 'gak': 'tidak', 'nggak': 'tidak', 'ngga': 'tidak',
            'udah': 'sudah', 'dah': 'sudah', 'udh': 'sudah',
            'bgt': 'banget', 'bener': 'benar',
            'yg': 'yang', 'org': 'orang', 'krn': 'karena',
            'gue': 'saya', 'gw': 'saya', 'aku': 'saya',
            'lo': 'kamu', 'lu': 'kamu',
            'kalo': 'kalau', 'gimana': 'bagaimana',
            'emang': 'memang', 'trus': 'terus',
        }
        
    def preprocess_text(self, text):
        """Preprocess text"""
        text = text.lower()
        text = re.sub(r'\d+', '', text)
        text = re.sub(r'[^a-zA-Z\s]', '', text)
        text = re.sub(r'\s+', ' ', text).strip()
        
        words = text.split()
        words = [self.slang_dict.get(w, w) for w in words]
        text = ' '.join(words)
        
        text = self.stopword_remover.remove(text)
        text = self.stemmer.stem(text)
        return text
    
    def extract_phrases(self, text, n=2):
        """Extract bigrams and trigrams"""
        words = text.split()
        phrases = []
        
        # Bigrams
        for i in range(len(words) - 1):
            phrase = f"{words[i]} {words[i+1]}"
            if len(phrase) >= 10:
                phrases.append(phrase)
        
        # Trigrams
        for i in range(len(words) - 2):
            phrase = f"{words[i]} {words[i+1]} {words[i+2]}"
            if len(phrase) >= 15:
                phrases.append(phrase)
        
        return list(set(phrases))
    
    def encode_text_bert(self, text):
        """Get BERT embeddings"""
        inputs = self.tokenizer(
            text, 
            return_tensors="pt", 
            padding=True,
            truncation=True, 
            max_length=512
        ).to(self.device)
        
        with torch.no_grad():
            outputs = self.bert_model(**inputs)
            embedding = outputs.last_hidden_state[:, 0, :].cpu().numpy()[0]
        
        return embedding
    
    def predict(self, conversation_text):
        """
        Predict attachment style dengan DETAILED OUTPUT
        Returns semua info model: BERT, emotion, phrase scores, dll
        """
        # Preprocess
        clean_text = self.preprocess_text(conversation_text)
        
        # Text statistics
        word_count = len(clean_text.split())
        sentence_count = conversation_text.count('.') + conversation_text.count('!') + conversation_text.count('?')
        
        # 1. BERT embedding
        bert_emb = self.encode_text_bert(clean_text)
        bert_emb_scaled = self.scaler_bert.transform([bert_emb])[0]
        feature_list = [bert_emb_scaled]
        
        # BERT summary untuk output
        bert_summary = {
            "embedding_dim": len(bert_emb),
            "embedding_mean": float(np.mean(bert_emb)),
            "embedding_std": float(np.std(bert_emb)),
            "embedding_max": float(np.max(bert_emb)),
            "embedding_min": float(np.min(bert_emb))
        }
        
        # 2. Phrase features WITH SCORES
        phrases = self.extract_phrases(clean_text)
        phrase_scores = {}
        
        if self.phrase_tfidf and phrases:
            phrase_text = ' '.join(phrases)
            phrase_features = self.phrase_tfidf.transform([phrase_text]).toarray()[0]
            feature_list.append(phrase_features)
            
            # Get TF-IDF scores untuk setiap phrase
            feature_names = self.phrase_tfidf.get_feature_names_out()
            for phrase in phrases:
                phrase_words = phrase.split()
                # Cari skor dari vocab
                matching_scores = []
                for word in phrase_words:
                    if word in feature_names:
                        idx = list(feature_names).index(word)
                        matching_scores.append(phrase_features[idx])
                
                if matching_scores:
                    phrase_scores[phrase] = float(np.mean(matching_scores))
        
        # 3. Emotion features (jika ada model emotion)
        emotion_scores = {}
        if self.feature_config.get('emotion_cols'):
            # Ini placeholder - kalau ada model emotion beneran, extract di sini
            emotion_zeros = np.zeros(len(self.feature_config['emotion_cols']))
            if self.scaler_emotion:
                emotion_zeros = self.scaler_emotion.transform([emotion_zeros])[0]
            feature_list.append(emotion_zeros)
            
            # Output emotion scores (untuk ditampilkan)
            for i, emotion_col in enumerate(self.feature_config['emotion_cols']):
                emotion_scores[emotion_col] = float(emotion_zeros[i])
        
        # 4. Text stats
        if self.feature_config.get('text_stat_cols'):
            text_stats = [word_count, sentence_count]
            if self.scaler_text:
                text_stats = self.scaler_text.transform([text_stats])[0]
            feature_list.append(text_stats)
        
        # Combine features
        X = np.concatenate(feature_list).reshape(1, -1)
        
        # Predict
        prediction = self.model.predict(X)[0]
        probabilities = self.model.predict_proba(X)[0]
        proba_dict = dict(zip(self.model.classes_, probabilities))
        
        # ENHANCED RETURN dengan semua detail model
        return {
            # Main prediction
            "prediction": prediction,
            "confidence": float(max(probabilities)),
            "probabilities": {k: float(v) for k, v in proba_dict.items()},
            
            # Phrase analysis
            "key_phrases": phrases[:20],
            "phrase_scores": phrase_scores,  
            
            # Emotion analysis (jika ada)
            "emotion_scores": emotion_scores,  
            
            # BERT features summary
            "bert_summary": bert_summary, 
            
            # Text stats
            "text_stats": {
                "word_count": word_count,
                "sentence_count": sentence_count,
                "clean_text_length": len(clean_text)
            },
            
            # Original text
            "clean_text": clean_text,
            "original_text": conversation_text
        }