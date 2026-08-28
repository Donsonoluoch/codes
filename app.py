# app.py
import os
import logging
import dotenv # Import dotenv
from pathlib import Path

# --- Load .env variables FIRST ---
dotenv.load_dotenv() # Load environment variables as early as possible

from flask import Flask
from extensions import db, login_manager, migrate
from config import Config # Import your Config class

def create_app():
    
    # 1. Tell Flask about the instance/ folder
    app = Flask(__name__, instance_relative_config=True)
    os.makedirs(app.instance_path, exist_ok=True)

    # 2. Compute absolute path for the SQLite file
    BASE_DIR = Path(__file__).resolve().parent
    INSTANCE_DIR = BASE_DIR / 'instance'
    DB_PATH = INSTANCE_DIR / 'data.db'
    INSTANCE_DIR.mkdir(parents=True, exist_ok=True)  # safe to re-run

    base_dir = os.path.abspath(os.path.dirname(__file__))
    uploads_dir = os.path.join(base_dir, 'uploads')
    os.makedirs(uploads_dir, exist_ok=True) # Ensure the folder exists

    # 3. Core configuration
    app.config.from_object(Config) # Load all configurations from the Config class

    # Set paths that depend on BASE_DIR after Config is loaded
    app.config['SQLALCHEMY_DATABASE_URI'] = f"sqlite:///{DB_PATH}"
    app.config['UPLOAD_FOLDER'] = uploads_dir

    # 4. Initialize extensions
    db.init_app(app)
    migrate.init_app(app, db)

    login_manager.init_app(app)
    login_manager.login_view = 'auth.login'
    login_manager.login_message = 'Please log in to access this page.'

    # 5. Register user-loader callback
    from models import User
    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(int(user_id))

    # 6. Register blueprints
    from routes import main_bp, auth_bp, student_bp, admin_bp

    app.register_blueprint(main_bp)
    app.register_blueprint(auth_bp, url_prefix='/auth')
    app.register_blueprint(student_bp, url_prefix='/student')
    app.register_blueprint(admin_bp, url_prefix='/admin')

    # 7. Create all tables before the first request
    with app.app_context():
        from models import User, Student, Course
        db.create_all()
        app.logger.info("Database tables ensured: %s", db.metadata.tables.keys())

    return app

# Expose the Flask app


if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)
    # app.py
import os
import logging
import dotenv # Import dotenv
from pathlib import Path

# --- Load .env variables FIRST ---
dotenv.load_dotenv() # Load environment variables as early as possible

from flask import Flask
from extensions import db, login_manager, migrate
from config import Config # Import your Config class

def create_app():
    
    # 1. Tell Flask about the instance/ folder
    app = Flask(__name__, instance_relative_config=True)
    os.makedirs(app.instance_path, exist_ok=True)

    # 2. Compute absolute path for the SQLite file
    BASE_DIR = Path(__file__).resolve().parent
    INSTANCE_DIR = BASE_DIR / 'instance'
    DB_PATH = INSTANCE_DIR / 'data.db'
    INSTANCE_DIR.mkdir(parents=True, exist_ok=True)  # safe to re-run

    base_dir = os.path.abspath(os.path.dirname(__file__))
    uploads_dir = os.path.join(base_dir, 'uploads')
    os.makedirs(uploads_dir, exist_ok=True) # Ensure the folder exists

    # 3. Core configuration
    app.config.from_object(Config) # Load all configurations from the Config class

    # Set paths that depend on BASE_DIR after Config is loaded
    app.config['SQLALCHEMY_DATABASE_URI'] = f"sqlite:///{DB_PATH}"
    app.config['UPLOAD_FOLDER'] = uploads_dir

    # 4. Initialize extensions
    db.init_app(app)
    migrate.init_app(app, db)

    login_manager.init_app(app)
    login_manager.login_view = 'auth.login'
    login_manager.login_message = 'Please log in to access this page.'

    # 5. Register user-loader callback
    from models import User
    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(int(user_id))

    # 6. Register blueprints
    from routes import main_bp, auth_bp, student_bp, admin_bp

    app.register_blueprint(main_bp)
    app.register_blueprint(auth_bp, url_prefix='/auth')
    app.register_blueprint(student_bp, url_prefix='/student')
    app.register_blueprint(admin_bp, url_prefix='/admin')

    # 7. Create all tables before the first request
    with app.app_context():
        from models import User, Student, Course
        db.create_all()
        app.logger.info("Database tables ensured: %s", db.metadata.tables.keys())

    return app

# Expose the Flask app


if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)
    app = create_app()
    app.run(debug=True, port=5000)
