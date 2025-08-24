import numpy as np
from sklearn.linear_model import SGDClassifier
from sklearn.ensemble import RandomForestClassifier
from sklearn.preprocessing import StandardScaler
import logging
from config.settings import Config

logger = logging.getLogger(__name__)

class TradingModel:
    def __init__(self):
        # Use online learning model for rapid adaptation
        self.model = SGDClassifier(
            loss='log_loss', 
            learning_rate='optimal', 
            eta0=0.1,
            random_state=42
        )
        self.scaler = StandardScaler()
        self.is_trained = False
        self.training_samples = 0
        
    def train(self, features, labels):
        """Train the model on available data"""
        if features is None or labels is None or len(features) < Config.WARMUP_PERIOD:
            logger.warning(f"Not enough data for training. Have {len(features) if features is not None else 0}, need {Config.WARMUP_PERIOD}")
            return False
            
        # Use the latest data for training
        X = features.iloc[-100:] if len(features) > 100 else features
        y = labels.iloc[-100:] if len(labels) > 100 else labels
        
        # Ensure we have matching lengths
        min_len = min(len(X), len(y))
        X = X.iloc[-min_len:]
        y = y.iloc[-min_len:]
        
        try:
            # Scale features
            if self.training_samples == 0:
                X_scaled = self.scaler.fit_transform(X)
            else:
                X_scaled = self.scaler.transform(X)
                
            # Train model
            self.model.partial_fit(X_scaled, y, classes=[0, 1])
            self.is_trained = True
            self.training_samples += len(X)
            
            logger.info(f"Model trained on {len(X)} samples. Total samples: {self.training_samples}")
            return True
        except Exception as e:
            logger.error(f"Error training model: {e}")
            return False
    
    def predict(self, features):
        """Make a prediction based on current features"""
        if not self.is_trained:
            return 0.5  # Neutral prediction if model not trained
            
        try:
            # Scale features
            features_scaled = self.scaler.transform(features)
            
            # Predict probability of success
            proba = self.model.predict_proba(features_scaled)
            return proba[0][1]  # Return probability of class 1 (success)
        except Exception as e:
            logger.error(f"Error making prediction: {e}")
            return 0.5
            
    def save_model(self, filepath):
        """Save model to file"""
        import joblib
        try:
            joblib.dump({
                'model': self.model,
                'scaler': self.scaler,
                'is_trained': self.is_trained,
                'training_samples': self.training_samples
            }, filepath)
            logger.info(f"Model saved to {filepath}")
            return True
        except Exception as e:
            logger.error(f"Error saving model: {e}")
            return False
            
    def load_model(self, filepath):
        """Load model from file"""
        import joblib
        try:
            data = joblib.load(filepath)
            self.model = data['model']
            self.scaler = data['scaler']
            self.is_trained = data['is_trained']
            self.training_samples = data['training_samples']
            logger.info(f"Model loaded from {filepath}. Training samples: {self.training_samples}")
            return True
        except Exception as e:
            logger.error(f"Error loading model: {e}")
            return False
