"""
会话Controller
负责面试会话相关的路由处理
"""

import os
from urllib.parse import urlparse, urlunparse
from flask import Blueprint, render_template, redirect, url_for
from backend.services.interview_service import SessionService, RoundService
from backend.clients.digitalhub_client import boot_dh
from backend.clients.minio_client import download_resume_data, minio_client
from backend.common.logger import get_logger

logger = get_logger(__name__)

# 创建蓝图
session_bp = Blueprint('session', __name__)

DEFAULT_PUBLIC_HOST = "vtuber.yeying.pub"
PLACEHOLDER_HOSTS = {"your_public_host_here", "your-public-host"}


@session_bp.route('/create_session/<room_id>')
def create_session(room_id):
    """在指定面试间创建新的面试会话"""
    # 检查简历是否已上传
    resume_data = download_resume_data(room_id)
    if not resume_data:
        logger.warning(f"Resume not found for room: {room_id}")
        return """
        <html>
        <head>
            <meta charset=\"UTF-8\">
            <script>
                alert('请先上传简历后再创建面试会话！');
                window.history.back();
            </script>
        </head>
        <body></body>
        </html>
        """, 400

    session = SessionService.create_session(room_id)
    if not session:
        logger.warning(f"Failed to create session for room: {room_id}")
        return "面试间不存在", 404

    return redirect(url_for('session.session_detail', session_id=session.id))


@session_bp.route('/session/<session_id>')
def session_detail(session_id):
    """面试会话详情页面"""
    session = SessionService.get_session(session_id)
    if not session:
        logger.warning(f"Session not found: {session_id}")
        return "面试会话不存在", 404

    # 启动数字人
    dh_message, dh_connect_url = _boot_digital_human(session)

    # 获取轮次数据
    rounds_dict = _load_session_rounds(session)

    # 获取简历数据（从session关联的room获取）
    room_id = session.room.id
    resume_data = download_resume_data(room_id)

    # 检查是否有自定义 JD
    has_custom_jd = bool(session.room.jd_id)

    return render_template('session.html',
                         session=SessionService.to_dict(session),
                         rounds=rounds_dict,
                         resume=resume_data,
                         has_custom_jd=has_custom_jd,
                         dh_message=dh_message,
                         dh_connect_url=dh_connect_url)


# ==================== 私有辅助函数 ====================

def _resolve_public_host() -> str:
    """Return a usable public host, avoiding placeholder defaults."""
    env_host = os.getenv("PUBLIC_HOST")
    if env_host and env_host.lower() not in PLACEHOLDER_HOSTS:
        return env_host
    return DEFAULT_PUBLIC_HOST


def _normalize_connect_url(connect_url: str | None, public_host: str) -> str | None:
    """Ensure connect_url uses the expected public host instead of placeholders."""
    if not connect_url:
        return None

    parsed = urlparse(connect_url)
    if parsed.netloc and parsed.netloc.lower() not in PLACEHOLDER_HOSTS:
        return connect_url

    scheme = parsed.scheme or "https"
    path = parsed.path or ""
    return urlunparse((scheme, public_host, path, "", "", ""))


def _normalize_dh_message(message: str | None, raw_connect_url: str | None,
                         normalized_connect_url: str | None, public_host: str) -> str | None:
    """Replace placeholder hosts in DH boot message so the user sees a real link."""
    if not message:
        return None

    updated_message = message

    if raw_connect_url and normalized_connect_url and raw_connect_url != normalized_connect_url:
        updated_message = updated_message.replace(raw_connect_url, normalized_connect_url)

    for placeholder in PLACEHOLDER_HOSTS:
        if placeholder in updated_message:
            updated_message = updated_message.replace(placeholder, public_host)

    return updated_message


def _boot_digital_human(session):
    """启动数字人服务"""
    try:
        public_host = _resolve_public_host()
        resp = boot_dh(session.room_id, session.id, public_host=public_host)
        data = resp.get("data") or {}

        raw_connect_url = data.get("connect_url")
        dh_connect_url = _normalize_connect_url(raw_connect_url, public_host)
        dh_message = _normalize_dh_message(data.get("message"), raw_connect_url,
                                          dh_connect_url, public_host)
        return dh_message, dh_connect_url
    except Exception as e:
        logger.warning(f"Failed to boot digital human for session {session.id}: {e}")
        return None, None


def _load_session_rounds(session):
    """加载会话的所有轮次数据"""
    session_id = session.id
    room_id = session.room.id

    rounds = RoundService.get_rounds_by_session(session_id)
    rounds_dict = []

    for round_obj in rounds:
        round_data = RoundService.to_dict(round_obj)

        # 加载问题数据
        try:
            questions = _load_round_questions(room_id, session_id, round_data['round_index'])
            round_data['questions'] = questions
        except Exception as e:
            logger.error(f"Error loading questions for round {round_data['id']}: {e}")
            round_data['questions'] = []

        rounds_dict.append(round_data)

    return rounds_dict


def _load_round_questions(room_id: str, session_id: str, round_index: int):
    """从MinIO加载轮次问题数据"""
    questions_data = minio_client.download_json(
        f"rooms/{room_id}/sessions/{session_id}/questions/round_{round_index}.json"
    )

    if questions_data:
        return questions_data.get('questions', [])

    return []
