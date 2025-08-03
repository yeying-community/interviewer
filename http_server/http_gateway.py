# http_gateway.py
import sys
import os
from flask import Flask, request, jsonify
from flask_cors import CORS
import grpc
import logging
from google.protobuf.json_format import MessageToDict

# 添加项目根目录到Python路径
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(current_dir)
sys.path.insert(0, project_root)

# 导入项目模块
try:
    import yeying.api.interviewer.room_pb2 as room_pb2
    import yeying.api.interviewer.room_pb2_grpc as room_pb2_grpc
    import yeying.api.common.message_pb2 as message_pb2
    from interviewer.tool.date import getCurrentUtcString
    
    print(f"Successfully imported modules from: {project_root}")
except ImportError as e:
    print(f"Import error: {e}")
    print(f"Current working directory: {os.getcwd()}")
    print(f"Project root: {project_root}")
    print(f"Python path: {sys.path}")
    raise

# 初始化 Flask 应用
app = Flask(__name__)
CORS(app)

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# gRPC 客户端配置
GRPC_SERVERS = [
    "localhost:9401",
    "[::1]:9401", 
    "127.0.0.1:9401",
]

def test_grpc_connection():
    """测试gRPC连接并返回详细信息"""
    for server in GRPC_SERVERS:
        try:
            logger.info(f"Trying to connect to {server}...")
            channel = grpc.insecure_channel(server)
            
            try:
                grpc.channel_ready_future(channel).result(timeout=3)
                logger.info(f"gRPC channel connected to {server}")
                return channel, server
            except grpc.FutureTimeoutError:
                logger.warning(f"gRPC connection timeout to {server}")
                channel.close()
                continue
            except Exception as e:
                logger.warning(f"gRPC connection failed to {server}: {e}")
                channel.close()
                continue
                
        except Exception as e:
            logger.warning(f"Failed to create gRPC channel to {server}: {e}")
            continue
    
    logger.error("All gRPC connection attempts failed")
    return None, None

def get_grpc_stub():
    """获取gRPC Stub"""
    if channel is None:
        logger.error("Cannot create stub: no gRPC channel")
        return None
    
    try:
        # 根据测试文件，应该使用RoomStub
        if hasattr(room_pb2_grpc, 'RoomStub'):
            stub = room_pb2_grpc.RoomStub(channel)
            logger.info("Using gRPC stub: RoomStub")
            return stub
        else:
            logger.error("RoomStub not found in room_pb2_grpc")
            return None
    except Exception as e:
        logger.error(f"Error creating gRPC stub: {e}")
        return None

# 创建连接
channel, connected_server = test_grpc_connection()
GRPC_SERVER = connected_server or GRPC_SERVERS[0]
stub = get_grpc_stub()

def create_message_header():
    """创建消息头，与测试文件中的格式一致"""
    return message_pb2.MessageHeader()

# RESTful API 路由
@app.route("/api/v1/rooms", methods=["POST"])
def create_room():
    """创建面试间"""
    try:
        if not request.is_json:
            return jsonify({"error": "Request must be JSON"}), 400
        
        data = request.json
        
        # 验证必填字段
        required_fields = ["roomId", "did", "roomName"]
        for field in required_fields:
            if not data.get(field):
                return jsonify({"error": f"Missing required field: {field}"}), 400
        
        # 构建房间元数据 - 与测试文件保持一致
        room_metadata = room_pb2.RoomMetadata(
            roomId=data.get("roomId"),
            did=data.get("did"),
            roomName=data.get("roomName"),
            resumeId=data.get("resumeId", ""),
            jobInfoId=data.get("jobInfoId", ""),
            contextId=data.get("contextId", ""),
            experienceId=data.get("experienceId", ""),
            knowledgeId=data.get("knowledgeId", ""),
            createdAt=getCurrentUtcString(),
            updatedAt=getCurrentUtcString(),
            signature=data.get("signature", "")
        )
        
        grpc_request = room_pb2.CreateRoomRequest(
            header=create_message_header(),
            body=room_pb2.CreateRoomRequestBody(room=room_metadata)
        )
        
        response = stub.Create(grpc_request)
        
        if response.body.status.code != 200:
            return jsonify({
                "error": response.body.status.message or "Failed to create room"
            }), response.body.status.code
        
        return jsonify({
            "status": response.body.status.code,
            "message": response.body.status.message or "Room created successfully",
            "data": MessageToDict(response.body.room)
        }), 200
        
    except grpc.RpcError as e:
        logger.error(f"gRPC error: {e}")
        return jsonify({"error": "gRPC service unavailable"}), 503
    except Exception as e:
        logger.error(f"Create room error: {str(e)}")
        return jsonify({"error": "Internal server error"}), 500

