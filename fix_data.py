from app import app, db, Doctor
with app.app_context():
    # Update existing doctors to handle all ages for testing
    doctors = Doctor.query.all()
    for d in doctors:
        d.min_age = 0
        d.max_age = 100
        # Clean up city names (strip whitespace)
        if d.city:
            d.city = d.city.strip()
    db.session.commit()
    print("Database updated: All doctors set to age range 0-100 and city names trimmed.")
