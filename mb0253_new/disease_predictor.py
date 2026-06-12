class DiseasePredictor:
    def __init__(self):
        # Comprehensive symptom to disease and specialist mapping
        self.disease_mapping = {
            # Respiratory conditions (Pulmonologist)
            'fever,cough,shortness of breath': {'disease': 'Respiratory Infection', 'specialist': 'Pulmonologist'},
            'cough,wheezing,chest tightness': {'disease': 'Asthma', 'specialist': 'Pulmonologist'},
            'chronic cough,fatigue,chest pain': {'disease': 'Bronchitis', 'specialist': 'Pulmonologist'},
            'cough,blood in sputum,weight loss': {'disease': 'Tuberculosis', 'specialist': 'Pulmonologist'},
            'shortness of breath,sleep problems,snoring': {'disease': 'Sleep Apnea', 'specialist': 'Pulmonologist'},
            'chest pain,difficulty breathing,cough with mucus': {'disease': 'Pneumonia', 'specialist': 'Pulmonologist'},
            
            # Cardiac conditions (Cardiologist)
            'chest pain,shortness of breath,dizziness': {'disease': 'Heart Disease', 'specialist': 'Cardiologist'},
            'palpitations,fatigue,shortness of breath': {'disease': 'Arrhythmia', 'specialist': 'Cardiologist'},
            'chest pressure,arm pain,sweating': {'disease': 'Angina', 'specialist': 'Cardiologist'},
            'fatigue,swollen ankles,shortness of breath': {'disease': 'Heart Failure', 'specialist': 'Cardiologist'},
            'severe chest pain,nausea,cold sweat': {'disease': 'Heart Attack', 'specialist': 'Cardiologist'},
            'leg pain,swelling,warmth in legs': {'disease': 'Deep Vein Thrombosis', 'specialist': 'Cardiologist'},
            
            # Neurological conditions (Neurologist)
            'headache,nausea,sensitivity to light': {'disease': 'Migraine', 'specialist': 'Neurologist'},
            'dizziness,balance problems,nausea': {'disease': 'Vertigo', 'specialist': 'Neurologist'},
            'tremors,stiffness,balance problems': {'disease': 'Parkinsons Disease', 'specialist': 'Neurologist'},
            'memory loss,confusion,mood changes': {'disease': 'Alzheimers Disease', 'specialist': 'Neurologist'},
            'seizures,loss of consciousness,confusion': {'disease': 'Epilepsy', 'specialist': 'Neurologist'},
            'numbness,tingling,weakness': {'disease': 'Multiple Sclerosis', 'specialist': 'Neurologist'},
            'sudden numbness,difficulty speaking,severe headache': {'disease': 'Stroke', 'specialist': 'Neurologist'},
            
            # Rheumatological conditions (Rheumatologist)
            'joint pain,stiffness,swelling': {'disease': 'Arthritis', 'specialist': 'Rheumatologist'},
            'muscle pain,fatigue,joint stiffness': {'disease': 'Fibromyalgia', 'specialist': 'Rheumatologist'},
            'joint pain,rash,fatigue': {'disease': 'Lupus', 'specialist': 'Rheumatologist'},
            'back pain,stiffness,reduced mobility': {'disease': 'Ankylosing Spondylitis', 'specialist': 'Rheumatologist'},
            'joint deformity,morning stiffness,fatigue': {'disease': 'Rheumatoid Arthritis', 'specialist': 'Rheumatologist'},
            'muscle weakness,skin rash,difficulty swallowing': {'disease': 'Dermatomyositis', 'specialist': 'Rheumatologist'},
            
            # Gastrointestinal conditions (Gastroenterologist)
            'abdominal pain,nausea,vomiting': {'disease': 'Gastritis', 'specialist': 'Gastroenterologist'},
            'heartburn,chest pain,regurgitation': {'disease': 'GERD', 'specialist': 'Gastroenterologist'},
            'abdominal pain,diarrhea,bloating': {'disease': 'IBS', 'specialist': 'Gastroenterologist'},
            'blood in stool,abdominal pain,weight loss': {'disease': 'Colorectal Cancer', 'specialist': 'Gastroenterologist'},
            'yellowing skin,abdominal pain,dark urine': {'disease': 'Hepatitis', 'specialist': 'Gastroenterologist'},
            'difficulty swallowing,weight loss,coughing': {'disease': 'Esophageal Disease', 'specialist': 'Gastroenterologist'},
            'severe abdominal pain,nausea,fever': {'disease': 'Pancreatitis', 'specialist': 'Gastroenterologist'},
            
            # Dermatological conditions (Dermatologist)
            'skin rash,itching,redness': {'disease': 'Dermatitis', 'specialist': 'Dermatologist'},
            'acne,skin inflammation,scarring': {'disease': 'Acne Vulgaris', 'specialist': 'Dermatologist'},
            'skin patches,scaling,itching': {'disease': 'Psoriasis', 'specialist': 'Dermatologist'},
            'changing moles,skin lesions,irregular borders': {'disease': 'Skin Cancer', 'specialist': 'Dermatologist'},
            'hair loss,scalp problems,itching': {'disease': 'Alopecia', 'specialist': 'Dermatologist'},
            'blisters,skin pain,fever': {'disease': 'Shingles', 'specialist': 'Dermatologist'},
            'excessive sweating,odor,skin irritation': {'disease': 'Hyperhidrosis', 'specialist': 'Dermatologist'},
            
            # Endocrine conditions (Endocrinologist)
            'fatigue,weight gain,cold intolerance': {'disease': 'Hypothyroidism', 'specialist': 'Endocrinologist'},
            'excessive thirst,frequent urination,fatigue': {'disease': 'Diabetes', 'specialist': 'Endocrinologist'},
            'weight loss,anxiety,heat intolerance': {'disease': 'Hyperthyroidism', 'specialist': 'Endocrinologist'},
            'weight gain,purple stretch marks,round face': {'disease': 'Cushings Syndrome', 'specialist': 'Endocrinologist'},
            'excessive growth,joint pain,enlarged hands': {'disease': 'Acromegaly', 'specialist': 'Endocrinologist'},
            'weakness,muscle cramps,irregular heartbeat': {'disease': 'Addisons Disease', 'specialist': 'Endocrinologist'},
            
            # General Physician conditions
            'fever,body ache,fatigue': {'disease': 'Viral Fever', 'specialist': 'General Physician'},
            'runny nose,sore throat,cough': {'disease': 'Common Cold', 'specialist': 'General Physician'},
            'fever,chills,muscle aches': {'disease': 'Flu', 'specialist': 'General Physician'},
            'fatigue,mild fever,sore throat': {'disease': 'Viral Infection', 'specialist': 'General Physician'},
            'stomach pain,diarrhea,mild fever': {'disease': 'Food Poisoning', 'specialist': 'General Physician'},
            'headache,fever,body pain': {'disease': 'Seasonal Infection', 'specialist': 'General Physician'}
        }

    def predict(self, symptoms):
        # Convert symptoms list to sorted string for matching
        symptoms_key = ','.join(sorted([s.strip().lower() for s in symptoms]))
        
        # Find the best matching disease based on symptoms
        best_match = None
        max_matching_symptoms = 0
        
        for disease_symptoms in self.disease_mapping:
            disease_symptom_set = set(disease_symptoms.split(','))
            input_symptom_set = set(symptoms_key.split(','))
            
            matching_symptoms = len(disease_symptom_set.intersection(input_symptom_set))
            
            if matching_symptoms > max_matching_symptoms:
                max_matching_symptoms = matching_symptoms
                best_match = self.disease_mapping[disease_symptoms]
        
        if best_match and max_matching_symptoms >= 1:  # Require at least 2 matching symptoms
            return best_match
        else:
            # If no good match is found, suggest consulting a General Physician
            return {
                'disease': 'Unspecified condition - requires further examination',
                'specialist': 'General Physician'
            } 