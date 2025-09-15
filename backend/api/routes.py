"""
API路由模块
"""

from flask import Blueprint, request, jsonify, render_template
from backend.services.interview_service import RoomService, SessionService, RoundService
from backend.services.question_service import question_generation_service
from backend.utils.minio_client import download_resume_data, minio_client


# 创建蓝图
main_bp = Blueprint('main', __name__)
api_bp = Blueprint('api', __name__, url_prefix='/api')


# 主页面路由
@main_bp.route('/')
def index():
    """首页 - 显示面试间列表"""
    rooms = RoomService.get_all_rooms()
    rooms_dict = [RoomService.to_dict(room) for room in rooms]
    return render_template('index.html', rooms=rooms_dict)


@main_bp.route('/create_room')
def create_room():
    """创建新的面试间"""
    room = RoomService.create_room()
    return jsonify({
        'success': True,
        'room': RoomService.to_dict(room),
        'redirect_url': f'/room/{room.id}'
    })


@main_bp.route('/room/<room_id>')
def room_detail(room_id):
    """面试间详情页面"""
    room = RoomService.get_room(room_id)
    if not room:
        return "面试间不存在", 404
    
    sessions = SessionService.get_sessions_by_room(room_id)
    sessions_dict = [SessionService.to_dict(session) for session in sessions]
    
    return render_template('room.html', 
                         room=RoomService.to_dict(room), 
                         sessions=sessions_dict)


@main_bp.route('/create_session/<room_id>')
def create_session(room_id):
    """在指定面试间创建新的面试会话"""
    session = SessionService.create_session(room_id)
    if not session:
        return "面试间不存在", 404
    
    return jsonify({
        'success': True,
        'session': SessionService.to_dict(session),
        'redirect_url': f'/session/{session.id}'
    })


@main_bp.route('/session/<session_id>')
def session_detail(session_id):
    """面试会话详情页面"""
    session = SessionService.get_session(session_id)
    if not session:
        return "面试会话不存在", 404
    
    rounds = RoundService.get_rounds_by_session(session_id)
    rounds_dict = [RoundService.to_dict(round_obj) for round_obj in rounds]
    
    # 获取简历数据用于展示
    resume_data = download_resume_data()
    
    return render_template('session.html',
                         session=SessionService.to_dict(session),
                         rounds=rounds_dict,
                         resume=resume_data)


@main_bp.route('/generate_questions/<session_id>', methods=['POST'])
def generate_questions(session_id):
    """生成面试题"""
    session = SessionService.get_session(session_id)
    if not session:
        return jsonify({'error': '面试会话不存在'}), 404
    
    result = question_generation_service.generate_questions(session_id)
    
    if result['success']:
        return jsonify(result)
    else:
        return jsonify({'error': result['error']}), 500


# API路由
@api_bp.route('/rooms')
def api_rooms():
    """API: 获取所有面试间"""
    rooms = RoomService.get_all_rooms()
    return jsonify([RoomService.to_dict(room) for room in rooms])


@api_bp.route('/sessions/<room_id>')
def api_sessions(room_id):
    """API: 获取指定面试间的所有会话"""
    sessions = SessionService.get_sessions_by_room(room_id)
    return jsonify([SessionService.to_dict(session) for session in sessions])


@api_bp.route('/rounds/<session_id>')
def api_rounds(session_id):
    """API: 获取指定会话的所有轮次"""
    rounds = RoundService.get_rounds_by_session(session_id)
    return jsonify([RoundService.to_dict(round_obj) for round_obj in rounds])


@api_bp.route('/minio/test')
def api_minio_test():
    """API: 测试MinIO连接和数据访问"""
    try:
        # 测试列出文件
        objects = minio_client.list_objects(prefix="data/")
        
        # 测试加载简历数据
        resume_data = download_resume_data()
        
        return jsonify({
            'status': 'success',
            'minio_objects': objects,
            'resume_loaded': resume_data is not None,
            'candidate_name': resume_data.get('name') if resume_data else None
        })
        
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500