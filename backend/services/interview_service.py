"""
面试管理服务
"""

import uuid
from typing import List, Optional, Dict, Any
from backend.models.models import Room, Session, Round


class RoomService:
    """房间管理服务"""
    
    @staticmethod
    def create_room(name: Optional[str] = None) -> Room:
        """创建新的面试间"""
        room_id = str(uuid.uuid4())
        memory_id = f"memory_{room_id[:8]}"
        room_name = name or "面试间"
        
        room = Room.create(
            id=room_id,
            memory_id=memory_id,
            name=room_name
        )
        return room
    
    @staticmethod
    def get_room(room_id: str) -> Optional[Room]:
        """获取面试间"""
        try:
            return Room.get_by_id(room_id)
        except Room.DoesNotExist:
            return None
    
    @staticmethod
    def get_all_rooms() -> List[Room]:
        """获取所有面试间"""
        return list(Room.select().order_by(Room.created_at.desc()))
    
    @staticmethod
    def delete_room(room_id: str) -> bool:
        """删除面试间"""
        try:
            room = Room.get_by_id(room_id)
            # 删除相关的会话和轮次
            for session in room.sessions:
                SessionService.delete_session(session.id)
            room.delete_instance()
            return True
        except Room.DoesNotExist:
            return False
    
    @staticmethod
    def to_dict(room: Room) -> Dict[str, Any]:
        """将Room对象转换为字典"""
        sessions = SessionService.get_sessions_by_room(room.id)
        total_rounds = 0
        
        for session in sessions:
            rounds = RoundService.get_rounds_by_session(session.id)
            total_rounds += len(rounds)
        
        return {
            'id': room.id,
            'memory_id': room.memory_id,
            'name': room.name,
            'created_at': room.created_at.isoformat(),
            'updated_at': room.updated_at.isoformat(),
            'sessions_count': len(sessions),
            'rounds_count': total_rounds
        }


class SessionService:
    """会话管理服务"""
    
    @staticmethod
    def create_session(room_id: str, name: Optional[str] = None) -> Optional[Session]:
        """在指定面试间创建新的面试会话"""
        room = RoomService.get_room(room_id)
        if not room:
            return None
        
        session_id = str(uuid.uuid4())
        session_name = name or f"面试会话{room.sessions.count() + 1}"
        
        session = Session.create(
            id=session_id,
            name=session_name,
            room=room
        )
        return session
    
    @staticmethod
    def get_session(session_id: str) -> Optional[Session]:
        """获取面试会话"""
        try:
            return Session.get_by_id(session_id)
        except Session.DoesNotExist:
            return None
    
    @staticmethod
    def get_sessions_by_room(room_id: str) -> List[Session]:
        """获取指定房间的所有会话"""
        room = RoomService.get_room(room_id)
        if not room:
            return []
        return list(room.sessions.order_by(Session.created_at.desc()))
    
    @staticmethod
    def delete_session(session_id: str) -> bool:
        """删除会话"""
        try:
            session = Session.get_by_id(session_id)
            # 删除相关的轮次
            for round_obj in session.rounds:
                RoundService.delete_round(round_obj.id)
            session.delete_instance()
            return True
        except Session.DoesNotExist:
            return False
    
    @staticmethod
    def update_session_status(session_id: str, status: str) -> bool:
        """更新会话状态"""
        try:
            session = Session.get_by_id(session_id)
            session.status = status
            session.save()
            return True
        except Session.DoesNotExist:
            return False
    
    @staticmethod
    def to_dict(session: Session) -> Dict[str, Any]:
        """将Session对象转换为字典"""
        rounds = RoundService.get_rounds_by_session(session.id)
        total_questions = 0
        
        for round_obj in rounds:
            total_questions += round_obj.questions_count
        
        return {
            'id': session.id,
            'name': session.name,
            'room_id': session.room.id,
            'status': session.status,
            'created_at': session.created_at.isoformat(),
            'updated_at': session.updated_at.isoformat(),
            'rounds_count': len(rounds),
            'questions_count': total_questions
        }


class RoundService:
    """轮次管理服务"""
    
    @staticmethod
    def create_round(session_id: str, questions: List[str], round_type: str = 'ai_generated') -> Optional[Round]:
        """创建新的对话轮次"""
        session = SessionService.get_session(session_id)
        if not session:
            return None
        
        round_id = str(uuid.uuid4())
        round_index = session.rounds.count()
        questions_file_path = f"data/questions_round_{round_index}_{session_id}.json"
        
        round_obj = Round.create(
            id=round_id,
            session=session,
            round_index=round_index,
            questions_count=len(questions),
            questions_file_path=questions_file_path,
            round_type=round_type
        )
        return round_obj
    
    @staticmethod
    def get_round(round_id: str) -> Optional[Round]:
        """获取轮次"""
        try:
            return Round.get_by_id(round_id)
        except Round.DoesNotExist:
            return None
    
    @staticmethod
    def get_rounds_by_session(session_id: str) -> List[Round]:
        """获取指定会话的所有轮次"""
        session = SessionService.get_session(session_id)
        if not session:
            return []
        return list(session.rounds.order_by(Round.round_index))
    
    @staticmethod
    def delete_round(round_id: str) -> bool:
        """删除轮次"""
        try:
            round_obj = Round.get_by_id(round_id)
            round_obj.delete_instance()
            return True
        except Round.DoesNotExist:
            return False
    
    @staticmethod
    def to_dict(round_obj: Round) -> Dict[str, Any]:
        """将Round对象转换为字典"""
        return {
            'id': round_obj.id,
            'session_id': round_obj.session.id,
            'round_index': round_obj.round_index,
            'questions_count': round_obj.questions_count,
            'questions_file_path': round_obj.questions_file_path,
            'round_type': round_obj.round_type,
            'created_at': round_obj.created_at.isoformat(),
            'updated_at': round_obj.updated_at.isoformat()
        }