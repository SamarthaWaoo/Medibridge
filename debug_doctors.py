from app import app, Doctor, User
with app.app_context():
    doctors = Doctor.query.all()
    print(f"Total Doctors: {len(doctors)}")
    for d in doctors:
        user = User.query.get(d.user_id)
        print(f"Doctor: {user.name}, Specialization: {d.specialization}, City: '{d.city}', Age: {d.min_age}-{d.max_age}")
