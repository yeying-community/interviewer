"""
数据库模型定义
使用Peewee ORM进行数据持久化
"""

from datetime import datetime
from peewee import *
import os
from dotenv import load_dotenv

load_dotenv()

# 数据库配置
DATABASE_PATH = os.getenv('DATABASE_PATH', 'data/yeying_interviewer.db')

# 确保数据目录存在（除非是内存数据库）
if DATABASE_PATH != ':memory:' and os.path.dirname(DATABASE_PATH):
    os.makedirs(os.path.dirname(DATABASE_PATH), exist_ok=True)

# 数据库连接
database = SqliteDatabase(DATABASE_PATH)


class BaseModel(Model):
    """基础模型类"""
    created_at = DateTimeField(default=datetime.now)
    updated_at = DateTimeField(default=datetime.now)
    
    class Meta:
        database = database
    
    def save(self, *args, **kwargs):
        self.updated_at = datetime.now()
        return super().save(*args, **kwargs)


class Room(BaseModel):
    """面试间模型"""
    id = CharField(primary_key=True)
    memory_id = CharField(unique=True)
    name = CharField(default="面试间")
    
    class Meta:
        table_name = 'rooms'


class Session(BaseModel):
    """面试会话模型"""
    id = CharField(primary_key=True)
    name = CharField()
    room = ForeignKeyField(Room, backref='sessions')
    status = CharField(default='active')  # active, completed, paused
    
    class Meta:
        table_name = 'sessions'


class Round(BaseModel):
    """对话轮次模型"""
    id = CharField(primary_key=True)
    session = ForeignKeyField(Session, backref='rounds')
    round_index = IntegerField()
    questions_count = IntegerField(default=0)
    questions_file_path = CharField()  # MinIO中的文件路径
    round_type = CharField(default='ai_generated')  # ai_generated, manual
    current_question_index = IntegerField(default=0)  # 当前问题索引
    status = CharField(default='active')  # active, completed, paused

    class Meta:
        table_name = 'rounds'


class QuestionAnswer(BaseModel):
    """问答记录模型"""
    id = CharField(primary_key=True)
    round = ForeignKeyField(Round, backref='question_answers')
    question_index = IntegerField()  # 问题在轮次中的索引
    question_text = TextField()  # 问题内容
    answer_text = TextField(null=True)  # 用户回答
    question_category = CharField(null=True)  # 问题分类
    is_answered = BooleanField(default=False)  # 是否已回答

    class Meta:
        table_name = 'question_answers'


def create_tables():
    """创建数据库表"""
    if not database.is_closed():
        database.close()
    database.connect()
    database.create_tables([Room, Session, Round, QuestionAnswer], safe=True)
    database.close()


def init_database():
    """初始化数据库"""
    create_tables()
    print("Database initialized successfully")