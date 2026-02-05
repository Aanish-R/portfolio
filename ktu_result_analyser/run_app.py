from flaskwebgui import FlaskUI
from app import app, db
import os

def start_app():
    # Initialize database and folders
    with app.app_context():
        db.create_all()
    
    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

    # Configure the UI
    # This will automatically start Flask and open a browser window in app mode
    # It supports Chrome, Edge, etc.
    ui = FlaskUI(
        app=app,
        server="flask",
        width=1200,
        height=800,
        port=5000
    )

    ui.run()

if __name__ == "__main__":
    start_app()
