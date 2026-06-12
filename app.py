from flask import Flask, render_template, request, redirect, url_for, flash, session, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from improved_disease_predictor import ImprovedDiseasePredictor
from gemini_chatbot import GeminiChatbot
import os
from datetime import datetime, timedelta

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your-secret-key'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///healthcare.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

# Initialize the improved disease predictor
disease_predictor = ImprovedDiseasePredictor()

# Initialize Gemini chatbot (will be initialized only if API key is available)
chatbot = None
try:
    chatbot = GeminiChatbot()
except ValueError:
    print("Warning: GEMINI_API_KEY not set. Chatbot feature will be disabled.")

# Database Models
class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(128))
    user_type = db.Column(db.String(20), nullable=False)  # 'patient', 'doctor', or 'admin'
    name = db.Column(db.String(100), nullable=False)
    is_admin = db.Column(db.Boolean, default=False)  # Flag for admin access

class Doctor(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    specialization = db.Column(db.String(100), nullable=False)
    min_age = db.Column(db.Integer, nullable=False, default=0)  # Minimum age for patients
    max_age = db.Column(db.Integer, nullable=False, default=100)  # Maximum age for patients
    # Professional Information
    license_number = db.Column(db.String(100), nullable=True)  # Medical license number
    license_expiry = db.Column(db.Date, nullable=True)  # License expiry date
    qualifications = db.Column(db.Text, nullable=True)  # Comma-separated qualifications
    experience_years = db.Column(db.Integer, nullable=True)  # Years of experience
    hospital_affiliation = db.Column(db.String(200), nullable=True)  # Current hospital/clinic
    city = db.Column(db.String(100), nullable=False, default='Unknown')  # Doctor's city
    contact = db.Column(db.String(15), nullable=True)  #  Doctor phone number
    bio = db.Column(db.Text, nullable=True)  # Professional bio
    is_verified = db.Column(db.Boolean, default=False)  # Admin verification status
    verification_date = db.Column(db.DateTime, nullable=True)  # When admin verified
    appointments = db.relationship('Appointment', backref='doctor', lazy=True)
    user = db.relationship('User', backref='doctor_profile', lazy=True)

class Patient(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    age_category = db.Column(db.String(20), nullable=False, default='Adult')  # 'Child', 'Adult', 'Old Age'
    city = db.Column(db.String(100), nullable=False, default='Unknown')  # Patient's city
    appointments = db.relationship('Appointment', backref='patient', lazy=True)
    user = db.relationship('User', backref='patient_profile', lazy=True)

class Appointment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    patient_id = db.Column(db.Integer, db.ForeignKey('patient.id'), nullable=False)
    doctor_id = db.Column(db.Integer, db.ForeignKey('doctor.id'), nullable=False)
    symptoms = db.Column(db.Text, nullable=False)
    predicted_disease = db.Column(db.String(100), nullable=False)
    status = db.Column(db.String(20), default='pending')  # pending, accepted, completed
    date_created = db.Column(db.DateTime, server_default=db.func.now())
    appointment_date = db.Column(db.Date, nullable=True)  # The scheduled date for the appointment
    time_slot = db.Column(db.String(20), nullable=True)   # The time slot (e.g., "09:00-10:00")
    medical_notes = db.relationship('MedicalNote', backref='appointment', lazy=True, cascade="all, delete-orphan")

class MedicalNote(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    appointment_id = db.Column(db.Integer, db.ForeignKey('appointment.id'), nullable=False)
    doctor_id = db.Column(db.Integer, db.ForeignKey('doctor.id'), nullable=False)
    content = db.Column(db.Text, nullable=False)
    date_created = db.Column(db.DateTime, server_default=db.func.now())
    is_private = db.Column(db.Boolean, default=False)  # Visible only to the doctor who wrote it
    doctor = db.relationship('Doctor', backref='notes', lazy=True)

class Review(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    patient_id = db.Column(db.Integer, db.ForeignKey('patient.id'), nullable=False)
    doctor_id = db.Column(db.Integer, db.ForeignKey('doctor.id'), nullable=False)
    rating = db.Column(db.Integer, nullable=False)  # 1-5 stars
    review_text = db.Column(db.Text, nullable=True)
    date_created = db.Column(db.DateTime, server_default=db.func.now())
    patient = db.relationship('Patient', backref='reviews', lazy=True)
    doctor = db.relationship('Doctor', backref='reviews', lazy=True)

class SubscriptionPlan(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False, unique=True)  # e.g., 'Basic', 'Professional', 'Premium'
    description = db.Column(db.Text, nullable=False)
    price = db.Column(db.Float, nullable=False)  # Price in dollars
    duration_days = db.Column(db.Integer, nullable=False)  # Subscription duration in days
    max_appointments = db.Column(db.Integer, nullable=False)  # Max appointments per month
    features = db.Column(db.Text, nullable=False)  # JSON string of features
    is_active = db.Column(db.Boolean, default=True)
    date_created = db.Column(db.DateTime, server_default=db.func.now())
    subscriptions = db.relationship('DoctorSubscription', backref='plan', lazy=True, cascade="all, delete-orphan")

class DoctorSubscription(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    doctor_id = db.Column(db.Integer, db.ForeignKey('doctor.id'), nullable=False)
    plan_id = db.Column(db.Integer, db.ForeignKey('subscription_plan.id'), nullable=False)
    start_date = db.Column(db.DateTime, server_default=db.func.now())
    end_date = db.Column(db.DateTime, nullable=False)
    status = db.Column(db.String(20), default='active')  # active, expired, cancelled
    appointments_used = db.Column(db.Integer, default=0)
    date_created = db.Column(db.DateTime, server_default=db.func.now())
    doctor = db.relationship('Doctor', backref='subscriptions', lazy=True)
    payments = db.relationship('Payment', backref='subscription', lazy=True, cascade="all, delete-orphan")

class Payment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    doctor_id = db.Column(db.Integer, db.ForeignKey('doctor.id'), nullable=False)
    subscription_id = db.Column(db.Integer, db.ForeignKey('doctor_subscription.id'), nullable=False)
    amount = db.Column(db.Float, nullable=False)
    payment_method = db.Column(db.String(50), nullable=False)  # 'credit_card', 'paypal', 'bank_transfer'
    transaction_id = db.Column(db.String(100), unique=True, nullable=False)
    status = db.Column(db.String(20), default='completed')  # completed, pending, failed
    date_created = db.Column(db.DateTime, server_default=db.func.now())
    doctor = db.relationship('Doctor', backref='payments', lazy=True)

class DoctorSchedule(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    doctor_id = db.Column(db.Integer, db.ForeignKey('doctor.id'), nullable=False)
    day_of_week = db.Column(db.Integer, nullable=False)  # 0=Monday, 1=Tuesday, etc.
    start_time = db.Column(db.Time, nullable=False)
    end_time = db.Column(db.Time, nullable=False)
    slot_duration = db.Column(db.Integer, default=60)  # Duration in minutes
    doctor = db.relationship('Doctor', backref='schedules', lazy=True)
    
    def get_available_slots(self, specific_date=None):
        # Calculate available time slots based on already booked appointments
        if specific_date is None:
            today = datetime.now().date()
            # Find the next occurrence of this day of the week
            days_ahead = self.day_of_week - today.weekday()
            if days_ahead < 0:  # Target day already happened this week
                days_ahead += 7
            specific_date = today + timedelta(days=days_ahead)
            
        # Get all booked appointments for this doctor on this day
        booked_appointments = Appointment.query.filter_by(
            doctor_id=self.doctor_id,
            appointment_date=specific_date
        ).all()
        
        # Get booked time slots
        booked_slots = [app.time_slot for app in booked_appointments if app.time_slot]
        
        # Generate all possible time slots
        all_slots = []
        current_time = self.start_time
        end_time = self.end_time
        
        while current_time < end_time:
            slot_end = (datetime.combine(datetime.today(), current_time) + 
                        timedelta(minutes=self.slot_duration)).time()
            if slot_end > end_time:
                break
                
            slot_str = f"{current_time.strftime('%H:%M')}-{slot_end.strftime('%H:%M')}"
            if slot_str not in booked_slots:
                all_slots.append(slot_str)
                
            current_time = slot_end
            
        return all_slots, specific_date

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# Routes
@app.route('/')
def home():
    return render_template('home.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    user_type = request.args.get('type')
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        name = request.form['name']
        user_type = request.form['user_type']
        city = request.form['city']
        
        if User.query.filter_by(email=email).first():
            flash('Email already exists')
            return redirect(url_for('register'))
        
        # Create a new user with is_admin=False by default
        user = User(
            email=email,
            password_hash=generate_password_hash(password),
            name=name,
            user_type=user_type,
            is_admin=False
        )
        db.session.add(user)
        db.session.commit()
        
        city = request.form.get('city', 'Unknown').strip()
        
        if user_type == 'doctor':
            specialization = request.form['specialization']
            contact = request.form.get('contact')


            # Get selected age groups (checkbox values)
            age_groups = request.form.getlist('age_groups')

            # Convert selected groups into min/max age
            min_age = 0
            max_age = 100

            if 'child' in age_groups:
                min_age = 0
                max_age = max(max_age, 13)

            if 'adult' in age_groups:
                min_age = min(min_age, 13)
                max_age = max(max_age, 65)

            if 'old' in age_groups:
                min_age = min(min_age, 65)
                max_age = 120

            doctor = Doctor(
                user_id=user.id,
                specialization=specialization,
                min_age=min_age,
                max_age=max_age,
                city=city,
                contact=contact
            )

            db.session.add(doctor)
        else:
            age_category = request.form.get('age_category', 'Adult').strip()
            patient = Patient(user_id=user.id, age_category=age_category, city=city)
            db.session.add(patient)
        
        db.session.commit()
        flash('Registration successful')
        return redirect(url_for('login'))
    
    return render_template('register.html', user_type=user_type)

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        user = User.query.filter_by(email=email).first()
        
        if user and check_password_hash(user.password_hash, password):
            login_user(user)
            if user.is_admin:
                return redirect(url_for('admin_dashboard'))
            elif user.user_type == 'doctor':
                return redirect(url_for('doctor_dashboard'))
            else:
                return redirect(url_for('patient_dashboard'))
        
        flash('Invalid email or password')
    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('home'))

@app.route('/patient/dashboard')
@login_required
def patient_dashboard():
    if current_user.user_type != 'patient':
        return redirect(url_for('home'))
    
    # Get or create patient record
    patient = Patient.query.filter_by(user_id=current_user.id).first()
    if not patient:
        # Create patient record if it doesn't exist (for users created before fields were updated)
        patient = Patient(user_id=current_user.id, age_category='Adult', city='Unknown')
        db.session.add(patient)
        db.session.commit()
    
    appointments = patient.appointments
    
    # Get list of common symptoms from the improved disease predictor
    common_symptoms = disease_predictor.get_all_symptoms()
    
    return render_template('patient_dashboard.html', 
                          patient=patient,
                          appointments=appointments,
                          common_symptoms=common_symptoms[:100])  # Limit to 100 symptoms to prevent UI overload

@app.route('/doctor/dashboard')
@login_required
def doctor_dashboard():
    if current_user.user_type != 'doctor':
        return redirect(url_for('home'))
    
    # Get or create doctor record
    doctor = Doctor.query.filter_by(user_id=current_user.id).first()
    if not doctor:
        # Create doctor record if it doesn't exist (for users created before age range fields were added)
        doctor = Doctor(user_id=current_user.id, specialization='General Physician', min_age=0, max_age=100)
        db.session.add(doctor)
        db.session.commit()
    
    appointments = doctor.appointments
    return render_template('doctor_dashboard.html', appointments=appointments, doctor=doctor)

@app.route('/check_symptoms', methods=['POST'])
@login_required
def check_symptoms():
    if current_user.user_type != 'patient':
        return redirect(url_for('home'))
    
    # Get patient profile
    patient = Patient.query.filter_by(user_id=current_user.id).first()
    
    # Get age category and city (from form or profile)
    age_category = request.form.get('age_category', patient.age_category)
    city = request.form.get('city', patient.city)
    
    # Map age category to a representative age for filtering
    category_map = {
        'Child': 5,
        'Adult': 30,
        'Old Age': 75
    }
    age = category_map.get(age_category, 30)
    
    # IMPROVEMENT: Clean the input string to prevent default "Heart Attack" predictions
    symptoms_raw = request.form.get('symptoms', '').strip()
    if not symptoms_raw:
        flash('Please enter symptoms', 'warning')
        return redirect(url_for('patient_dashboard'))
    
    # Convert symptoms string to a clean list (removing empty strings from extra commas)
    symptoms_list = [s.strip() for s in symptoms_raw.split(',') if s.strip()]
    
    if not symptoms_list:
        flash('Please enter valid symptoms', 'warning')
        return redirect(url_for('patient_dashboard'))
    
    # Get prediction using improved ML model
    prediction = disease_predictor.predict(symptoms_list)
    
    # Find all doctors with matching specialization, age range, and city
    from sqlalchemy import func
    doctors_with_ratings = db.session.query(
        Doctor,
        func.avg(Review.rating).label('avg_rating'),
        func.count(Review.id).label('review_count')
    ).outerjoin(Review).filter(
        Doctor.specialization == prediction['specialist'],
        Doctor.is_verified == True,  # Ensures only verified doctors appear
        Doctor.min_age <= age,
        Doctor.max_age >= age,
        func.lower(Doctor.city) == city.strip().lower()
    ).group_by(Doctor.id).order_by(
        func.avg(Review.rating).desc().nullslast()
    ).all()
    
    # Fallback to any city
    if not doctors_with_ratings:
        doctors_with_ratings = db.session.query(
            Doctor,
            func.avg(Review.rating).label('avg_rating'),
            func.count(Review.id).label('review_count')
        ).outerjoin(Review).filter(
            Doctor.specialization == prediction['specialist'],
            Doctor.is_verified == True,
            Doctor.min_age <= age,
            Doctor.max_age >= age
        ).group_by(Doctor.id).order_by(
            func.avg(Review.rating).desc().nullslast()
        ).all()
        
        if doctors_with_ratings:
            flash(f'We found {prediction["specialist"]}s, but none in your city ({city}). Showing doctors from other cities.', 'info')
    
    if not doctors_with_ratings:
        flash(f'We predict you may have {prediction["disease"]} (Confidence: {prediction["confidence"] * 100:.0f}%). However, no {prediction["specialist"]} is currently available for your age group.', 'danger')
        return redirect(url_for('patient_dashboard'))
    
    # Check subscription status
    available_doctors_list = []
    for doctor, avg_rating, review_count in doctors_with_ratings:
        active_subscription = DoctorSubscription.query.filter_by(
            doctor_id=doctor.id,
            status='active'
        ).first()
        
        available_doctors_list.append({
            'doctor_id': doctor.id,
            'name': doctor.user.name,
            'specialization': doctor.specialization,
            'avg_rating': float(avg_rating) if avg_rating else 0,
            'review_count': review_count,
            'has_active_subscription': active_subscription is not None,
            'city': doctor.city
        })
    
    # Clear any old prediction data before setting new data to prevent loops
    session.pop('prediction', None)
    
    # Store prediction in session
    session['prediction'] = {
        'disease': prediction['disease'],
        'specialist': prediction['specialist'],
        'symptoms': symptoms_raw,
        'confidence': prediction['confidence'],
        'patient_age': age,
        'available_doctors': available_doctors_list
    }
    
    # Redirect to the selection page
    return redirect(url_for('book_appointment'))

@app.route('/book_appointment', methods=['GET', 'POST'])
@login_required
def book_appointment():
    if current_user.user_type != 'patient':
        return redirect(url_for('home'))
        
    # Get prediction from session
    prediction = session.get('prediction', {})
    if not prediction:
        flash('Please check your symptoms first', 'warning')
        return redirect(url_for('patient_dashboard'))
    
    # Handle doctor selection via POST
    if request.method == 'POST':
        doctor_id = request.form.get('doctor_id')
        if not doctor_id:
            flash('Please select a doctor', 'warning')
            return redirect(url_for('book_appointment'))
        
        # Update session with selected doctor
        prediction['doctor_id'] = int(doctor_id)
        session['prediction'] = prediction
        # Redirect back to the same route as a GET request to show the calendar
        return redirect(url_for('book_appointment'))
    
    # If no doctor selected yet, show doctor selection page
    if 'doctor_id' not in prediction:
        available_doctors = prediction.get('available_doctors', [])
        return render_template(
            'select_doctor.html',
            prediction=prediction,
            available_doctors=available_doctors
        )
    
    # Get the selected doctor
    doctor = Doctor.query.get_or_404(prediction['doctor_id'])
    
    # Get doctor's schedule for the next 14 days
    doctor_schedules = DoctorSchedule.query.filter_by(doctor_id=doctor.id).all()
    
    available_dates = []
    today = datetime.now().date()
    
    for i in range(14):
        check_date = today + timedelta(days=i)
        day_schedules = [s for s in doctor_schedules if s.day_of_week == check_date.weekday()]
        
        for schedule in day_schedules:
            slots, _ = schedule.get_available_slots(check_date)
            if slots:
                available_dates.append({
                    'date': check_date,
                    'day_name': check_date.strftime('%A'),
                    'formatted_date': check_date.strftime('%Y-%m-%d'),
                    'slots': slots
                })
                break
    
    return render_template('book_appointment.html', 
                          doctor=doctor,
                          prediction=prediction,
                          available_dates=available_dates)

@app.route('/confirm_appointment', methods=['POST'])
@login_required
def confirm_appointment():

    if current_user.user_type != 'patient':
        return redirect(url_for('home'))

    # Get prediction from session
    prediction = session.get('prediction')
    if not prediction:
        flash('Please check your symptoms first')
        return redirect(url_for('patient_dashboard'))

    # Get form data
    appointment_date = request.form.get('appointment_date')
    time_slot = request.form.get('time_slot')

    if not appointment_date or not time_slot:
        flash('Please select both date and time for your appointment')
        return redirect(url_for('book_appointment'))

    try:
        # Parse the date
        parsed_date = datetime.strptime(appointment_date, '%Y-%m-%d').date()

        # Get patient
        patient = Patient.query.filter_by(user_id=current_user.id).first()

        # >>> ADDED: check if slot already exists
        existing = Appointment.query.filter_by(
            doctor_id=prediction['doctor_id'],
            appointment_date=parsed_date,
            time_slot=time_slot
        ).first()

        # >>> ADDED: prevent double booking
        if existing:
            flash('This time slot has already been booked. Please choose another slot.')
            return redirect(url_for('book_appointment'))

        # Create appointment
        appointment = Appointment(
            patient_id=patient.id,
            doctor_id=prediction['doctor_id'],
            symptoms=prediction['symptoms'],
            predicted_disease=prediction['disease'],
            appointment_date=parsed_date,
            time_slot=time_slot
        )

        db.session.add(appointment)
        db.session.commit()

        # Clear the session prediction
        session.pop('prediction', None)

        flash(
            f'Your appointment with Dr. {appointment.doctor.user.name} '
            f'has been scheduled for {parsed_date.strftime("%B %d, %Y")} at {time_slot}.'
        )

        return redirect(url_for('patient_dashboard'))

    except Exception as e:
        flash(f'Error scheduling appointment: {str(e)}')
        return redirect(url_for('book_appointment'))

@app.route('/emergency_support')
@login_required
def emergency_support():
    return render_template("emergency_support.html")

@app.route('/doctor/schedule', methods=['GET', 'POST'])
@login_required
def manage_doctor_schedule():
    if current_user.user_type != 'doctor':
        return redirect(url_for('home'))
    
    doctor = Doctor.query.filter_by(user_id=current_user.id).first()
    
    if request.method == 'POST':
        # Handle schedule creation/update
        day_of_week = int(request.form.get('day_of_week'))
        start_time = request.form.get('start_time')
        end_time = request.form.get('end_time')
        slot_duration = int(request.form.get('slot_duration', 60))
        
        if not start_time or not end_time:
            flash('Please provide both start and end times')
            return redirect(url_for('manage_doctor_schedule'))
            
        try:
            # Parse times
            start_time_obj = datetime.strptime(start_time, '%H:%M').time()
            end_time_obj = datetime.strptime(end_time, '%H:%M').time()
            
            # Check if schedule already exists
            schedule = DoctorSchedule.query.filter_by(
                doctor_id=doctor.id,
                day_of_week=day_of_week
            ).first()
            
            if schedule:
                # Update existing schedule
                schedule.start_time = start_time_obj
                schedule.end_time = end_time_obj
                schedule.slot_duration = slot_duration
            else:
                # Create new schedule
                schedule = DoctorSchedule(
                    doctor_id=doctor.id,
                    day_of_week=day_of_week,
                    start_time=start_time_obj,
                    end_time=end_time_obj,
                    slot_duration=slot_duration
                )
                db.session.add(schedule)
                
            db.session.commit()
            flash('Schedule updated successfully')
            
        except Exception as e:
            flash(f'Error updating schedule: {str(e)}')
    
    # Get current schedules
    schedules = DoctorSchedule.query.filter_by(doctor_id=doctor.id).all()
    day_names = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
    
    return render_template('doctor_schedule.html', 
                          doctor=doctor,
                          schedules=schedules,
                          day_names=day_names)

@app.route('/update_appointment_status/<int:appointment_id>', methods=['POST'])
@login_required
def update_appointment_status(appointment_id):
    if current_user.user_type != 'doctor':
        return redirect(url_for('home'))
    
    appointment = Appointment.query.get_or_404(appointment_id)
    doctor = Doctor.query.filter_by(user_id=current_user.id).first()
    
    if appointment.doctor_id != doctor.id:
        flash('Unauthorized access')
        return redirect(url_for('doctor_dashboard'))
    
    new_status = request.form['status']
    if new_status in ['pending', 'accepted', 'completed']:
        appointment.status = new_status
        db.session.commit()
        flash('Appointment status updated successfully')
    
    return redirect(url_for('doctor_dashboard'))

@app.route('/delete_appointment/<int:appointment_id>', methods=['POST'])
@login_required
def delete_appointment(appointment_id):
    if current_user.user_type != 'patient':
        flash('Only patients can delete appointments')
        return redirect(url_for('home'))
    
    appointment = Appointment.query.get_or_404(appointment_id)
    patient = Patient.query.filter_by(user_id=current_user.id).first()
    
    if appointment.patient_id != patient.id:
        flash('You can only delete your own appointments')
        return redirect(url_for('patient_dashboard'))
    
    db.session.delete(appointment)
    db.session.commit()
    
    flash('Appointment deleted successfully')
    return redirect(url_for('patient_dashboard'))

@app.route('/submit_review/<int:doctor_id>', methods=['POST'])
@login_required
def submit_review(doctor_id):
    if current_user.user_type != 'patient':
        flash('Only patients can submit reviews')
        return redirect(url_for('home'))
    
    patient = Patient.query.filter_by(user_id=current_user.id).first()
    doctor = Doctor.query.get_or_404(doctor_id)
    
    rating = request.form.get('rating', 0)
    review_text = request.form.get('review_text', '').strip()
    
    try:
        rating = int(rating)
        if rating < 1 or rating > 5:
            flash('Rating must be between 1 and 5 stars')
            return redirect(url_for('patient_dashboard'))
    except ValueError:
        flash('Invalid rating')
        return redirect(url_for('patient_dashboard'))
    
    # Check if patient already reviewed this doctor
    existing_review = Review.query.filter_by(patient_id=patient.id, doctor_id=doctor_id).first()
    if existing_review:
        # Update existing review
        existing_review.rating = rating
        existing_review.review_text = review_text
        existing_review.date_created = db.func.now()
    else:
        # Create new review
        review = Review(patient_id=patient.id, doctor_id=doctor_id, rating=rating, review_text=review_text)
        db.session.add(review)
    
    db.session.commit()
    flash('Review submitted successfully!')
    return redirect(url_for('patient_dashboard'))

@app.route('/top_doctors')
def top_doctors():
    # Get all doctors with their average ratings
    from sqlalchemy import func
    
    doctors_with_ratings = db.session.query(
        Doctor,
        func.avg(Review.rating).label('avg_rating'),
        func.count(Review.id).label('review_count')
    ).outerjoin(Review).group_by(Doctor.id).order_by(
        func.avg(Review.rating).desc().nullslast()
    ).all()
    
    return render_template('top_doctors.html', doctors_with_ratings=doctors_with_ratings)

# Doctor Profile Routes
@app.route('/doctor/profile')
@login_required
def doctor_profile():
    if current_user.user_type != 'doctor':
        flash('Only doctors can access this page')
        return redirect(url_for('home'))
    
    doctor = Doctor.query.filter_by(user_id=current_user.id).first()
    if not doctor:
        flash('Doctor profile not found')
        return redirect(url_for('home'))
    
    return render_template('doctor_profile.html', doctor=doctor, now=datetime.now().date())

@app.route('/doctor/profile/edit', methods=['GET', 'POST'])
@login_required
def edit_doctor_profile():
    if current_user.user_type != 'doctor':
        flash('Only doctors can access this page')
        return redirect(url_for('home'))
    
    doctor = Doctor.query.filter_by(user_id=current_user.id).first()
    if not doctor:
        flash('Doctor profile not found')
        return redirect(url_for('home'))
    
    if request.method == 'POST':
        # --- NEW LOGIC FOR TOGGLE ---
        # If 'allow_calls' exists in request.form, it means it was checked.
        # If it doesn't exist, it means it was unchecked.
        allow_calls_val = request.form.get('allow_calls')
        if allow_calls_val is not None:
            doctor.allow_calls = (allow_calls_val == 'on')
        
        # Existing information updates
        doctor.license_number = request.form.get('license_number', '').strip()
        doctor.license_expiry = request.form.get('license_expiry')
        doctor.qualifications = request.form.get('qualifications', '').strip()
        doctor.experience_years = request.form.get('experience_years')
        doctor.hospital_affiliation = request.form.get('hospital_affiliation', '').strip()
        doctor.city = request.form.get('city', doctor.city).strip()
        doctor.contact = request.form.get('contact', doctor.contact).strip() if request.form.get('contact') else doctor.contact
        doctor.bio = request.form.get('bio', '').strip()
        
        # Convert experience_years to int if provided
        if doctor.experience_years:
            try:
                doctor.experience_years = int(doctor.experience_years)
            except ValueError:
                flash('Experience years must be a number')
                return render_template('edit_doctor_profile.html', doctor=doctor)
        
        # Convert license_expiry to date if provided
        if doctor.license_expiry:
            try:
                from datetime import datetime
                doctor.license_expiry = datetime.strptime(doctor.license_expiry, '%Y-%m-%d').date()
            except ValueError:
                flash('Invalid date format for license expiry')
                return render_template('edit_doctor_profile.html', doctor=doctor)
        
        db.session.commit()
        flash('Profile updated successfully')
        return redirect(url_for('doctor_profile'))
    
    return render_template('edit_doctor_profile.html', doctor=doctor)

# Subscription routes
@app.route('/doctor/subscriptions')
@login_required
def doctor_subscriptions():
    if current_user.user_type != 'doctor':
        return redirect(url_for('home'))
    
    doctor = Doctor.query.filter_by(user_id=current_user.id).first()
    if not doctor:
        flash('Doctor profile not found')
        return redirect(url_for('home'))
    if not doctor.is_verified:
        flash('Your profile is under review. You can subscribe after approval.', 'warning')
    # Get active subscription
    active_subscription = DoctorSubscription.query.filter_by(
        doctor_id=doctor.id,
        status='active'
    ).first()
    
    # Get all subscriptions
    all_subscriptions = DoctorSubscription.query.filter_by(doctor_id=doctor.id).all()
    
    # Get available plans
    available_plans = SubscriptionPlan.query.filter_by(is_active=True).all()
    
    return render_template('doctor_subscriptions.html',
                          doctor=doctor,
                          active_subscription=active_subscription,
                          all_subscriptions=all_subscriptions,
                          available_plans=available_plans)

@app.route('/doctor/subscribe/<int:plan_id>', methods=['POST'])
@login_required
def subscribe_to_plan(plan_id):
    if current_user.user_type != 'doctor':
        return redirect(url_for('home'))
    
    doctor = Doctor.query.filter_by(user_id=current_user.id).first()
    if not doctor.is_verified:
        flash('Verification required before making a payment.', 'danger')
        return redirect(url_for('doctor_subscriptions'))
    plan = SubscriptionPlan.query.get_or_404(plan_id)
    
    if not plan.is_active:
        flash('This plan is no longer available')
        return redirect(url_for('doctor_subscriptions'))
    
    # Check if doctor already has an active subscription
    active_sub = DoctorSubscription.query.filter_by(
        doctor_id=doctor.id,
        status='active'
    ).first()
    
    if active_sub:
        flash('You already have an active subscription. Please cancel it first.')
        return redirect(url_for('doctor_subscriptions'))
    
    # Redirect to payment page
    return redirect(url_for('process_payment', plan_id=plan_id))

@app.route('/doctor/payment/<int:plan_id>', methods=['GET', 'POST'])
@login_required
def process_payment(plan_id):
    if current_user.user_type != 'doctor':
        return redirect(url_for('home'))
    
    doctor = Doctor.query.filter_by(user_id=current_user.id).first()
    if not doctor.is_verified:
        flash('Your account is pending admin verification. Subscription is not available yet.', 'danger')
        return redirect(url_for('doctor_subscriptions'))
    plan = SubscriptionPlan.query.get_or_404(plan_id)
    
    if request.method == 'POST':
        payment_method = request.form.get('payment_method')
        card_number = request.form.get('card_number', '')
        
        if not payment_method:
            flash('Please select a payment method')
            return redirect(url_for('process_payment', plan_id=plan_id))
        
        try:
            # Generate dummy transaction ID
            import uuid
            transaction_id = f"TXN-{uuid.uuid4().hex[:12].upper()}"
            
            # Create subscription (starts as 'pending_payment')
            end_date = datetime.now() + timedelta(days=plan.duration_days)
            subscription = DoctorSubscription(
                doctor_id=doctor.id,
                plan_id=plan.id,
                end_date=end_date,
                status='pending_payment'
            )
            db.session.add(subscription)
            db.session.flush()
            
            # Create payment record (starts as 'pending')
            payment = Payment(
                doctor_id=doctor.id,
                subscription_id=subscription.id,
                amount=plan.price,
                payment_method=payment_method,
                transaction_id=transaction_id,
                status='pending'
            )
            db.session.add(payment)
            db.session.commit()
            
            flash(f'Payment submitted! Transaction ID: {transaction_id}. Please wait for admin verification to activate your subscription.')
            return redirect(url_for('doctor_subscriptions'))
            
        except Exception as e:
            db.session.rollback()
            flash(f'Error processing payment: {str(e)}')
            return redirect(url_for('process_payment', plan_id=plan_id))
    
    return render_template('payment_page.html', plan=plan, doctor=doctor)

@app.route('/doctor/cancel_subscription/<int:subscription_id>', methods=['POST'])
@login_required
def cancel_subscription(subscription_id):
    if current_user.user_type != 'doctor':
        return redirect(url_for('home'))
    
    doctor = Doctor.query.filter_by(user_id=current_user.id).first()
    subscription = DoctorSubscription.query.get_or_404(subscription_id)
    
    if subscription.doctor_id != doctor.id:
        flash('Unauthorized access')
        return redirect(url_for('doctor_subscriptions'))
    
    subscription.status = 'cancelled'
    db.session.commit()
    
    flash('Subscription cancelled successfully')
    return redirect(url_for('doctor_subscriptions'))

# Admin routes
@app.route('/admin/dashboard')
@login_required
def admin_dashboard():
    if not current_user.is_admin:
        flash('Access denied. Admin privileges required.')
        return redirect(url_for('home'))
    
    # Get all users, grouped by type
    doctors = Doctor.query.all()
    patients = Patient.query.all()
    
    # Get all appointments
    appointments = Appointment.query.all()
    
    return render_template('admin_dashboard.html', 
                          doctors=doctors,
                          patients=patients,
                          appointments=appointments)

@app.route('/admin/create', methods=['GET', 'POST'])
@login_required
def create_admin():
    if not current_user.is_admin:
        flash('Access denied. Admin privileges required.')
        return redirect(url_for('home'))
    
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        name = request.form['name']
        
        if User.query.filter_by(email=email).first():
            flash('Email already exists')
            return redirect(url_for('create_admin'))
        
        # Create a new admin user
        admin = User(
            email=email,
            password_hash=generate_password_hash(password),
            name=name,
            user_type='admin',
            is_admin=True
        )
        db.session.add(admin)
        db.session.commit()
        
        flash('Admin account created successfully')
        return redirect(url_for('admin_dashboard'))
    
    return render_template('create_admin.html')

@app.route('/admin/toggle_user_status/<int:user_id>', methods=['POST'])
@login_required
def toggle_user_status(user_id):
    if not current_user.is_admin:
        flash('Access denied. Admin privileges required.')
        return redirect(url_for('home'))
    
    user = User.query.get_or_404(user_id)
    
    # Toggle admin status (but prevent removing your own admin status)
    if user.id != current_user.id:
        user.is_admin = not user.is_admin
        db.session.commit()
        flash(f'User {user.name} admin status updated successfully')
    else:
        flash('You cannot change your own admin status')
    
    return redirect(url_for('admin_dashboard'))

@app.route('/admin/delete_user/<int:user_id>', methods=['POST'])
@login_required
def delete_user(user_id):
    if not current_user.is_admin:
        flash('Access denied. Admin privileges required.')
        return redirect(url_for('home'))
    
    user = User.query.get_or_404(user_id)
    
    # Prevent deleting yourself
    if user.id == current_user.id:
        flash('You cannot delete your own account')
        return redirect(url_for('admin_dashboard'))
    
    if user.user_type == 'doctor':
        doctor = Doctor.query.filter_by(user_id=user.id).first()
        if doctor:
            # Delete the doctor's schedules first
            schedules = DoctorSchedule.query.filter_by(doctor_id=doctor.id).all()
            for schedule in schedules:
                db.session.delete(schedule)
            # Delete the doctor's subscriptions and their payments
            subscriptions = DoctorSubscription.query.filter_by(doctor_id=doctor.id).all()
            for subscription in subscriptions:
                payments = Payment.query.filter_by(subscription_id=subscription.id).all()
                for payment in payments:
                    db.session.delete(payment)
                db.session.delete(subscription)
            # Delete the doctor's appointments
            appointments = Appointment.query.filter_by(doctor_id=doctor.id).all()
            for appointment in appointments:
                db.session.delete(appointment)
            db.session.delete(doctor)
    
    elif user.user_type == 'patient':
        patient = Patient.query.filter_by(user_id=user.id).first()
        if patient:
            # Delete the patient's appointments first
            appointments = Appointment.query.filter_by(patient_id=patient.id).all()
            for appointment in appointments:
                db.session.delete(appointment)
            db.session.delete(patient)
    
    db.session.delete(user)
    db.session.commit()
    
    flash(f'User {user.name} has been deleted')
    return redirect(url_for('admin_dashboard'))

# Admin Subscription Management Routes
@app.route('/admin/subscriptions')
@login_required
def admin_subscriptions():
    if not current_user.is_admin:
        flash('Access denied. Admin privileges required.')
        return redirect(url_for('home'))
    
    # Get all subscription plans
    plans = SubscriptionPlan.query.all()
    
    # Get all doctor subscriptions
    doctor_subscriptions = DoctorSubscription.query.all()
    
    # Get all payments
    payments = Payment.query.all()
    
    return render_template('admin_subscriptions.html',
                          plans=plans,
                          doctor_subscriptions=doctor_subscriptions,
                          payments=payments)

@app.route('/admin/create_plan', methods=['GET', 'POST'])
@login_required
def create_subscription_plan():
    if not current_user.is_admin:
        flash('Access denied. Admin privileges required.')
        return redirect(url_for('home'))
    
    if request.method == 'POST':
        name = request.form.get('name')
        description = request.form.get('description')
        price = request.form.get('price')
        duration_days = request.form.get('duration_days')
        max_appointments = request.form.get('max_appointments')
        features = request.form.get('features')
        
        try:
            plan = SubscriptionPlan(
                name=name,
                description=description,
                price=float(price),
                duration_days=int(duration_days),
                max_appointments=int(max_appointments),
                features=features
            )
            db.session.add(plan)
            db.session.commit()
            
            flash(f'Subscription plan "{name}" created successfully')
            return redirect(url_for('admin_subscriptions'))
        except Exception as e:
            db.session.rollback()
            flash(f'Error creating plan: {str(e)}')
    
    return render_template('create_subscription_plan.html')

@app.route('/admin/edit_plan/<int:plan_id>', methods=['GET', 'POST'])
@login_required
def edit_subscription_plan(plan_id):
    if not current_user.is_admin:
        flash('Access denied. Admin privileges required.')
        return redirect(url_for('home'))
    
    plan = SubscriptionPlan.query.get_or_404(plan_id)
    
    if request.method == 'POST':
        plan.name = request.form.get('name')
        plan.description = request.form.get('description')
        plan.price = float(request.form.get('price'))
        plan.duration_days = int(request.form.get('duration_days'))
        plan.max_appointments = int(request.form.get('max_appointments'))
        plan.features = request.form.get('features')
        plan.is_active = 'is_active' in request.form
        
        try:
            db.session.commit()
            flash('Subscription plan updated successfully')
            return redirect(url_for('admin_subscriptions'))
        except Exception as e:
            db.session.rollback()
            flash(f'Error updating plan: {str(e)}')
    
    return render_template('edit_subscription_plan.html', plan=plan)

@app.route('/admin/delete_plan/<int:plan_id>', methods=['POST'])
@login_required
def delete_subscription_plan(plan_id):
    if not current_user.is_admin:
        flash('Access denied. Admin privileges required.')
        return redirect(url_for('home'))
    
    plan = SubscriptionPlan.query.get_or_404(plan_id)
    
    try:
        db.session.delete(plan)
        db.session.commit()
        flash(f'Subscription plan "{plan.name}" deleted successfully')
    except Exception as e:
        db.session.rollback()
        flash(f'Error deleting plan: {str(e)}')
    
    return redirect(url_for('admin_subscriptions'))

@app.route('/admin/verify_payment/<int:payment_id>/<string:action>', methods=['POST'])
@login_required
def admin_verify_payment(payment_id, action):
    if not current_user.is_admin:
        flash('Access denied. Admin privileges required.')
        return redirect(url_for('home'))
        
    payment = Payment.query.get_or_404(payment_id)
    subscription = DoctorSubscription.query.get(payment.subscription_id)
    
    if action == 'approve':
        payment.status = 'completed'
        if subscription:
            subscription.status = 'active'
            subscription.start_date = datetime.now()
            subscription.end_date = datetime.now() + timedelta(days=subscription.plan.duration_days)
        db.session.commit()
        flash('Payment approved and subscription activated')
    elif action == 'reject':
        payment.status = 'failed'
        if subscription:
            subscription.status = 'cancelled'
        db.session.commit()
        flash('Payment rejected')
        
    return redirect(url_for('admin_subscriptions'))

# Create first admin user command
@app.cli.command("create-admin")
def create_first_admin():
    """Create the first admin user."""
    admin_email = "admin@healthcare.com"
    admin_password = "admin123"
    admin_name = "System Administrator"
    
    if User.query.filter_by(email=admin_email).first():
        print("Admin user already exists")
        return
    
    admin = User(
        email=admin_email,
        password_hash=generate_password_hash(admin_password),
        name=admin_name,
        user_type='admin',
        is_admin=True
    )
    db.session.add(admin)
    db.session.commit()
    
    print(f"Admin user created. Email: {admin_email}, Password: {admin_password}")

# Admin Patient Management Routes
@app.route('/admin/doctors')
@login_required
def admin_view_doctors():
    if not current_user.is_admin:
        flash('Access denied. Admin privileges required.')
        return redirect(url_for('home'))
    
    # Get all doctors with their patient counts
    doctors = Doctor.query.all()
    
    return render_template('admin_doctors.html', doctors=doctors)

@app.route('/admin/doctor/<int:doctor_id>/verify')
@login_required
def admin_verify_doctor(doctor_id):
    if not current_user.is_admin:
        flash('Access denied. Admin privileges required.')
        return redirect(url_for('home'))
    
    doctor = Doctor.query.get_or_404(doctor_id)
    
    return render_template('admin_verify_doctor.html', doctor=doctor, now=datetime.now().date())

@app.route('/admin/doctor/<int:doctor_id>/verify/approve', methods=['POST'])
@login_required
def admin_approve_doctor(doctor_id):
    if not current_user.is_admin:
        flash('Access denied. Admin privileges required.')
        return redirect(url_for('home'))
    
    doctor = Doctor.query.get_or_404(doctor_id)
    doctor.is_verified = True
    doctor.verification_date = datetime.now()
    db.session.commit()
    
    flash(f'Doctor {doctor.user.name} has been verified successfully')
    return redirect(url_for('admin_view_doctors'))

@app.route('/admin/doctor/<int:doctor_id>/verify/reject', methods=['POST'])
@login_required
def admin_reject_doctor(doctor_id):
    if not current_user.is_admin:
        flash('Access denied. Admin privileges required.')
        return redirect(url_for('home'))
    
    doctor = Doctor.query.get_or_404(doctor_id)
    doctor.is_verified = False
    doctor.verification_date = None
    db.session.commit()
    
    flash(f'Doctor {doctor.user.name} verification has been rejected')
    return redirect(url_for('admin_view_doctors'))

@app.route('/admin/doctor/<int:doctor_id>/patients')
@login_required
def admin_view_doctor_patients(doctor_id):
    if not current_user.is_admin:
        flash('Access denied. Admin privileges required.')
        return redirect(url_for('home'))
    
    # Get the doctor
    doctor = Doctor.query.get_or_404(doctor_id)
    
    # Get all appointments for this doctor
    appointments = Appointment.query.filter_by(doctor_id=doctor_id).all()
    
    # Get unique patients for this doctor
    patient_ids = set(appointment.patient_id for appointment in appointments)
    patients = Patient.query.filter(Patient.id.in_(patient_ids)).all() if patient_ids else []
    
    return render_template('admin_doctor_patients.html', 
                          doctor=doctor,
                          patients=patients,
                          appointments=appointments)

@app.route('/admin/patient/<int:patient_id>/details')
@login_required
def admin_view_patient_details(patient_id):
    if not current_user.is_admin:
        flash('Access denied. Admin privileges required.')
        return redirect(url_for('home'))
    
    # Get the patient
    patient = Patient.query.get_or_404(patient_id)
    
    # Get all appointments for this patient
    appointments = Appointment.query.filter_by(patient_id=patient_id).order_by(Appointment.date_created.desc()).all()
    
    # Get all medical notes for this patient's appointments
    all_notes = {}
    for appointment in appointments:
        notes = MedicalNote.query.filter_by(appointment_id=appointment.id).all()
        if notes:
            all_notes[appointment.id] = notes
    
    return render_template('admin_patient_details.html',
                          patient=patient,
                          appointments=appointments,
                          all_notes=all_notes)

@app.cli.command("setup-database")
def setup_database():
    """Set up the database with initial data."""
    try:
        db.create_all()
        
        # Only add demo data if there are no users yet
        if User.query.count() == 0:
            print("Creating sample data...")
            
            # Create admin user
            admin = User(email="admin@example.com", 
                       name="Admin User", 
                       user_type="admin",
                       is_admin=True)
            admin.password_hash = generate_password_hash("admin12345")
            db.session.add(admin)
            
            # Create sample doctors
            doctor_data = [
                {"email": "cardio@example.com", "name": "John Smith", "specialization": "Cardiologist"},
                {"email": "neuro@example.com", "name": "Sarah Johnson", "specialization": "Neurologist"},
                {"email": "derma@example.com", "name": "David Williams", "specialization": "Dermatologist"},
                {"email": "gastro@example.com", "name": "Emily Brown", "specialization": "Gastroenterologist"},
                {"email": "gp@example.com", "name": "Michael Davis", "specialization": "General Physician"}
            ]
            
            for data in doctor_data:
                doctor_user = User(email=data["email"], name=data["name"], user_type="doctor")
                doctor_user.password_hash = generate_password_hash("doc123")
                db.session.add(doctor_user)
                db.session.flush()  # To get the user ID
                
                doctor = Doctor(user_id=doctor_user.id, specialization=data["specialization"])
                db.session.add(doctor)
                
                # Create sample schedule for each doctor
                for day in range(5):  # Monday to Friday
                    schedule = DoctorSchedule(
                        doctor_id=doctor.id,
                        day_of_week=day,
                        start_time=datetime.strptime("09:00", "%H:%M").time(),
                        end_time=datetime.strptime("17:00", "%H:%M").time(),
                        slot_duration=60
                    )
                    db.session.add(schedule)
            
            # Create sample patients
            patient_user = User(email="patient@example.com", name="Alex Johnson", user_type="patient")
            patient_user.password_hash = generate_password_hash("pt1234")
            db.session.add(patient_user)
            db.session.flush()
            
            patient = Patient(user_id=patient_user.id)
            db.session.add(patient)
            
            # Create sample subscription plans (in Indian Rupees)
            plans_data = [
                {
                    "name": "Basic",
                    "description": "Perfect for getting started",
                    "price": 2499,
                    "duration_days": 30,
                    "max_appointments": 50,
                    "features": "Basic analytics, Up to 50 appointments/month, Email support"
                },
                {
                    "name": "Professional",
                    "description": "For growing practices",
                    "price": 6999,
                    "duration_days": 30,
                    "max_appointments": 200,
                    "features": "Advanced analytics, Up to 200 appointments/month, Priority support, Patient messaging"
                },
                {
                    "name": "Premium",
                    "description": "For established practices",
                    "price": 12999,
                    "duration_days": 30,
                    "max_appointments": 500,
                    "features": "Full analytics, Unlimited appointments, 24/7 support, API access, Custom branding"
                }
            ]
            
            for plan_data in plans_data:
                plan = SubscriptionPlan(**plan_data)
                db.session.add(plan)
            
            db.session.commit()
            print("Sample data created successfully!")
        else:
            print("Database already has data. No sample data was created.")
            
    except Exception as e:
        print(f"Error setting up database: {e}")
        db.session.rollback()

@app.route('/doctor/view_patient/<int:patient_id>')
@login_required
def view_patient_history(patient_id):
    if current_user.user_type != 'doctor':
        flash('Only doctors can access patient history')
        return redirect(url_for('home'))
    
    # Get the doctor and patient
    doctor = Doctor.query.filter_by(user_id=current_user.id).first()
    patient = Patient.query.get_or_404(patient_id)
    
    # Get all appointments for this patient, with any doctor
    all_appointments = Appointment.query.filter_by(patient_id=patient.id).order_by(Appointment.date_created.desc()).all()
    
    # Check if the doctor has any appointments with this patient (for verification)
    doctor_appointments = [a for a in all_appointments if a.doctor_id == doctor.id]
    
    # If this doctor has never seen this patient, show a warning
    if not doctor_appointments:
        flash('Note: You have not personally treated this patient before.', 'warning')
    
    # Get all medical notes
    all_notes = {}
    for appointment in all_appointments:
        notes = MedicalNote.query.filter_by(appointment_id=appointment.id).all()
        # Filter notes: include all public notes and private notes that belong to the current doctor
        visible_notes = [n for n in notes if not n.is_private or n.doctor_id == doctor.id]
        if visible_notes:
            all_notes[appointment.id] = visible_notes
    
    return render_template('patient_history.html', 
                          patient=patient,
                          all_appointments=all_appointments,
                          doctor_appointments=doctor_appointments,
                          current_doctor_id=doctor.id,
                          all_notes=all_notes)

@app.route('/doctor/add_note/<int:appointment_id>', methods=['POST'])
@login_required
def add_medical_note(appointment_id):
    if current_user.user_type != 'doctor':
        flash('Only doctors can add medical notes')
        return redirect(url_for('home'))
    
    # Get the doctor and appointment
    doctor = Doctor.query.filter_by(user_id=current_user.id).first()
    appointment = Appointment.query.get_or_404(appointment_id)
    
    # Get form data
    note_content = request.form.get('note_content')
    is_private = 'is_private' in request.form
    
    if not note_content:
        flash('Note content cannot be empty')
        return redirect(url_for('view_patient_history', patient_id=appointment.patient_id))
    
    # Create new medical note
    note = MedicalNote(
        appointment_id=appointment.id,
        doctor_id=doctor.id,
        content=note_content,
        is_private=is_private
    )
    
    db.session.add(note)
    db.session.commit()
    
    flash('Medical note added successfully')
    return redirect(url_for('view_patient_history', patient_id=appointment.patient_id))

@app.route('/doctor/delete_note/<int:note_id>', methods=['POST'])
@login_required
def delete_medical_note(note_id):
    if current_user.user_type != 'doctor':
        flash('Only doctors can delete medical notes')
        return redirect(url_for('home'))
    
    # Get the doctor and note
    doctor = Doctor.query.filter_by(user_id=current_user.id).first()
    note = MedicalNote.query.get_or_404(note_id)
    
    # Check if the doctor owns the note
    if note.doctor_id != doctor.id:
        flash('You can only delete your own notes')
        return redirect(url_for('doctor_dashboard'))
    
    # Get patient ID for redirection
    patient_id = note.appointment.patient_id
    
    db.session.delete(note)
    db.session.commit()
    
    flash('Medical note deleted successfully')
    return redirect(url_for('view_patient_history', patient_id=patient_id))

@app.route('/patient/my_history')
@login_required
def patient_my_history():
    if current_user.user_type != 'patient':
        flash('Only patients can access their history')
        return redirect(url_for('home'))
    
    # Get the patient
    patient = Patient.query.filter_by(user_id=current_user.id).first()
    if not patient:
        flash('Patient profile not found')
        return redirect(url_for('home'))
    
    # Get all appointments for this patient
    all_appointments = Appointment.query.filter_by(patient_id=patient.id).order_by(Appointment.date_created.desc()).all()
    
    # Get all medical notes for this patient's appointments
    all_notes = {}
    for appointment in all_appointments:
        notes = MedicalNote.query.filter_by(appointment_id=appointment.id).all()
        # Patients can see all public notes and their own appointment notes
        visible_notes = [n for n in notes if not n.is_private]
        if visible_notes:
            all_notes[appointment.id] = visible_notes
    
    return render_template('patient_my_history.html', 
                          patient=patient,
                          all_appointments=all_appointments,
                          all_notes=all_notes)

@app.route('/admin/model_metrics')
@login_required
def model_metrics():
    if not current_user.is_admin:
        flash('Access denied. Admin privileges required.')
        return redirect(url_for('home'))
    
    # Get model metrics and visualizations
    confusion_matrix = disease_predictor.get_confusion_matrix()
    roc_curve = disease_predictor.get_roc_curve()
    feature_importance = disease_predictor.get_feature_importance()
    classification_report = disease_predictor.get_classification_report_viz()
    
    return render_template('model_metrics.html',
                          confusion_matrix=confusion_matrix,
                          roc_curve=roc_curve,
                          feature_importance=feature_importance,
                          classification_report=classification_report)

# Chatbot Routes
@app.route('/patient/chatbot')
@login_required
def chatbot_page():
    if current_user.user_type != 'patient':
        flash('Only patients can access the chatbot')
        return redirect(url_for('home'))
    
    if not chatbot:
        flash('Chatbot feature is not available. Please contact administrator.')
        return redirect(url_for('patient_dashboard'))
    
    return render_template('chatbot.html')

@app.route('/api/chatbot/message', methods=['POST'])
@login_required
def chatbot_message():
    if current_user.user_type != 'patient':
        return jsonify({'success': False, 'error': 'Unauthorized'}), 403
    
    if not chatbot:
        return jsonify({'success': False, 'error': 'Chatbot not available'}), 503
    
    try:
        data = request.get_json()
        user_message = data.get('message', '').strip()
        
        if not user_message:
            return jsonify({'success': False, 'error': 'Message cannot be empty'}), 400
        
        # Get response from Gemini
        response = chatbot.chat(user_message)
        
        if response['success']:
            return jsonify({
                'success': True,
                'response': response['response']
            })
        else:
            return jsonify({
                'success': False,
                'error': response['error']
            }), 500
    
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/chatbot/remedy', methods=['POST'])
@login_required
def chatbot_remedy():
    if current_user.user_type != 'patient':
        return jsonify({'success': False, 'error': 'Unauthorized'}), 403
    
    if not chatbot:
        return jsonify({'success': False, 'error': 'Chatbot not available'}), 503
    
    try:
        data = request.get_json()
        symptoms = data.get('symptoms', '').strip()
        
        if not symptoms:
            return jsonify({'success': False, 'error': 'Symptoms cannot be empty'}), 400
        
        # Get home remedy advice from Gemini
        response = chatbot.get_home_remedy_advice(symptoms)
        
        if response['success']:
            return jsonify({
                'success': True,
                'response': response['response']
            })
        else:
            return jsonify({
                'success': False,
                'error': response['error']
            }), 500
    
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500
@app.route("/doctor/<int:doctor_id>/reviews")
@login_required
def doctor_reviews(doctor_id):

    doctor = Doctor.query.get_or_404(doctor_id)

    reviews = Review.query.filter_by(doctor_id=doctor_id)\
        .order_by(Review.date_created.desc()).all()

    avg_rating = db.session.query(db.func.avg(Review.rating))\
        .filter(Review.doctor_id == doctor_id).scalar()

    return render_template(
        "doctor_reviews.html",
        doctor=doctor,
        reviews=reviews,
        avg_rating=round(avg_rating,1) if avg_rating else None
    )
@app.route("/doctors")
@login_required
def view_doctors():

    doctors = Doctor.query.all()

    doctor_data = []

    for doctor in doctors:
        reviews = Review.query.filter_by(doctor_id=doctor.id).all()

        if reviews:
            avg_rating = round(sum(r.rating for r in reviews) / len(reviews), 1)
        else:
            avg_rating = None

        doctor_data.append({
            "doctor": doctor,
            "avg_rating": avg_rating,
            "review_count": len(reviews)
        })

    return render_template(
        "doctors_list.html",
        doctor_data=doctor_data
    )
if __name__ == '__main__':
    with app.app_context():
        # Don't drop the database on every startup!
        # Only create tables if they don't exist
        db.create_all()
        
        # Check if admin exists, create if not
        admin = User.query.filter_by(email="admin@12345.com").first()
        if not admin:
            admin = User(
                email="admin@healthcare.com",
                password_hash=generate_password_hash("admin12345"),
                name="System Administrator",
                user_type='admin',
                is_admin=True
            )
            db.session.add(admin)
            db.session.commit()
            print("Default admin created: admin@12345.com / admin12345")
            
    # Start the application
    app.run(debug=True, host='0.0.0.0', port=5000) 
