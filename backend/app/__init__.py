"""
UngdrooFish Backend - Flask Application Factory
"""

import os
import mimetypes
import warnings

# Windows 레지스트리가 .js 를 text/plain 으로 등록한 경우 ES module 스크립트 실행이 거부된다.
# Flask send_from_directory(=mimetypes.guess_type)가 올바른 MIME 을 반환하도록 강제 등록.
mimetypes.add_type('text/javascript', '.js')
mimetypes.add_type('text/javascript', '.mjs')
mimetypes.add_type('text/css', '.css')
mimetypes.add_type('application/json', '.json')
mimetypes.add_type('image/svg+xml', '.svg')

# suppress multiprocessing resource_tracker warnings from third-party libs (e.g. transformers)
warnings.filterwarnings("ignore", message=".*resource_tracker.*")

from flask import Flask, request, send_from_directory
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

    # built Vue SPA serving (collapses the frontend into this one process)
    # dist 경로: backend/app/__init__.py -> ../../frontend/dist
    frontend_dist = os.path.abspath(
        os.path.join(os.path.dirname(__file__), '..', '..', 'frontend', 'dist')
    )

    @app.route('/', defaults={'path': ''})
    @app.route('/<path:path>')
    def serve_spa(path):
        # /api/*, /health 는 위 블루프린트/라우트가 우선 매칭되므로 여기 도달하지 않음.
        # 정적 파일이 있으면 그 파일을, 없으면 SPA fallback 으로 index.html (createWebHistory 딥링크 대응).
        if not os.path.isdir(frontend_dist):
            return (
                'UngdrooFish frontend dist not found. '
                'Run `npm run build` in gemstone-forecast-sim/frontend.',
                503,
            )
        candidate = os.path.join(frontend_dist, path)
        if path and os.path.isfile(candidate):
            return send_from_directory(frontend_dist, path)
        return send_from_directory(frontend_dist, 'index.html')

    if should_log_startup:
        logger.info("UngdrooFish Backend started successfully")
        logger.info(f"Serving frontend dist from: {frontend_dist}")

    return app