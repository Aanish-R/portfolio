from app import app, db, User, generate_password_hash

with app.app_context():
    # Check if demo user exists
    user = User.query.filter_by(email='demo.user@example.com').first()
    if user:
        print(f"User found: {user.email}")
        # Update password just in case
        user.password = generate_password_hash('demo_password_abc123')
        db.session.commit()
        print("Password updated for demo.user@example.com")
    else:
        print("Demo user not found. Creating...")
        new_user = User(
            email='demo.user@example.com',
            name='Demo User',
            password=generate_password_hash('demo_password_abc123')
        )
        db.session.add(new_user)
        db.session.commit()
        print("Demo user created with password: demo_password_abc123")
