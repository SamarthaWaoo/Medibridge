MediBridge – An Intelligent Healthcare Navigation System
MediBridge is a digital healthcare platform designed to streamline interactions between patients, doctors, and administrators. 
The system integrates Machine Learning for symptom-based disease diagnostics and Generative AI for real-time conversational assistance.

Key Features
-> AI Chatbot:-Powered by "Google Gemini AI" for instant healthcare-related Q&A.
-> Disease Prediction:- Built an intelligent prediction engine using "Scikit-Learn" to analyze symptoms.
-> Smart Scheduling:-Weekly availability management for doctors with advanced patient-age filtering rules.
-> Monetization Module:-Tiered subscription plans (Basic, Professional, Premium) with a mock transactional payment system.
-> Admin Control Panel:-Complete system governance, including manual doctor license verification workflows.


Tech Stack
-> Backend: Flask, Flask-SQLAlchemy, Flask-Login, Gunicorn
-> Machine Learning & AI: Scikit-Learn, Pandas, NumPy, Google Generative AI (Gemini SDK)
-> Database: SQLite 3


Project Structure

├── app.py                         # Core Flask application logic
├── improved_disease_predictor.py  # ML prediction engine
├── gemini_chatbot.py              # Google Gemini AI configuration
├── requirements.txt               # Project dependencies
├── ml_model.pkl                  # Trained Machine Learning model
├── templates/                     # UI Frontend layouts (27 views)
└── DOCUMENTATION_FILES/           # Feature & configuration guides
