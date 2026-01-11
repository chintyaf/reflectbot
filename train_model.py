import pandas as pd
import numpy as np
import torch
import joblib
import json
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
from sklearn.ensemble import GradientBoostingClassifier
from sklearn.metrics import classification_report, accuracy_score
from imblearn.over_sampling import SMOTE
from transformers import AutoTokenizer, AutoModel
from Sastrawi.StopWordRemover.StopWordRemoverFactory import StopWordRemoverFactory
from Sastrawi.Stemmer.StemmerFactory import StemmerFactory
from sklearn.feature_extraction.text import TfidfVectorizer
import re

class ModelTrainer:
    def __init__(self):
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        self.model_name = "indobenchmark/indobert-base-p1"
        self.tokenizer = AutoTokenizer.from_pretrained(self.model_name)
        self.bert_model = AutoModel.from_pretrained(self.model_name).to(self.device)
        self.bert_model.eval()

        # Initialize preprocessing
        self._init_preprocessing()

    def _init_preprocessing(self):
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

    def prepare_features(self, df):
        print("Preparing features...")

        # Preprocess texts
        df['clean_text'] = df['text'].apply(self.preprocess_text)

        # Extract phrases and create TF-IDF
        all_phrases = []
        for text in df['clean_text']:
            phrases = self.extract_phrases(text)
            all_phrases.append(' '.join(phrases))

        self.phrase_tfidf = TfidfVectorizer(max_features=100, ngram_range=(1, 3))
        phrase_features = self.phrase_tfidf.fit_transform(all_phrases).toarray()

        # BERT embeddings
        bert_embeddings = []
        for text in df['clean_text']:
            emb = self.encode_text_bert(text)
            bert_embeddings.append(emb)

        bert_embeddings = np.array(bert_embeddings)

        # Text statistics
        df['word_count'] = df['clean_text'].apply(lambda x: len(x.split()))
        df['sentence_count'] = df['text'].apply(lambda x: x.count('.') + x.count('!') + x.count('?'))

        # Combine features
        features = np.hstack([
            bert_embeddings,
            phrase_features,
            df[['word_count', 'sentence_count']].values
        ])

        return features, df['label'].values

    def train_model(self, data_path="data/training_data.csv"):
        print("Loading data...")
        df = pd.read_csv(data_path)

        print("Class distribution before SMOTE:")
        print(df['label'].value_counts())

        # Prepare features
        X, y = self.prepare_features(df)

        # Split data
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=0.2, random_state=42, stratify=y
        )

        # Encode labels to numeric
        from sklearn.preprocessing import LabelEncoder
        label_encoder = LabelEncoder()
        y_train_encoded = label_encoder.fit_transform(y_train)
        y_test_encoded = label_encoder.transform(y_test)

        # Apply SMOTE for handling imbalance (only if enough samples)
        try:
            min_samples = min(np.bincount(y_train_encoded))
            k_neighbors = min(3, max(1, min_samples - 1))
            smote = SMOTE(random_state=42, k_neighbors=k_neighbors)
            X_train_smote, y_train_smote = smote.fit_resample(X_train, y_train_encoded)
            print("SMOTE applied successfully.")
        except ValueError as e:
            print(f"SMOTE not applied due to insufficient samples: {e}")
            print("Using original training data.")
            X_train_smote, y_train_smote = X_train, y_train_encoded

        print("Class distribution after SMOTE:")
        unique, counts = np.unique(y_train_smote, return_counts=True)
        for cls, count in zip(unique, counts):
            print(f"Class {cls}: {count}")

        # Scale features
        self.scaler_bert = StandardScaler()
        bert_dim = 768  # IndoBERT base dimension
        X_train_bert_scaled = self.scaler_bert.fit_transform(X_train_smote[:, :bert_dim])
        X_test_bert_scaled = self.scaler_bert.transform(X_test[:, :bert_dim])

        # Scale phrase features
        phrase_dim = 100
        self.scaler_phrase = StandardScaler()
        X_train_phrase_scaled = self.scaler_phrase.fit_transform(X_train_smote[:, bert_dim:bert_dim+phrase_dim])
        X_test_phrase_scaled = self.scaler_phrase.transform(X_test[:, bert_dim:bert_dim+phrase_dim])

        # Scale text stats
        self.scaler_text = StandardScaler()
        X_train_text_scaled = self.scaler_text.fit_transform(X_train_smote[:, -2:])
        X_test_text_scaled = self.scaler_text.transform(X_test[:, -2:])

        # Combine scaled features
        X_train_scaled = np.hstack([
            X_train_bert_scaled,
            X_train_phrase_scaled,
            X_train_text_scaled
        ])

        X_test_scaled = np.hstack([
            X_test_bert_scaled,
            X_test_phrase_scaled,
            X_test_text_scaled
        ])

        # Train model
        print("Training model...")
        self.model = GradientBoostingClassifier(
            n_estimators=200,
            learning_rate=0.1,
            max_depth=6,
            random_state=42
        )

        self.model.fit(X_train_scaled, y_train_smote)

        # Evaluate
        y_pred_encoded = self.model.predict(X_test_scaled)
        y_pred = label_encoder.inverse_transform(y_pred_encoded)
        y_test_decoded = label_encoder.inverse_transform(y_test_encoded)
        
        print("Test Accuracy:", accuracy_score(y_test_decoded, y_pred))
        print("Classification Report:")
        print(classification_report(y_test_decoded, y_pred))

        # Save model and scalers
        print("Saving model...")
        joblib.dump(self.model, "app/model/model_best.pkl")
        joblib.dump(self.scaler_bert, "app/model/scaler_bert.pkl")
        joblib.dump(self.scaler_phrase, "app/model/scaler_phrase.pkl")
        joblib.dump(self.scaler_text, "app/model/scaler_text.pkl")
        joblib.dump(self.phrase_tfidf, "app/model/phrase_tfidf.pkl")

        # Save feature config
        feature_config = {
            "bert_dim": bert_dim,
            "phrase_dim": phrase_dim,
            "text_stat_cols": ["word_count", "sentence_count"],
            "total_features": X_train_scaled.shape[1],
            "best_model": "Gradient Boosting with SMOTE"
        }

        with open("app/model/feature_config.json", "w") as f:
            json.dump(feature_config, f, indent=2)

        print("Training completed!")

if __name__ == "__main__":
    trainer = ModelTrainer()
    # Note: You need to provide training_data.csv with columns: text, label
    trainer.train_model()