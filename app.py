"""Flask application factory for POS System."""
import os
import sys

from flask import Flask
from flask_login import LoginManager
from flask_wtf.csrf import CSRFProtect

from config import config
from models import db, User


def _resource_path(relative_path):
    """Resolve path for PyInstaller bundle or development."""
    if getattr(sys, 'frozen', False):
        return os.path.join(sys._MEIPASS, relative_path)
    return os.path.join(os.path.dirname(os.path.abspath(__file__)), relative_path)


def create_app(config_name='default'):
    """Create and configure Flask application."""
    app = Flask(__name__,
                template_folder=_resource_path('templates'),
                static_folder=_resource_path('static'))
    app.config.from_object(config[config_name])
    
    # Security: Limit upload size to 16MB for Excel imports
    app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024 
    
    CSRFProtect(app)
    db.init_app(app)
    
    login_manager = LoginManager()
    login_manager.init_app(app)
    login_manager.login_view = 'auth.login'
    login_manager.login_message = 'Please log in to access this page.'
    login_manager.login_message_category = 'info'
    
    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(int(user_id))
    
    # Register blueprints
    from routes.auth import auth_bp
    from routes.pos import pos_bp
    from routes.inventory import inventory_bp
    from routes.customers import customers_bp
    from routes.dashboard import dashboard_bp
    from routes.reports import reports_bp
    
    app.register_blueprint(auth_bp, url_prefix='/auth')
    app.register_blueprint(pos_bp, url_prefix='/pos')
    app.register_blueprint(inventory_bp, url_prefix='/inventory')
    app.register_blueprint(customers_bp, url_prefix='/customers')
    app.register_blueprint(dashboard_bp, url_prefix='/dashboard')
    app.register_blueprint(reports_bp, url_prefix='/reports')
    
    @app.route('/')
    def index():
        from flask import redirect
        # Check if setup is needed
        try:
            if not User.query.first():
                return redirect('/auth/setup')
        except Exception:
            # Handle cases where DB is not yet initialized
            pass
        return redirect('/dashboard')
    
    # Create tables and run migrations
    with app.app_context():
        db.create_all()
        
        # Migration logic for existing installations
        try:
            from sqlalchemy import text
            # 1. Add cost_price to sales_items (Essential for the Profit Report)
            result = db.session.execute(text("PRAGMA table_info(sales_items)"))
            cols = [r[1] for r in result]
            if 'cost_price' not in cols:
                db.session.execute(text("ALTER TABLE sales_items ADD COLUMN cost_price NUMERIC(12,2) DEFAULT 0"))
                db.session.commit()
            
            # 2. Migration: Ensure products table has expiry_date if mentioned in templates
            result_prod = db.session.execute(text("PRAGMA table_info(products)"))
            prod_cols = [r[1] for r in result_prod]
            if 'expiry_date' not in prod_cols:
                db.session.execute(text("ALTER TABLE products ADD COLUMN expiry_date DATE"))
                db.session.commit()
                
        except Exception as e:
            print(f"Migration error: {e}")
            db.session.rollback()
    
    # Inject POS name and current summary into all templates
    @app.context_processor
    def inject_globals():
        return {
            'pos_name': app.config.get('POS_NAME', 'POS System'),
            # You can inject simple summary data here if needed by base.html
        }
    
    return app
