"""Flask应用入口"""
from flask import Flask
from backend.api import interview_routes, room_routes, question_routes
from config import Config

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)
    
    # 注册蓝图
    app.register_blueprint(interview_routes.bp, url_prefix='/api/interview')
    app.register_blueprint(room_routes.bp, url_prefix='/api/room')
    app.register_blueprint(question_routes.bp, url_prefix='/api/question')
    
    return app

if __name__ == '__main__':
    app = create_app()
    app.run(debug=True, host='0.0.0.0', port=5000)