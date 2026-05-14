"""
Spam Classifier AI - Core Machine Learning Model
SRS Section: 2.1 (Supervised Learning), 4.4 (Datasets)
Single source of truth for all integrations
Windows-compatible version
"""

import sys
import os

# Fix Windows encoding for emoji-free operation
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding='utf-8')
        sys.stderr.reconfigure(encoding='utf-8')
    except:
        pass

import pandas as pd
import numpy as np
from sklearn.feature_extraction.text import CountVectorizer, TfidfTransformer
from sklearn.naive_bayes import MultinomialNB
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
from sklearn.metrics import accuracy_score, classification_report
import joblib
import re
import warnings
warnings.filterwarnings('ignore')

# Try importing NLTK, but handle if not available
try:
    import nltk
    from nltk.corpus import stopwords
    from nltk.tokenize import word_tokenize
    
    try:
        nltk.data.find('tokenizers/punkt')
    except LookupError:
        nltk.download('punkt', quiet=True)
    try:
        nltk.data.find('corpora/stopwords')
    except LookupError:
        nltk.download('stopwords', quiet=True)
    
    NLTK_AVAILABLE = True
except ImportError:
    NLTK_AVAILABLE = False
    print("[WARNING] NLTK not installed. Using basic text preprocessing.")
    print("          Install with: pip install nltk")

