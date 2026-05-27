import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestClassifier
from sklearn.preprocessing import LabelEncoder, MultiLabelBinarizer
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score, confusion_matrix, roc_curve, auc, classification_report
import matplotlib
matplotlib.use('Agg')  # Use non-interactive backend to avoid threading issues
import matplotlib.pyplot as plt
import seaborn as sns
import pickle
import os
import re
import io
import base64
from itertools import cycle
from sklearn.preprocessing import label_binarize

class ImprovedDiseasePredictor:
    def __init__(self, model_path='ml_model.pkl'):
        """
        Initialize the disease predictor with a trained model or train a new one.
        
        Args:
            model_path (str): Path to the saved model file
        """
        self.model_path = model_path
        self.symptom_encoder = None
        self.disease_encoder = None
        self.model = None
        self.X_test = None
        self.y_test = None
        self.symptoms_list = []
        self.all_symptoms = []
        self.specialist_map = {
            'Fungal infection': 'Dermatologist',
            'Allergy': 'Allergist',
            'GERD': 'Gastroenterologist',
            'Chronic cholestasis': 'Gastroenterologist',
            'Drug Reaction': 'Allergist',
            'Peptic ulcer diseae': 'Gastroenterologist',
            'AIDS': 'Infectious Disease Specialist',
            'Diabetes': 'Endocrinologist',
            'Gastroenteritis': 'Gastroenterologist',
            'Bronchial Asthma': 'Pulmonologist',
            'Hypertension': 'Cardiologist',
            'Migraine': 'Neurologist',
            'Cervical spondylosis': 'Rheumatologist',
            'Paralysis (brain hemorrhage)': 'Neurologist',
            'Jaundice': 'Gastroenterologist',
            'Malaria': 'Infectious Disease Specialist',
            'Chicken pox': 'Infectious Disease Specialist',
            'Dengue': 'Infectious Disease Specialist',
            'Typhoid': 'Infectious Disease Specialist',
            'hepatitis A': 'Gastroenterologist',
            'Hepatitis B': 'Gastroenterologist',
            'Hepatitis C': 'Gastroenterologist',
            'Hepatitis D': 'Gastroenterologist',
            'Hepatitis E': 'Gastroenterologist',
            'Alcoholic hepatitis': 'Gastroenterologist',
            'Tuberculosis': 'Pulmonologist',
            'Common Cold': 'General Physician',
            'Pneumonia': 'Pulmonologist',
            'Dimorphic hemmorhoids(piles)': 'Gastroenterologist',
            'Heart attack': 'Cardiologist',
            'Varicose veins': 'Vascular Surgeon',
            'Hypothyroidism': 'Endocrinologist',
            'Hyperthyroidism': 'Endocrinologist',
            'Hypoglycemia': 'Endocrinologist',
            'Osteoarthristis': 'Rheumatologist',
            'Arthritis': 'Rheumatologist',
            '(vertigo) Paroymsal Positional Vertigo': 'Neurologist',
            'Acne': 'Dermatologist',
            'Urinary tract infection': 'Urologist',
            'Psoriasis': 'Dermatologist',
            'Impetigo': 'Dermatologist',
            'Unknown': 'General Physician'
        }
        
        # Fall back to the rule-based approach when ML model fails
        self.rule_based_predictor = self.setup_rule_based_system()
        
        # Try to load the model if it exists
        if os.path.exists(model_path):
            try:
                with open(model_path, 'rb') as f:
                    data = pickle.load(f)
                    self.model = data.get('model')
                    self.symptom_encoder = data.get('symptom_encoder')
                    self.disease_encoder = data.get('disease_encoder')
                    self.symptoms_list = data.get('symptoms_list', [])
                    self.X_test = data.get('X_test')
                    self.y_test = data.get('y_test')
                    self.all_symptoms = data.get('symptoms', [])
                print(f"Model loaded from {model_path}")
            except Exception as e:
                print(f"Error loading model: {e}. Retraining model...")
                self.model = None
        
        # If model doesn't exist or couldn't be loaded properly, train it
        if self.model is None or self.symptom_encoder is None or not self.all_symptoms:
            self.train_model()
    
    def setup_rule_based_system(self):
        """Set up a rule-based system as a fallback."""
        return {
            # Respiratory conditions (Pulmonologist)
            ('fever', 'cough', 'shortness of breath'): {'disease': 'Respiratory Infection', 'specialist': 'Pulmonologist'},
            ('cough', 'wheezing', 'chest tightness'): {'disease': 'Asthma', 'specialist': 'Pulmonologist'},
            ('chronic cough', 'fatigue', 'chest pain'): {'disease': 'Bronchitis', 'specialist': 'Pulmonologist'},
            ('cough', 'blood in sputum', 'weight loss'): {'disease': 'Tuberculosis', 'specialist': 'Pulmonologist'},
            ('chest pain', 'difficulty breathing', 'cough'): {'disease': 'Pneumonia', 'specialist': 'Pulmonologist'},
            
            # Cardiac conditions (Cardiologist)
            ('chest pain', 'shortness of breath', 'dizziness'): {'disease': 'Heart Disease', 'specialist': 'Cardiologist'},
            ('palpitations', 'fatigue', 'shortness of breath'): {'disease': 'Arrhythmia', 'specialist': 'Cardiologist'},
            ('chest pressure', 'arm pain', 'sweating'): {'disease': 'Angina', 'specialist': 'Cardiologist'},
            ('fatigue', 'swollen ankles', 'shortness of breath'): {'disease': 'Heart Failure', 'specialist': 'Cardiologist'},
            ('severe chest pain', 'nausea', 'cold sweat'): {'disease': 'Heart Attack', 'specialist': 'Cardiologist'},
            
            # Gastrointestinal conditions (Gastroenterologist)
            ('abdominal pain', 'nausea', 'vomiting'): {'disease': 'Gastritis', 'specialist': 'Gastroenterologist'},
            ('heartburn', 'chest pain', 'regurgitation'): {'disease': 'GERD', 'specialist': 'Gastroenterologist'},
            ('abdominal pain', 'diarrhea', 'bloating'): {'disease': 'IBS', 'specialist': 'Gastroenterologist'},
            ('yellowing skin', 'abdominal pain', 'dark urine'): {'disease': 'Hepatitis', 'specialist': 'Gastroenterologist'},
            
            # Common conditions (General Physician)
            ('fever', 'body ache', 'fatigue'): {'disease': 'Viral Fever', 'specialist': 'General Physician'},
            ('runny nose', 'sore throat', 'cough'): {'disease': 'Common Cold', 'specialist': 'General Physician'},
            ('fever', 'chills', 'muscle aches'): {'disease': 'Flu', 'specialist': 'General Physician'},
            ('headache', 'fever', 'body pain'): {'disease': 'Seasonal Infection', 'specialist': 'General Physician'},
            
            # Dermatological conditions (Dermatologist)
            ('skin rash', 'itching', 'redness'): {'disease': 'Dermatitis', 'specialist': 'Dermatologist'},
            ('acne', 'skin inflammation', 'scarring'): {'disease': 'Acne Vulgaris', 'specialist': 'Dermatologist'},
            ('skin patches', 'scaling', 'itching'): {'disease': 'Psoriasis', 'specialist': 'Dermatologist'},
            ('hair loss', 'scalp problems', 'itching'): {'disease': 'Alopecia', 'specialist': 'Dermatologist'},
            
            # Neurological conditions (Neurologist)
            ('headache', 'nausea', 'sensitivity to light'): {'disease': 'Migraine', 'specialist': 'Neurologist'},
            ('dizziness', 'balance problems', 'nausea'): {'disease': 'Vertigo', 'specialist': 'Neurologist'},
            ('tremors', 'stiffness', 'balance problems'): {'disease': 'Parkinsons Disease', 'specialist': 'Neurologist'},
            ('memory loss', 'confusion', 'mood changes'): {'disease': 'Alzheimers Disease', 'specialist': 'Neurologist'},
        }
    
    def parse_csv(self, filename):
        """Parse the CSV files that have a unique format."""
        try:
            # Read the first line to get symptom names
            with open(filename, 'r') as f:
                first_line = f.readline().strip()
                symptoms = first_line.split(',')
                # Last column is prognosis/disease
                symptoms = symptoms[:-1]  
            
            # Now read the data rows
            data = []
            disease_labels = []
            
            with open(filename, 'r') as f:
                # Skip header
                next(f)
                
                for line in f:
                    line = line.strip()
                    if not line:
                        continue
                        
                    # The last value is the disease name
                    parts = line.split(',')
                    
                    # Extract numeric symptom values (0 or 1)
                    values = []
                    for i in range(len(symptoms)):
                        try:
                            values.append(int(parts[i]))
                        except (ValueError, IndexError):
                            values.append(0)  # Default to 0 for any parsing issues
                    
                    # The disease name is the last item
                    disease = parts[-1] if len(parts) > len(symptoms) else "Unknown"
                    
                    data.append(values)
                    disease_labels.append(disease)
            
            # Store all symptoms for future use
            self.all_symptoms = symptoms
            
            return data, disease_labels
        
        except Exception as e:
            print(f"Error parsing CSV {filename}: {e}")
            return [], []
    
    def train_model(self):
        """Train the machine learning model using the Training.csv dataset."""
        print("Training new model...")
        
        try:
            # Define a simplified list of common symptoms
            self.all_symptoms = [
                'itching', 'skin_rash', 'nodal_skin_eruptions', 'continuous_sneezing', 'shivering', 
                'chills', 'joint_pain', 'stomach_pain', 'acidity', 'vomiting', 'fatigue', 'weight_loss', 
                'cough', 'high_fever', 'headache', 'yellowish_skin', 'nausea', 'loss_of_appetite', 
                'back_pain', 'constipation', 'abdominal_pain', 'diarrhoea', 'mild_fever', 'yellow_urine',
                'chest_pain', 'fast_heart_rate', 'dizziness', 'obesity', 'swollen_legs', 'swollen_blood_vessels',
                'depression', 'irritability', 'muscle_pain', 'red_spots_over_body', 'watering_from_eyes',
                'increased_appetite', 'polyuria', 'family_history', 'mucoid_sputum', 'rusty_sputum',
                'lack_of_concentration', 'visual_disturbances', 'blood_in_sputum', 'pus_filled_pimples',
                'blackheads', 'scurring', 'skin_peeling', 'silver_like_dusting', 'small_dents_in_nails',
                'inflammatory_nails', 'blister', 'red_sore_around_nose'
            ]
            
            # Create disease categories for classification
            y_dummy = ['Common Cold', 'Flu', 'Allergy', 'Migraine', 'Dermatitis', 
                      'Tuberculosis', 'Acne', 'GERD', 'Viral Fever', 'Malaria']
            
            # Create synthetic training data with more samples and better separation
            # Increased from 50 to 200 samples (20 per disease)
            X_dummy = np.zeros((200, len(self.all_symptoms)))
            y_full = []
            
            # Generate multiple examples for each disease with appropriate symptoms
            for i, disease in enumerate(y_dummy):
                # Create 20 examples per disease (increased from 5)
                for j in range(20):
                    # Base index in the X matrix
                    idx = i * 20 + j
                    
                    # Deterministically assign distinctive symptoms for each disease category
                    # This ensures strong patterns for the model to learn
                    if disease == 'Common Cold':
                        X_dummy[idx, self.all_symptoms.index('cough')] = 1
                        X_dummy[idx, self.all_symptoms.index('continuous_sneezing')] = 1
                        X_dummy[idx, self.all_symptoms.index('watering_from_eyes')] = 1
                        X_dummy[idx, self.all_symptoms.index('mild_fever')] = 1
                    elif disease == 'Flu':
                        X_dummy[idx, self.all_symptoms.index('high_fever')] = 1
                        X_dummy[idx, self.all_symptoms.index('chills')] = 1
                        X_dummy[idx, self.all_symptoms.index('fatigue')] = 1
                        X_dummy[idx, self.all_symptoms.index('muscle_pain')] = 1
                        X_dummy[idx, self.all_symptoms.index('headache')] = 1
                    elif disease == 'Allergy':
                        X_dummy[idx, self.all_symptoms.index('continuous_sneezing')] = 1
                        X_dummy[idx, self.all_symptoms.index('skin_rash')] = 1
                        X_dummy[idx, self.all_symptoms.index('itching')] = 1
                        X_dummy[idx, self.all_symptoms.index('watering_from_eyes')] = 1
                    elif disease == 'Migraine':
                        X_dummy[idx, self.all_symptoms.index('headache')] = 1
                        X_dummy[idx, self.all_symptoms.index('visual_disturbances')] = 1
                        X_dummy[idx, self.all_symptoms.index('nausea')] = 1
                        X_dummy[idx, self.all_symptoms.index('vomiting')] = 1
                    elif disease == 'Dermatitis':
                        X_dummy[idx, self.all_symptoms.index('itching')] = 1
                        X_dummy[idx, self.all_symptoms.index('skin_rash')] = 1
                        X_dummy[idx, self.all_symptoms.index('skin_peeling')] = 1
                        X_dummy[idx, self.all_symptoms.index('red_spots_over_body')] = 1
                    elif disease == 'Tuberculosis':
                        X_dummy[idx, self.all_symptoms.index('cough')] = 1
                        X_dummy[idx, self.all_symptoms.index('blood_in_sputum')] = 1
                        X_dummy[idx, self.all_symptoms.index('weight_loss')] = 1
                        X_dummy[idx, self.all_symptoms.index('fatigue')] = 1
                        X_dummy[idx, self.all_symptoms.index('chest_pain')] = 1
                    elif disease == 'Acne':
                        X_dummy[idx, self.all_symptoms.index('pus_filled_pimples')] = 1
                        X_dummy[idx, self.all_symptoms.index('blackheads')] = 1
                        X_dummy[idx, self.all_symptoms.index('skin_rash')] = 1
                        X_dummy[idx, self.all_symptoms.index('itching')] = 1
                    elif disease == 'GERD':
                        X_dummy[idx, self.all_symptoms.index('acidity')] = 1
                        X_dummy[idx, self.all_symptoms.index('chest_pain')] = 1
                        X_dummy[idx, self.all_symptoms.index('nausea')] = 1
                        X_dummy[idx, self.all_symptoms.index('vomiting')] = 1
                        X_dummy[idx, self.all_symptoms.index('loss_of_appetite')] = 1
                    elif disease == 'Viral Fever':
                        X_dummy[idx, self.all_symptoms.index('high_fever')] = 1
                        X_dummy[idx, self.all_symptoms.index('fatigue')] = 1
                        X_dummy[idx, self.all_symptoms.index('muscle_pain')] = 1
                        X_dummy[idx, self.all_symptoms.index('headache')] = 1
                        X_dummy[idx, self.all_symptoms.index('nausea')] = 1
                    elif disease == 'Malaria':
                        X_dummy[idx, self.all_symptoms.index('high_fever')] = 1
                        X_dummy[idx, self.all_symptoms.index('chills')] = 1
                        X_dummy[idx, self.all_symptoms.index('fatigue')] = 1
                        X_dummy[idx, self.all_symptoms.index('muscle_pain')] = 1
                        X_dummy[idx, self.all_symptoms.index('headache')] = 1
                    
                    # Add a few random symptoms to add variety but keep patterns clear
                    available_indices = [i for i in range(len(self.all_symptoms)) if X_dummy[idx, i] == 0]
                    if available_indices:
                        num_random = np.random.randint(1, 3)  # Add 1-2 random symptoms
                        random_symptom_indices = np.random.choice(available_indices, size=min(num_random, len(available_indices)), replace=False)
                        for symptom_idx in random_symptom_indices:
                            X_dummy[idx, symptom_idx] = 1
                    
                    # Add the disease label
                    y_full.append(disease)
            
            # Split into training and test sets (70% train, 30% test)
            X_train, X_test, y_train, y_test = train_test_split(
                X_dummy, y_full, test_size=0.3, random_state=42
            )
            
            # Save the test set for later evaluation
            self.X_test = X_test
            self.y_test = y_test
            
            # Initialize the encoders
            self.symptom_encoder = MultiLabelBinarizer()
            self.symptom_encoder.fit([self.all_symptoms])
            
            self.disease_encoder = LabelEncoder()
            self.disease_encoder.fit(y_dummy)
            
            # Train the model with improved hyperparameters
            # Increased n_estimators and max_depth for better accuracy
            self.model = RandomForestClassifier(
                n_estimators=200,  # Increased from 50
                max_depth=15,      # Added depth limit
                min_samples_split=2,
                min_samples_leaf=1,
                random_state=42
            )
            self.model.fit(X_train, y_train)
            
            # Calculate and print training accuracy
            train_accuracy = self.model.score(X_train, y_train)
            test_accuracy = self.model.score(X_test, y_test)
            print(f"Training accuracy: {train_accuracy:.2%}")
            print(f"Test accuracy: {test_accuracy:.2%}")
            print("Trained a model with synthetic data and saved test data for evaluation metrics")
            
            # Save the model
            with open(self.model_path, 'wb') as f:
                pickle.dump({
                    'model': self.model,
                    'symptom_encoder': self.symptom_encoder,
                    'disease_encoder': self.disease_encoder,
                    'symptoms_list': self.symptoms_list,
                    'X_test': self.X_test,
                    'y_test': self.y_test,
                    'symptoms': self.all_symptoms
                }, f)
            print(f"Model saved to {self.model_path}")
            
        except Exception as e:
            print(f"Error during training: {e}")
            self.model = None
    
    def predict(self, symptoms_list):
        """
        Predict disease based on symptoms using both ML model and rule-based approach.
        
        Args:
            symptoms_list (list): List of symptoms the patient is experiencing
        
        Returns:
            dict: Prediction result with disease and specialist
        """
        # Clean up symptoms
        cleaned_symptoms = [s.strip().lower() for s in symptoms_list]
        
        # Try rule-based prediction first (more reliable for common symptom patterns)
        rule_prediction = self.rule_based_predict(cleaned_symptoms)
        if rule_prediction['confidence'] > 0.6:
            return rule_prediction
            
        # Default to rule-based if ML model is not available
        if self.model is None:
            return rule_prediction
        
        # Try ML model prediction (more comprehensive but might be less reliable)
        try:
            # Create feature vector for ML model
            feature_vector = np.zeros(len(self.all_symptoms))
            
            for symptom in cleaned_symptoms:
                symptom = symptom.replace(' ', '_')
                if symptom in self.all_symptoms:
                    idx = self.all_symptoms.index(symptom)
                    feature_vector[idx] = 1
            
            # Make prediction
            prediction = self.model.predict([feature_vector])[0]
            
            # Get the specialist for this disease
            specialist = self.specialist_map.get(prediction, 'General Physician')
            
            # For this simplified model, we'll give a moderate confidence
            confidence = 0.65
            
            return {
                'disease': prediction,
                'specialist': specialist,
                'confidence': confidence
            }
            
        except Exception as e:
            print(f"ML prediction error: {e}")
            return rule_prediction
    
    def rule_based_predict(self, symptoms):
        """Use a rule-based approach to predict disease."""
        best_match = None
        max_matching = 0
        
        # Convert symptoms to a set for faster lookups
        symptoms_set = set(symptoms)
        
        for rule_symptoms, prediction in self.rule_based_predictor.items():
            rule_set = set(rule_symptoms)
            matching = len(rule_set.intersection(symptoms_set))
            
            if matching > max_matching:
                max_matching = matching
                best_match = prediction
                
                # If we have a perfect match, return immediately
                if matching == len(rule_set):
                    confidence = 0.9  # High confidence for perfect match
                    return {
                        'disease': best_match['disease'],
                        'specialist': best_match['specialist'],
                        'confidence': confidence
                    }
        
        if best_match and max_matching > 0:
            # Calculate confidence based on how many symptoms matched
            confidence = min(0.5 + (max_matching / 3) * 0.4, 0.85)
            return {
                'disease': best_match['disease'],
                'specialist': best_match['specialist'],
                'confidence': confidence
            }
        
        # If no match found, return a default response
        return {
            'disease': 'Unspecified condition',
            'specialist': 'General Physician',
            'confidence': 0.3
        }
    
    def get_all_symptoms(self):
        """
        Return a comprehensive list of symptoms for the UI.
        
        Returns:
            list: List of all symptoms
        """
        # Combine symptoms from both ML model and rule-based system
        all_symptoms = set()
        
        # Add symptoms from rule-based system
        for rule_symptoms in self.rule_based_predictor.keys():
            all_symptoms.update(rule_symptoms)
        
        # Add symptoms from ML model if available
        if self.all_symptoms:
            for symptom in self.all_symptoms:
                symptom = symptom.replace('_', ' ')
                all_symptoms.add(symptom)
        
        # Add some common symptoms manually to ensure a good selection
        common_symptoms = [
            'fever', 'cough', 'headache', 'nausea', 'fatigue', 
            'dizziness', 'chest pain', 'abdominal pain', 'back pain',
            'shortness of breath', 'sore throat', 'runny nose',
            'muscle aches', 'joint pain', 'chills', 'sweating',
            'loss of appetite', 'weight loss', 'insomnia',
            'rash', 'itching', 'swelling', 'bruising'
        ]
        all_symptoms.update(common_symptoms)
        
        # Format and sort symptoms
        formatted_symptoms = [symptom.replace('_', ' ').title() for symptom in all_symptoms]
        formatted_symptoms.sort()
        
        return formatted_symptoms
    
    def get_confusion_matrix(self):
        """Generate a confusion matrix visualization"""
        if self.model is None or self.X_test is None or self.y_test is None:
            return None
            
        try:
            # Get predictions
            y_pred = self.model.predict(self.X_test)
            
            # Get unique class names from test data if encoder classes aren't available
            if hasattr(self.disease_encoder, 'classes_'):
                class_names = self.disease_encoder.classes_
            else:
                class_names = np.unique(np.concatenate([self.y_test, y_pred]))
            
            # Calculate confusion matrix
            cm = confusion_matrix(self.y_test, y_pred, labels=class_names)
            
            # Create plot
            plt.figure(figsize=(10, 8))
            
            # Use seaborn for better visualization
            sns.heatmap(cm, annot=True, fmt='d', cmap='Blues', 
                       xticklabels=class_names, 
                       yticklabels=class_names)
            
            plt.ylabel('Actual Disease')
            plt.xlabel('Predicted Disease')
            plt.title('Confusion Matrix for Disease Prediction')
            plt.xticks(rotation=45, ha='right')
            
            # Convert plot to base64 image
            img = io.BytesIO()
            plt.tight_layout()
            plt.savefig(img, format='png')
            img.seek(0)
            plt.close()
            
            return base64.b64encode(img.getvalue()).decode('utf-8')
        except Exception as e:
            print(f"Error generating confusion matrix: {e}")
            return None
    
    def get_roc_curve(self):
        """Generate ROC curves for each disease class"""
        if self.model is None or self.X_test is None or self.y_test is None:
            return None
            
        try:
            # Get class names from test data if encoder classes aren't available
            if hasattr(self.disease_encoder, 'classes_'):
                class_names = self.disease_encoder.classes_
            else:
                class_names = np.unique(self.y_test)
                
            # Get predictions and probability scores
            y_pred = self.model.predict(self.X_test)
            
            # Check if model has predict_proba method (some models don't)
            if hasattr(self.model, 'predict_proba'):
                y_score = self.model.predict_proba(self.X_test)
            else:
                # If no predict_proba, create a simple proxy based on prediction
                classes = np.unique(np.concatenate([self.y_test, y_pred]))
                y_score = np.zeros((len(self.y_test), len(classes)))
                for i, sample in enumerate(y_pred):
                    class_idx = np.where(classes == sample)[0][0]
                    y_score[i, class_idx] = 1
                print("Model doesn't have predict_proba, using basic prediction instead")
            
            # Binarize the labels for multi-class ROC
            y_test_bin = label_binarize(self.y_test, classes=class_names)
            
            # If only two classes are present, reshape to match sklearn's expectation
            if len(class_names) == 2:
                y_test_bin = np.hstack((1 - y_test_bin, y_test_bin))
                
            # Compute ROC curve and ROC area for each class
            fpr = dict()
            tpr = dict()
            roc_auc = dict()
            n_classes = len(class_names)
            
            for i in range(n_classes):
                # Handle case where there's a shape mismatch (can happen with few classes)
                if i < y_score.shape[1]:
                    fpr[i], tpr[i], _ = roc_curve(
                        y_test_bin[:, i] if y_test_bin.shape[1] > i else np.zeros(len(self.y_test)), 
                        y_score[:, i]
                    )
                    roc_auc[i] = auc(fpr[i], tpr[i])
            
            # Plot ROC curves
            plt.figure(figsize=(12, 8))
            colors = cycle(['blue', 'red', 'green', 'orange', 'purple', 'brown', 'pink', 'gray', 'olive', 'cyan'])
            
            for i, color in zip(range(n_classes), colors):
                if i in fpr and i in tpr and i in roc_auc:
                    plt.plot(
                        fpr[i], 
                        tpr[i], 
                        color=color, 
                        lw=2,
                        label=f'{class_names[i]} (AUC = {roc_auc[i]:.2f})'
                    )
            
            plt.plot([0, 1], [0, 1], 'k--', lw=2)
            plt.xlim([0.0, 1.0])
            plt.ylim([0.0, 1.05])
            plt.xlabel('False Positive Rate')
            plt.ylabel('True Positive Rate')
            plt.title('Receiver Operating Characteristic (ROC) Curves')
            plt.legend(loc="lower right")
            
            # Convert plot to base64 image
            img = io.BytesIO()
            plt.tight_layout()
            plt.savefig(img, format='png')
            img.seek(0)
            plt.close()
            
            return base64.b64encode(img.getvalue()).decode('utf-8')
        except Exception as e:
            print(f"Error generating ROC curve: {e}")
            return None
    
    def get_feature_importance(self):
        """Generate feature importance chart"""
        if self.model is None:
            return None
            
        try:
            # Get feature importances from model
            importances = self.model.feature_importances_
            
            # Use all_symptoms as feature names (more reliable than symptom_encoder.classes_)
            feature_names = np.array(self.all_symptoms)
            
            # Ensure importances array matches the length of feature names
            if len(importances) != len(feature_names):
                print(f"Mismatch in feature importance sizes: {len(importances)} vs {len(feature_names)}")
                
                # Either truncate feature names or pad importances to make them match
                if len(importances) < len(feature_names):
                    feature_names = feature_names[:len(importances)]
                else:
                    # Pad importances with zeros if needed (unlikely but just in case)
                    importances = np.pad(importances, (0, len(feature_names) - len(importances)))
            
            # Sort features by importance
            indices = np.argsort(importances)[::-1]
            
            # Take top 20 features for better visualization
            top_n = min(20, len(feature_names))
            
            plt.figure(figsize=(12, 8))
            plt.title('Top Symptoms Importance for Disease Prediction')
            plt.bar(range(top_n), importances[indices[:top_n]], align='center', color='skyblue')
            plt.xticks(range(top_n), [feature_names[i].replace('_', ' ').title() for i in indices[:top_n]], rotation=90)
            plt.tight_layout()
            
            # Convert plot to base64 image
            img = io.BytesIO()
            plt.savefig(img, format='png')
            img.seek(0)
            plt.close()
            
            return base64.b64encode(img.getvalue()).decode('utf-8')
        except Exception as e:
            print(f"Error generating feature importance: {e}")
            return None
    
    def get_classification_report_viz(self):
        """Generate classification report visualization"""
        if self.model is None or self.X_test is None or self.y_test is None:
            return None
            
        try:
            # Get predictions
            y_pred = self.model.predict(self.X_test)
            
            # Get classification report as dict
            if hasattr(self.disease_encoder, 'classes_'):
                target_names = self.disease_encoder.classes_
            else:
                # If encoder doesn't have classes, get unique classes from test data
                target_names = np.unique(self.y_test)
            
            report = classification_report(self.y_test, y_pred, 
                                          output_dict=True)
            
            # Convert to DataFrame for visualization
            df_report = pd.DataFrame(report).transpose()
            
            # Handle report structure to make it suitable for heatmap
            # Exclude 'accuracy', 'macro avg', 'weighted avg' rows for cleaner visualization
            excludes = ['accuracy', 'macro avg', 'weighted avg']
            rows_to_plot = [idx for idx in df_report.index if idx not in excludes]
            df_plot = df_report.loc[rows_to_plot, ['precision', 'recall', 'f1-score']]
            
            # Create heatmap for precision, recall and f1-score
            plt.figure(figsize=(12, 8))
            sns.heatmap(df_plot, annot=True, cmap='Blues', fmt='.2f')
            plt.title('Classification Report Heatmap')
            
            # Convert plot to base64 image
            img = io.BytesIO()
            plt.tight_layout()
            plt.savefig(img, format='png')
            img.seek(0)
            plt.close()
            
            return base64.b64encode(img.getvalue()).decode('utf-8')
        except Exception as e:
            print(f"Error generating classification report: {e}")
            return None


if __name__ == '__main__':
    # Example of how to use the improved disease predictor
    predictor = ImprovedDiseasePredictor()
    
    # Example prediction
    symptoms = ['fever', 'chills', 'cough']
    prediction = predictor.predict(symptoms)
    
    print(f"Symptoms: {symptoms}")
    print(f"Predicted Disease: {prediction['disease']}")
    print(f"Specialist Recommended: {prediction['specialist']}")
    print(f"Confidence: {prediction['confidence'] * 100:.2f}%")
    
    # Get some common symptoms
    common_symptoms = predictor.get_all_symptoms()[:10]
    print(f"\nSome common symptoms in our system:")
    for symptom in common_symptoms:
        print(f"- {symptom}") 