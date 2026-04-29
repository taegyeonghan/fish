"""
UngdrooFish Backend - Flask Application Factory
"""

import os
import warnings

# suppress multiprocessing resource_tracker warnings from third-party libs (e.g. transformers)
warnings.filterwarnings("ignore", message=".*resource_tracker.*")

from flask import Flask, request
from flask_cors import CORS

from .config import Config
from .utils.logger import setup_logger, get_logger


def create_app(config_class=Config):
    """Flask application factory"""
    app = Flask(__name__)
    app.config.from_object(config_class)

    # JSON encoding: display Korean/CJK characters directly (not \uXXXX)
    if hasattr(app, 'json') and hasattr(app.json, 'ensure_ascii'):
        app.json.ensure_ascii = False

    logger = setup_logger('ungdroofish')

    # only log startup in reloader subprocess (avoid double log in debug mode)
    is_reloader_process = os.environ.get('WERKZEUG_RUN_MAIN') == 'true'
    debug_mode = app.config.get('DEBUG', False)
    should_log_startup = not debug_mode or is_reloader_process

    if should_log_startup:
        logger.info("=" * 50)
        logger.info("UngdrooFish Backend starting...")
        logger.info("=" * 50)

    CORS(app, resources={r"/api/*": {"origins": "*"}})

    # register simulation process cleanup
    from .services.simulation_runner import SimulationRunner
    SimulationRunner.register_cleanup()
    if should_log_startup:
        logger.info("Simulation process cleanup registered")

    # request logging middleware
    @app.before_request
    def log_request():
        logger = get_logger('ungdroofish.request')
        logger.debug(f"Request: {request.method} {request.path}")
        if request.content_type and 'json' in request.content_type:
            logger.debug(f"Body: {request.get_json(silent=True)}")

    @app.after_request
    def log_response(response):
        logger = get_logger('ungdroofish.request')
        logger.debug(f"Response: {response.status_code}")
        return response

    # register blueprints
    from .api import graph_bp, simulation_bp, report_bp, invest_bp
    app.register_blueprint(graph_bp, url_prefix='/api/graph')
    app.register_blueprint(simulation_bp, url_prefix='/api/simulation')
    app.register_blueprint(report_bp, url_prefix='/api/report')
    app.register_blueprint(invest_bp, url_prefix='/api/invest')

    # health check
    @app.route('/health')
    def health():
        return {'status': 'ok', 'service': 'UngdrooFish Backend'}

    if should_log_startup:
        logger.info("UngdrooFish Backend started successfully")

    return app