@app.route("/api/v1/rooms/<string:did>/<string:room_id>", methods=["GET"])
def get_room(did, room_id):
    """获取面试间详情"""
    try:
        grpc_request = room_pb2.GetRoomRequest(
            header=create_message_header(),
            body=room_pb2.GetRoomRequestBody(
                roomId=room_id,
                did=did
            )
        )
        
        response = stub.Get(grpc_request)
        
        if response.body.status.code == 404:
            return jsonify({"error": "Room not found"}), 404
        elif response.body.status.code != 200:
            return jsonify({
                "error": response.body.status.message or "Failed to get room"
            }), response.body.status.code
        
        return jsonify({
            "status": 200,
            "message": "Room retrieved successfully",
            "data": MessageToDict(response.body.room)
        }), 200
        
    except grpc.RpcError as e:
        logger.error(f"gRPC error: {e}")
        return jsonify({"error": "gRPC service unavailable"}), 503
    except Exception as e:
        logger.error(f"Get room error: {str(e)}")
        return jsonify({"error": "Internal server error"}), 500

@app.route("/api/v1/rooms/<string:did>/<string:room_id>", methods=["PUT"])
def update_room(did, room_id):
    """更新面试间"""
    try:
        if not request.is_json:
            return jsonify({"error": "Request must be JSON"}), 400
        
        data = request.json
        
        # 构建更新请求体 - 根据测试文件，只包含基础字段
        update_body = room_pb2.UpdateRoomRequestBody(
            roomId=room_id,
            did=did
        )
        
        # 根据protobuf定义设置可选字段
        if "roomName" in data:
            update_body.roomName = data["roomName"]
        if "jobInfoId" in data:
            update_body.jobInfoId = data["jobInfoId"]
        if "contextId" in data:
            update_body.contextId = data["contextId"]
        if "experienceId" in data:
            update_body.experienceId = data["experienceId"]
        if "knowledgeId" in data:
            update_body.knowledgeId = data["knowledgeId"]
        
        grpc_request = room_pb2.UpdateRoomRequest(
            header=create_message_header(),
            body=update_body
        )
        
        response = stub.Update(grpc_request)
        
        if response.body.status.code == 404:
            return jsonify({"error": "Room not found"}), 404
        elif response.body.status.code != 200:
            return jsonify({
                "error": response.body.status.message or "Failed to update room"
            }), response.body.status.code
        
        return jsonify({
            "status": 200,
            "message": "Room updated successfully",
            "data": MessageToDict(response.body.room)
        }), 200
        
    except grpc.RpcError as e:
        logger.error(f"gRPC error: {e}")
        return jsonify({"error": "gRPC service unavailable"}), 503
    except Exception as e:
        logger.error(f"Update room error: {str(e)}")
        return jsonify({"error": "Internal server error"}), 500

@app.route("/api/v1/rooms/<string:did>/<string:room_id>", methods=["DELETE"])
def delete_room(did, room_id):
    """删除面试间"""
    try:
        grpc_request = room_pb2.DeleteRoomRequest(
            header=create_message_header(),
            body=room_pb2.DeleteRoomRequestBody(
                roomId=room_id,
                did=did
            )
        )
        
        response = stub.Delete(grpc_request)
        
        if response.body.status.code == 404:
            return jsonify({"error": "Room not found"}), 404
        elif response.body.status.code != 200:
            return jsonify({
                "error": response.body.status.message or "Failed to delete room"
            }), response.body.status.code
        
        return jsonify({
            "status": 200,
            "message": "Room deleted successfully"
        }), 200
        
    except grpc.RpcError as e:
        logger.error(f"gRPC error: {e}")
        return jsonify({"error": "gRPC service unavailable"}), 503
    except Exception as e:
        logger.error(f"Delete room error: {str(e)}")
        return jsonify({"error": "Internal server error"}), 500

