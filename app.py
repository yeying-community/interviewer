#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Yeying面试官系统 - Flask应用主入口

系统架构：
- 面试间 (Room): 包含memory_id的面试空间
- 面试会话 (Session): 面试间内的具体会话实例
- 对话轮次 (Round): 会话内的问答轮次，每轮生成新的面试题

技术栈：Flask + Qwen API + HTML/CSS/JS
"""

import os
import json
import uuid
from datetime import datetime
from flask import Flask, render_template, request, jsonify, redirect, url_for
from pathlib import Path

# 添加项目路径以支持模块导入
project_root = Path(__file__).parent
import sys
sys.path.append(str(project_root))

from llm.clients.qwen_client import QwenClient
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

app = Flask(__name__, 
           template_folder='frontend/templates',
           static_folder='frontend/static')
app.secret_key = os.getenv('SECRET_KEY', 'dev-secret-key')

# 全局变量存储会话数据（生产环境建议使用数据库）
rooms = {}
sessions = {}
rounds = {}

def load_resume_data():
    """加载简历数据"""
    try:
        with open('tests/data/resume.json', 'r', encoding='utf-8') as f:
            return json.load(f)
    except FileNotFoundError:
        return None

def format_resume_for_llm(resume_data):
    """格式化简历数据供LLM使用"""
    if not resume_data:
        return ""
    
    content = f"""
姓名：{resume_data.get('name', '')}
职位：{resume_data.get('position', '')}

技能：
"""
    skills = resume_data.get('skills', [])
    for i, skill in enumerate(skills, 1):
        content += f"{i}. {skill}\n"
    
    content += "\n项目经验：\n"
    projects = resume_data.get('projects', [])
    for i, project in enumerate(projects, 1):
        content += f"{i}. {project}\n"
    
    return content.strip()

@app.route('/')
def index():
    """首页 - 显示面试间列表"""
    return render_template('index.html', 
                         rooms=rooms, 
                         sessions=sessions, 
                         rounds=rounds)

@app.route('/create_room')
def create_room():
    """创建新的面试间"""
    room_id = str(uuid.uuid4())
    memory_id = f"memory_{room_id[:8]}"
    
    rooms[room_id] = {
        'id': room_id,
        'memory_id': memory_id,
        'created_at': datetime.now().isoformat(),
        'sessions': []
    }
    
    return redirect(url_for('room_detail', room_id=room_id))

@app.route('/room/<room_id>')
def room_detail(room_id):
    """面试间详情页面 - 显示该间内的所有会话"""
    room = rooms.get(room_id)
    if not room:
        return "面试间不存在", 404
    
    # 获取该面试间的所有会话
    room_sessions = []
    for session_id in room['sessions']:
        if session_id in sessions:
            room_sessions.append(sessions[session_id])
    
    return render_template('room.html', room=room, sessions=room_sessions, rounds=rounds)

@app.route('/create_session/<room_id>')
def create_session(room_id):
    """在指定面试间创建新的面试会话"""
    room = rooms.get(room_id)
    if not room:
        return "面试间不存在", 404
    
    session_id = str(uuid.uuid4())
    session_name = f"面试会话{len(room['sessions']) + 1}"
    
    sessions[session_id] = {
        'id': session_id,
        'name': session_name,
        'room_id': room_id,
        'created_at': datetime.now().isoformat(),
        'rounds': []
    }
    
    room['sessions'].append(session_id)
    
    return redirect(url_for('session_detail', session_id=session_id))

@app.route('/session/<session_id>')
def session_detail(session_id):
    """面试会话详情页面 - 类似ChatGPT的聊天界面"""
    session = sessions.get(session_id)
    if not session:
        return "面试会话不存在", 404
    
    # 获取该会话的所有轮次
    session_rounds = []
    for round_id in session['rounds']:
        if round_id in rounds:
            session_rounds.append(rounds[round_id])
    
    # 获取简历数据用于展示
    resume_data = load_resume_data()
    
    return render_template('session.html', 
                         session=session, 
                         rounds=session_rounds,
                         resume=resume_data)

@app.route('/generate_questions/<session_id>', methods=['POST'])
def generate_questions(session_id):
    """生成面试题 - 创建新的对话轮次"""
    session = sessions.get(session_id)
    if not session:
        return jsonify({'error': '面试会话不存在'}), 404
    
    try:
        # 加载简历数据
        resume_data = load_resume_data()
        if not resume_data:
            return jsonify({'error': '未找到简历数据'}), 400
        
        # 格式化简历内容
        resume_content = format_resume_for_llm(resume_data)
        
        # 初始化Qwen客户端并生成问题
        client = QwenClient()
        questions = client.generate_questions(resume_content, num_questions=5)
        
        if not questions:
            return jsonify({'error': '未能生成面试题'}), 500
        
        # 创建新的轮次
        round_id = str(uuid.uuid4())
        round_index = len(session['rounds'])
        
        rounds[round_id] = {
            'id': round_id,
            'index': round_index,
            'session_id': session_id,
            'questions': questions,
            'created_at': datetime.now().isoformat(),
            'type': 'ai_generated'
        }
        
        session['rounds'].append(round_id)
        
        # 保存生成的问题到文件（可选）
        save_questions_to_file(questions, round_index)
        
        return jsonify({
            'success': True,
            'round_id': round_id,
            'questions': questions,
            'round_index': round_index
        })
        
    except Exception as e:
        return jsonify({'error': f'生成面试题失败: {str(e)}'}), 500

def save_questions_to_file(questions, round_index):
    """保存问题到文件"""
    os.makedirs('tests/data', exist_ok=True)
    
    qa_data = {
        'questions': questions,
        'round_index': round_index,
        'total_count': len(questions),
        'generated_at': datetime.now().isoformat()
    }
    
    filename = f'tests/data/questions_round_{round_index}.json'
    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(qa_data, f, ensure_ascii=False, indent=2)

@app.route('/api/rooms')
def api_rooms():
    """API: 获取所有面试间"""
    return jsonify(list(rooms.values()))

@app.route('/api/sessions/<room_id>')
def api_sessions(room_id):
    """API: 获取指定面试间的所有会话"""
    room = rooms.get(room_id)
    if not room:
        return jsonify({'error': '面试间不存在'}), 404
    
    room_sessions = []
    for session_id in room['sessions']:
        if session_id in sessions:
            room_sessions.append(sessions[session_id])
    
    return jsonify(room_sessions)

if __name__ == '__main__':
    # 创建默认的面试间和会话用于测试
    if not rooms:
        default_room_id = str(uuid.uuid4())
        rooms[default_room_id] = {
            'id': default_room_id,
            'memory_id': f"memory_{default_room_id[:8]}",
            'created_at': datetime.now().isoformat(),
            'sessions': []
        }
        
        # 创建默认会话
        default_session_id = str(uuid.uuid4())
        sessions[default_session_id] = {
            'id': default_session_id,
            'name': '面试会话1',
            'room_id': default_room_id,
            'created_at': datetime.now().isoformat(),
            'rounds': []
        }
        rooms[default_room_id]['sessions'].append(default_session_id)
    
    app.run(host='0.0.0.0', port=5000, debug=True)