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
        try:
            self.model = joblib.load(f"{model_path}model_best.pkl")
        except Exception as e:
            print(f"Warning: Could not load model: {e}. Using mock predictions.")
            self.model = None
        
        try:
            self.scaler_bert = joblib.load(f"{model_path}scaler_bert.pkl")
        except:
            self.scaler_bert = None
        
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
        try:
            with open(f"{model_path}feature_config.json", "r") as f:
                self.feature_config = json.load(f)
        except:
            self.feature_config = {"emotion_cols": [], "text_stat_cols": []}
        
        # Load IndoBERT
        try:
            model_name = "indobenchmark/indobert-base-p1"
            self.tokenizer = AutoTokenizer.from_pretrained(model_name)
            self.bert_model = AutoModel.from_pretrained(model_name).to(self.device)
            self.bert_model.eval()
        except Exception as e:
            print(f"Warning: Could not load IndoBERT: {e}")
            self.tokenizer = None
            self.bert_model = None
        
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
    
    def _rule_based_prediction(self, text):
        """Simple rule-based prediction for attachment styles"""
        text_lower = text.lower()
        
        # Anxious indicators
        anxious_keywords = ['takut', 'khawatir', 'cemburu', 'butuh', 'dukung', 'pastikan', 'yakin', 'tenang']
        anxious_score = sum(1 for word in anxious_keywords if word in text_lower)
        
        # Avoidant indicators  
        avoidant_keywords = ['sendiri', 'mandiri', 'bebas', 'ruang', 'waktu', 'pribadi', 'jaga jarak']
        avoidant_score = sum(1 for word in avoidant_keywords if word in text_lower)
        
        # Secure indicators
        secure_keywords = ['percaya', 'dukung', 'saling', 'komunikasi', 'terbuka', 'jujur', 'harmonis']
        secure_score = sum(1 for word in secure_keywords if word in text_lower)
        
        # Determine prediction based on highest score
        scores = {
            'anxious': anxious_score,
            'avoidant': avoidant_score, 
            'secure': secure_score
        }
        
        max_style = max(scores, key=scores.get)
        
        return max_style
    
    def encode_text_bert(self, text):
        """Get BERT embeddings"""
        if self.tokenizer is None or self.bert_model is None:
            # Return mock embedding
            return np.random.randn(768).astype(np.float32)
            
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
        
        # Mock data jika model tidak tersedia
        if self.model is None or self.tokenizer is None or self.bert_model is None:
            phrases = self.extract_phrases(clean_text)
            
            # Simple rule-based prediction
            prediction = self._rule_based_prediction(clean_text)
            
            return {
                # Main prediction
                "prediction": prediction,
                "confidence": 0.7,  # Mock confidence
                "probabilities": {"secure": 0.4, "anxious": 0.3, "avoidant": 0.3},  # Mock probabilities
                
                # Phrase analysis
                "key_phrases": phrases[:20],
                "phrase_scores": {phrase: 0.5 for phrase in phrases[:5]},  
                
                # Emotion analysis (jika ada)
                "emotion_scores": {},  
                
                # BERT features summary
                "bert_summary": {
                    "embedding_dim": 768,
                    "embedding_mean": 0.0,
                    "embedding_std": 1.0,
                    "embedding_max": 1.0,
                    "embedding_min": -1.0
                }, 
                
                # Text stats
                "text_stats": {
                    "word_count": int(word_count),
                    "sentence_count": int(sentence_count),
                    "clean_text_length": int(len(clean_text))
                },
                
                # Rule scores (placeholder for now)
                "rule_scores": {
                    "secure": 0.5,  # Placeholder
                    "anxious": 0.3,  # Placeholder  
                    "avoidant": 0.2   # Placeholder
                },
                
                # Original text
                "clean_text": clean_text,
                "original_text": conversation_text
            }
        
        # 1. BERT embedding
        bert_emb = self.encode_text_bert(clean_text)
        bert_emb_scaled = self.scaler_bert.transform([bert_emb])[0]
        feature_list = [bert_emb_scaled]
        
        # BERT summary untuk output
        bert_summary = {
            "embedding_dim": int(len(bert_emb)),
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
        prediction = str(self.model.predict(X)[0])
        probabilities = self.model.predict_proba(X)[0]
        proba_dict = dict(zip(self.model.classes_, probabilities))
        
        # Convert classes to strings if needed
        classes = [str(cls) for cls in self.model.classes_]
        proba_dict = dict(zip(classes, probabilities))
        
        print(f"DEBUG: Raw prediction: {prediction}, Probabilities: {proba_dict}")
        
        # Map prediction and probabilities to labels
        label_mapping = {'0': 'secure', '1': 'anxious', '2': 'avoidant'}
        prediction = label_mapping.get(prediction, prediction)
        
        # Convert probabilities keys to labels
        proba_dict_labeled = {}
        for key, value in proba_dict.items():
            label = label_mapping.get(key, key)
            proba_dict_labeled[label] = float(value)
        
        # ENHANCED RETURN dengan semua detail model
        return {
            # Main prediction
            "prediction": prediction,
            "confidence": float(max(probabilities)),
            "probabilities": proba_dict_labeled,
            
            # Phrase analysis
            "key_phrases": phrases[:20],
            "phrase_scores": {k: float(v) for k, v in phrase_scores.items()},  
            
            # Emotion analysis (jika ada)
            "emotion_scores": {k: float(v) for k, v in emotion_scores.items()},  
            
            # BERT features summary
            "bert_summary": bert_summary, 
            
            # Text stats
            "text_stats": {
                "word_count": int(word_count),
                "sentence_count": int(sentence_count),
                "clean_text_length": int(len(clean_text))
            },
            
            # Rule scores (placeholder for now)
            "rule_scores": {
                "secure": 0.5,  # Placeholder
                "anxious": 0.3,  # Placeholder  
                "avoidant": 0.2   # Placeholder
            },
            
            # Original text
            "clean_text": clean_text,
            "original_text": conversation_text
        }