@app.route("/api/v1/rooms", methods=["GET"])
def list_rooms():
    """获取面试间列表"""
    try:
        did = request.args.get("did")
        if not did:
            return jsonify({"error": "Missing required parameter: did"}), 400
        
        page = int(request.args.get("page", 1))
        page_size = int(request.args.get("pageSize", 10))
        
        # 验证分页参数
        if page < 1:
            page = 1
        if page_size < 1 or page_size > 100:
            page_size = 10
        
        grpc_request = room_pb2.ListRoomsRequest(
            header=create_message_header(),
            body=room_pb2.ListRoomsRequestBody(
                did=did,
                page=page,
                pageSize=page_size
            )
        )
        
        response = stub.List(grpc_request)
        
        if response.body.status.code != 200:
            return jsonify({
                "error": response.body.status.message or "Failed to list rooms"
            }), response.body.status.code
        
        return jsonify({
            "status": 200,
            "message": "Rooms retrieved successfully",
            "data": {
                "rooms": [MessageToDict(room) for room in response.body.rooms],
                "total": response.body.total,
                "page": response.body.page,
                "pageSize": response.body.pageSize
            }
        }), 200
        
    except ValueError as e:
        return jsonify({"error": "Invalid page or pageSize parameter"}), 400
    except grpc.RpcError as e:
        logger.error(f"gRPC error: {e}")
        return jsonify({"error": "gRPC service unavailable"}), 503
    except Exception as e:
        logger.error(f"List rooms error: {str(e)}")
        return jsonify({"error": "Internal server error"}), 500

@app.route("/health", methods=["GET"])
def health_check():
    """健康检查"""
    health_info = {
        "service": "http_gateway",
        "grpc_server": GRPC_SERVER,
        "status": "unknown"
    }
    
    try:
        if channel is None:
            health_info.update({
                "status": "unhealthy",
                "grpc_connection": "failed",
                "error": "No gRPC channel"
            })
            return jsonify(health_info), 503
        
        if stub is None:
            health_info.update({
                "status": "unhealthy",
                "grpc_connection": "connected",
                "grpc_stub": "failed",
                "error": "No gRPC stub"
            })
            return jsonify(health_info), 503
        
        # 简化的健康检查
        health_info.update({
            "status": "healthy",
            "grpc_connection": "ready",
            "grpc_stub": "available"
        })
        return jsonify(health_info), 200
        
    except Exception as e:
        logger.error(f"Health check failed: {str(e)}")
        health_info.update({
            "status": "unhealthy",
            "error": str(e)
        })
        return jsonify(health_info), 500

@app.route("/debug/grpc", methods=["GET"])
def debug_grpc():
    """gRPC调试信息"""
    debug_info = {
        "grpc_server": GRPC_SERVER,
        "channel_available": channel is not None,
        "stub_available": stub is not None,
        "room_pb2_grpc_attributes": [attr for attr in dir(room_pb2_grpc) if not attr.startswith('_')],
    }
    
    if channel:
        try:
            debug_info["channel_status"] = "created"
            future = grpc.channel_ready_future(channel)
            if future.done():
                debug_info["channel_ready"] = True
            else:
                debug_info["channel_ready"] = "pending"
        except Exception as e:
            debug_info["channel_error"] = str(e)
    
    return jsonify(debug_info)

# 错误处理器
@app.errorhandler(404)
def not_found(error):
    return jsonify({"error": "Endpoint not found"}), 404

@app.errorhandler(405)
def method_not_allowed(error):
    return jsonify({"error": "Method not allowed"}), 405

@app.errorhandler(500)
def internal_error(error):
    return jsonify({"error": "Internal server error"}), 500

if __name__ == "__main__":
    print("Starting Flask app on port 8080")
    app.run(host="0.0.0.0", port=8080, debug=True)