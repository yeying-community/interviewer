from peewee import CharField, Database, Proxy, Model, TextField, IntegerField

database_proxy: Database = Proxy()


class DbModel(Model):
    class Meta:
        database = database_proxy


class SchemaMigration(DbModel):
    version = CharField()


# 用户模型
class UserDO(DbModel):
    class Meta:
        table_name = 'users'

    did = CharField(primary_key=True, max_length=128)
    name = CharField(null=False, max_length=128)
    avatar = TextField(null=True)
    createdAt = CharField(null=False, column_name="created_at", max_length=64)
    updatedAt = CharField(null=False, column_name="updated_at", max_length=64)
    signature = CharField(null=False, max_length=192)


class UserStateDO(DbModel):
    class Meta:
        table_name = 'user_state'

    owner = CharField(null=False, max_length=128)
    did = CharField(primary_key=True, max_length=128)
    role = CharField(null=False, max_length=64)
    status = CharField(null=False, max_length=64)
    createdAt = CharField(null=False, column_name="created_at", max_length=64)
    updatedAt = CharField(null=False, column_name="updated_at", max_length=64)
    signature = CharField(null=False, max_length=192)


# === 面试官的数据模型 ===

class ResumeDO(DbModel):
    """简历表"""

    class Meta:
        table_name = 'resumes'

    resumeId = CharField(primary_key=True, max_length=36, column_name="resume_id")  # UUID
    did = CharField(null=False, max_length=255)  # 用户DID
    resumeName = CharField(null=False, max_length=100, column_name="resume_name")  # 简历名称
    version = CharField(null=False, max_length=32, default='v1.0')  # 版本号
    fileUrl = CharField(null=True, max_length=500, column_name="file_url")  # 文件URL
    promptType = CharField(null=True, max_length=64, column_name="prompt_type")  # prompt类型

    createdAt = CharField(null=False, column_name="created_at", max_length=64)  # 创建时间
    updatedAt = CharField(null=False, column_name="updated_at", max_length=64)  # 更新时间
    signature = CharField(null=False, max_length=192)


class JobInfoDO(DbModel):
    """职位信息表"""

    class Meta:
        table_name = 'job_infos'

    jobInfoId = CharField(primary_key=True, max_length=36, column_name="job_info_id")  # UUID
    company = CharField(null=False, max_length=255)  # 公司名称
    jobTitle = CharField(null=False, max_length=255, column_name="job_title")  # 职位名称
    jobDescription = TextField(null=True, column_name="job_description")  # 职位描述

    createdAt = CharField(null=False, column_name="created_at", max_length=64)  # 创建时间
    updatedAt = CharField(null=False, column_name="updated_at", max_length=64)  # 更新时间
    signature = CharField(null=False, max_length=192)


class InterviewRoomDO(DbModel):
    """面试间表"""

    class Meta:
        table_name = 'interview_rooms'

    roomId = CharField(primary_key=True, max_length=36, column_name="room_id")  # UUID
    did = CharField(null=False, max_length=255)  # 用户DID
    roomName = CharField(null=False, max_length=100, column_name="room_name")  # 面试间名称

    # 三个知识库ID
    contextId = CharField(null=False, max_length=36, column_name="context_id")  # 上下文知识库ID
    experienceId = CharField(null=False, max_length=36, column_name="experience_id")  # 用户知识库ID
    knowledgeId = CharField(null=False, max_length=36, column_name="knowledge_id")  # 应用知识库ID

    # 外键关系
    resumeId = CharField(null=False, max_length=36, column_name="resume_id")  # 简历ID
    jobInfoId = CharField(null=False, max_length=36, column_name="job_info_id")  # 职位信息ID

    createdAt = CharField(null=False, column_name="created_at", max_length=64)  # 创建时间
    updatedAt = CharField(null=False, column_name="updated_at", max_length=64)  # 更新时间
    signature = CharField(null=False, max_length=192)


class InterviewSessionDO(DbModel):
    """面试会话表"""

    class Meta:
        table_name = 'interview_sessions'

    sessionId = CharField(primary_key=True, max_length=36, column_name="session_id")  # UUID
    sessionName = CharField(null=False, max_length=100, column_name="session_name")  # 会话名称

    # 外键关系
    roomId = CharField(null=False, max_length=36, column_name="room_id")  # 面试间ID

    createdAt = CharField(null=False, column_name="created_at", max_length=64)  # 创建时间
    updatedAt = CharField(null=False, column_name="updated_at", max_length=64)  # 更新时间
    signature = CharField(null=False, max_length=192)


class InterviewSessionRoundDO(DbModel):
    """面试会话轮次表"""

    class Meta:
        table_name = 'interview_session_rounds'

    roundId = CharField(primary_key=True, max_length=36, column_name="round_id")  # UUID
    round = IntegerField(null=False)  # 轮次编号
    qaJsonUrl = CharField(null=True, max_length=255, column_name="qa_json_url")  # 问答JSON URL

    # 外键关系
    sessionId = CharField(null=False, max_length=36, column_name="session_id")  # 会话ID

    createdAt = CharField(null=False, column_name="created_at", max_length=64)  # 创建时间
    updatedAt = CharField(null=False, column_name="updated_at", max_length=64)  # 更新时间
    signature = CharField(null=False, max_length=192)


class InterviewReportDO(DbModel):
    """面试报告表"""

    class Meta:
        table_name = 'interview_reports'

    reportId = CharField(primary_key=True, max_length=36, column_name="report_id")  # UUID
    reportName = CharField(null=False, max_length=100, column_name="report_name")  # 报告名称
    reportJsonUrl = CharField(null=True, max_length=255, column_name="report_json_url")  # 报告JSON URL
    summary = TextField(null=True)  # 面试总结

    # 外键关系
    roundId = CharField(null=False, max_length=36, column_name="round_id")  # 轮次ID

    createdAt = CharField(null=False, column_name="created_at", max_length=64)  # 创建时间
    updatedAt = CharField(null=False, column_name="updated_at", max_length=64)  # 更新时间
    signature = CharField(null=False, max_length=192)


class TaskDO(DbModel):
    """任务表"""

    class Meta:
        table_name = 'tasks'

    taskId = CharField(primary_key=True, max_length=36, column_name="task_id")  # UUID
    taskType = CharField(null=True, max_length=64, column_name="task_type")  # 任务类型
    relatedId = CharField(null=True, max_length=36, column_name="related_id")  # 关联ID
    status = CharField(null=False, max_length=20, default='pending')  # 任务状态
    resultUrl = CharField(null=True, max_length=255, column_name="result_url")  # 结果URL
    log = TextField(null=True)  # 日志

    createdAt = CharField(null=False, column_name="created_at", max_length=64)  # 创建时间
    updatedAt = CharField(null=False, column_name="updated_at", max_length=64)  # 更新时间
    signature = CharField(null=False, max_length=192)