class SpamClassifier:
    """
    Main Spam Classifier Class
    Implements Goal-Based Agent architecture (SRS Section 2.3)
    """
    
    def __init__(self):
        self.model = None
        self.vectorizer = None
        self.tfidf_transformer = None
        self.pipeline = None
        self.is_trained = False
        self.model_path = "spam_model.joblib"
        self.vectorizer_path = "vectorizer.joblib"
        
        if NLTK_AVAILABLE:
            try:
                self.stop_words = set(stopwords.words('english'))
            except:
                self.stop_words = set()
        else:
            self.stop_words = set()
        
    def preprocess_text(self, text):
        """Text Preprocessing"""
        text = text.lower()
        text = re.sub(r'[^a-zA-Z\s]', '', text)
        text = re.sub(r'\s+', ' ', text).strip()
        
        if NLTK_AVAILABLE and self.stop_words:
            try:
                tokens = word_tokenize(text)
                tokens = [word for word in tokens if word not in self.stop_words]
                return ' '.join(tokens)
            except:
                pass
        
        return text
    
    def train(self, csv_path="spam.csv", save_model=True):
        """Train the classifier"""
        print("=" * 60)
        print("SPAM CLASSIFIER AI - TRAINING PHASE")
        print("=" * 60)
        
        print("\n[1/5] Loading dataset...")
        try:
            data = pd.read_csv(csv_path, encoding='latin-1')
            data = data.iloc[:, :2]
            data.columns = ['label', 'message']
        except:
            try:
                data = pd.read_csv(csv_path, sep='\t', header=None, 
                                  names=["label", "message"], skiprows=1)
            except Exception as e:
                print(f"[ERROR] Could not load dataset: {e}")
                raise
        
        print(f"      Loaded {len(data)} messages")
        print(f"      Ham: {(data['label']=='ham').sum()}, Spam: {(data['label']=='spam').sum()}")
        
        print("\n[2/5] Preprocessing labels...")
        data['label'] = data['label'].map({'ham': 0, 'spam': 1})
        data = data.dropna(subset=['message'])
        
        print("\n[3/5] Preprocessing messages...")
        data['processed_message'] = data['message'].apply(self.preprocess_text)
        
        print("\n[4/5] Splitting dataset (80% training, 20% testing)...")
        X_train, X_test, y_train, y_test = train_test_split(
            data['processed_message'], 
            data['label'], 
            test_size=0.2, 
            random_state=42
        )
        
        print("\n[5/5] Training Machine Learning Pipeline...")
        self.pipeline = Pipeline([
            ('vectorizer', CountVectorizer(max_features=5000)),
            ('tfidf', TfidfTransformer()),
            ('classifier', MultinomialNB(alpha=0.1))
        ])
        
        self.pipeline.fit(X_train, y_train)
        self.is_trained = True
        
        y_pred = self.pipeline.predict(X_test)
        accuracy = accuracy_score(y_test, y_pred)
        
        print(f"\n[SUCCESS] Model Training Complete!")
        print(f"          Accuracy: {accuracy:.2%}")
        print(f"\nClassification Report:")
        print(f"{'='*60}")
        print(classification_report(y_test, y_pred, target_names=['Ham', 'Spam']))
        
        if save_model:
            joblib.dump(self.pipeline, self.model_path)
            print(f"[SAVED] Model saved to: {self.model_path}")
        
        return {
            'accuracy': accuracy,
            'samples_trained': len(X_train),
            'samples_tested': len(X_test)
        }
    
    def load_model(self):
        """Load pre-trained model from disk"""
        if os.path.exists(self.model_path):
            try:
                self.pipeline = joblib.load(self.model_path)
                self.is_trained = True
                print("[LOADED] Model loaded from disk")
                return True
            except Exception as e:
                print(f"[ERROR] Could not load model: {e}")
                return False
        return False
    
    def predict(self, message):
        """
        Predict if a message is spam or ham
        
        Returns:
            dict: {
                'result': 'SPAM' or 'HAM',
                'confidence': float (percentage),
                'explanation': str,
                'raw_score': float
            }
        """
        if not self.is_trained:
            raise Exception("Model not trained! Call train() or load_model() first")
        
        if not message or not message.strip():
            return {
                'result': 'HAM',
                'confidence': 0.0,
                'explanation': 'Empty message',
                'raw_score': 0.0
            }
        
        processed_msg = self.preprocess_text(message)
        probabilities = self.pipeline.predict_proba([processed_msg])[0]
        prediction = self.pipeline.predict([processed_msg])[0]
        
        spam_probability = probabilities[1]
        ham_probability = probabilities[0]
        
        if prediction == 1:  # SPAM
            result = 'SPAM'
            confidence = spam_probability * 100
            if confidence > 90:
                explanation = "Very high confidence - Contains strong spam indicators"
            elif confidence > 70:
                explanation = "High confidence - Contains multiple spam patterns"
            else:
                explanation = "Moderate confidence - May contain some spam-like content"
        else:  # HAM
            result = 'HAM'
            confidence = ham_probability * 100
            explanation = "Message appears to be legitimate communication"
        
        return {
            'result': result,
            'confidence': round(confidence, 2),
            'explanation': explanation,
            'raw_score': round(spam_probability, 4)
        }
    
    def get_feature_importance(self, message, top_n=10):
        """Get words that contributed most to classification"""
        if not self.is_trained:
            return []
        
        processed_msg = self.preprocess_text(message)
        vectorizer = self.pipeline.named_steps['vectorizer']
        classifier = self.pipeline.named_steps['classifier']
        
        feature_names = vectorizer.get_feature_names_out()
        msg_vector = vectorizer.transform([processed_msg])
        msg_array = msg_vector.toarray()[0]
        word_indices = msg_array.nonzero()[0]
        
        importance_scores = []
        for idx in word_indices:
            word = feature_names[idx]
            score = classifier.feature_log_prob_[1][idx] - classifier.feature_log_prob_[0][idx]
            importance_scores.append({
                'word': word,
                'importance': round(score, 4),
                'indicates_spam': score > 0
            })
        
        importance_scores.sort(key=lambda x: abs(x['importance']), reverse=True)
        return importance_scores[:top_n]


if __name__ == "__main__":
    print("=" * 60)
    print("SPAM CLASSIFIER - STANDALONE TEST")
    print("=" * 60)
    
    clf = SpamClassifier()
    
    if os.path.exists("spam_model.joblib"):
        print("\nLoading existing model...")
        clf.load_model()
    else:
        print("\nTraining new model...")
        clf.train()
    
    test_messages = [
        "Congratulations! You've won a free iPhone! Click here to claim!",
        "Hey, are you coming to the meeting at 3pm?",
        "URGENT: Your account has been hacked! Send your password now!",
        "Don't forget to pick up milk on your way home"
    ]
    
    print("\n" + "=" * 60)
    print("TESTING PREDICTIONS")
    print("=" * 60)
    
    for msg in test_messages:
        result = clf.predict(msg)
        print(f"\nMessage: {msg[:60]}...")
        print(f"Result: {result['result']}")
        print(f"Confidence: {result['confidence']}%")
        print(f"Explanation: {result['explanation']}")