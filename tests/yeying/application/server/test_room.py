"""
面试间服务单元测试
测试文件：tests/yeying/application/server/test_room.py
"""

import unittest
import uuid

import yeying.api.interviewer.room_pb2 as room_pb2
import yeying.api.common.message_pb2 as message_pb2
from interviewer.application.server.room import RoomService
from interviewer.domain.mapper.entities import InterviewRoomDO
from interviewer.infrastructure.db.instance import Instance
from interviewer.tool.date import getCurrentUtcString
from tests.yeying.common.test_config import setup_test_database, setup_test_logging


class RoomServiceTestCase(unittest.TestCase):
    instance = Instance(setup_test_database([InterviewRoomDO]))

    @classmethod
    def setUpClass(cls):
        setup_test_logging()

    def setUp(self):
        """每个测试前的初始化"""
        self.room_service = RoomService(authenticate=None, db_instance=self.instance)

    def test_grpc_create_room(self):
        """测试创建面试间"""
        did = "did:example:create-test"
        room_id = str(uuid.uuid4())
        
        self.room_service.deleteRoom(did=did, room_id=room_id)  # 预清理
        
        # 创建房间
        room_metadata = room_pb2.RoomMetadata(
            roomId=room_id,
            did=did,
            roomName="Python面试间",
            resumeId="resume-001",
            jobInfoId="job-001",
            contextId="context-001",
            experienceId="experience-001",
            knowledgeId="knowledge-001",
            createdAt=getCurrentUtcString(),
            updatedAt=getCurrentUtcString(),
            signature="signature"
        )
        create_request = room_pb2.CreateRoomRequest(
            header=message_pb2.MessageHeader(),
            body=room_pb2.CreateRoomRequestBody(room=room_metadata)
        )
        
        create_response = self.room_service.Create(create_request, None)
        self.assertEqual(create_response.body.status.code, 200)
        self.assertEqual(create_response.body.room.roomName, "Python面试间")
        self.assertEqual(create_response.body.room.jobInfoId, "job-001")
        
        self.room_service.deleteRoom(did=did, room_id=room_id)  # 后清理

    def test_grpc_get_room(self):
        """测试获取面试间"""
        did = "did:example:get-test"
        room_id = str(uuid.uuid4())
        
        self.room_service.deleteRoom(did=did, room_id=room_id)  # 预清理
        
        # 先创建房间
        room_metadata = room_pb2.RoomMetadata(
            roomId=room_id,
            did=did,
            roomName="测试获取房间",
            resumeId="resume-001",
            jobInfoId="job-001",
            contextId="context-001",
            experienceId="experience-001",
            knowledgeId="knowledge-001",
            createdAt=getCurrentUtcString(),
            updatedAt=getCurrentUtcString(),
            signature="signature"
        )
        create_request = room_pb2.CreateRoomRequest(
            header=message_pb2.MessageHeader(),
            body=room_pb2.CreateRoomRequestBody(room=room_metadata)
        )
        self.room_service.Create(create_request, None)
        
        # 测试获取
        get_request = room_pb2.GetRoomRequest(
            header=message_pb2.MessageHeader(),
            body=room_pb2.GetRoomRequestBody(roomId=room_id, did=did)
        )
        
        get_response = self.room_service.Get(get_request, None)
        self.assertEqual(get_response.body.status.code, 200)
        self.assertEqual(get_response.body.room.roomId, room_id)
        self.assertEqual(get_response.body.room.roomName, "测试获取房间")
        
        self.room_service.deleteRoom(did=did, room_id=room_id)  # 后清理

    def test_grpc_get_room_not_found(self):
        """测试获取不存在的面试间"""
        did = "did:example:not-found-test"
        room_id = str(uuid.uuid4())
        
        get_request = room_pb2.GetRoomRequest(
            header=message_pb2.MessageHeader(),
            body=room_pb2.GetRoomRequestBody(roomId=room_id, did=did)
        )
        
        get_response = self.room_service.Get(get_request, None)
        self.assertEqual(get_response.body.status.code, 404)

    def test_grpc_update_room(self):
        """测试更新面试间"""
        did = "did:example:update-test"
        room_id = str(uuid.uuid4())
        
        self.room_service.deleteRoom(did=did, room_id=room_id)  # 预清理
        
        # 先创建房间
        room_metadata = room_pb2.RoomMetadata(
            roomId=room_id,
            did=did,
            roomName="原始房间名",
            resumeId="resume-001",
            jobInfoId="job-001",
            contextId="context-001",
            experienceId="experience-001",
            knowledgeId="knowledge-001",
            createdAt=getCurrentUtcString(),
            updatedAt=getCurrentUtcString(),
            signature="signature"
        )
        create_request = room_pb2.CreateRoomRequest(
            header=message_pb2.MessageHeader(),
            body=room_pb2.CreateRoomRequestBody(room=room_metadata)
        )
        self.room_service.Create(create_request, None)
        
        # 测试更新
        update_request = room_pb2.UpdateRoomRequest(
            header=message_pb2.MessageHeader(),
            body=room_pb2.UpdateRoomRequestBody(
                roomId=room_id,
                did=did,
                roomName="更新后的房间名"
            )
        )
        
        update_response = self.room_service.Update(update_request, None)
        self.assertEqual(update_response.body.status.code, 200)
        self.assertEqual(update_response.body.room.roomName, "更新后的房间名")
        # 其他字段应该保持不变
        self.assertEqual(update_response.body.room.jobInfoId, "job-001")
        self.assertEqual(update_response.body.room.contextId, "context-001")
        
        self.room_service.deleteRoom(did=did, room_id=room_id)  # 后清理

    def test_grpc_update_room_not_found(self):
        """测试更新不存在的面试间"""
        did = "did:example:update-not-found-test"
        room_id = str(uuid.uuid4())
        
        update_request = room_pb2.UpdateRoomRequest(
            header=message_pb2.MessageHeader(),
            body=room_pb2.UpdateRoomRequestBody(
                roomId=room_id,
                did=did,
                roomName="不存在的房间"
            )
        )
        
        update_response = self.room_service.Update(update_request, None)
        self.assertEqual(update_response.body.status.code, 404)

    def test_grpc_delete_room(self):
        """测试删除面试间"""
        did = "did:example:delete-test"
        room_id = str(uuid.uuid4())
        
        self.room_service.deleteRoom(did=did, room_id=room_id)  # 预清理
        
        # 先创建房间
        room_metadata = room_pb2.RoomMetadata(
            roomId=room_id,
            did=did,
            roomName="待删除房间",
            resumeId="resume-001",
            jobInfoId="job-001",
            contextId="context-001",
            experienceId="experience-001",
            knowledgeId="knowledge-001",
            createdAt=getCurrentUtcString(),
            updatedAt=getCurrentUtcString(),
            signature="signature"
        )
        create_request = room_pb2.CreateRoomRequest(
            header=message_pb2.MessageHeader(),
            body=room_pb2.CreateRoomRequestBody(room=room_metadata)
        )
        self.room_service.Create(create_request, None)
        
        # 测试删除
        delete_request = room_pb2.DeleteRoomRequest(
            header=message_pb2.MessageHeader(),
            body=room_pb2.DeleteRoomRequestBody(roomId=room_id, did=did)
        )
        
        delete_response = self.room_service.Delete(delete_request, None)
        self.assertEqual(delete_response.body.status.code, 200)
        
        # 验证确实被删除了
        get_request = room_pb2.GetRoomRequest(
            header=message_pb2.MessageHeader(),
            body=room_pb2.GetRoomRequestBody(roomId=room_id, did=did)
        )
        get_response = self.room_service.Get(get_request, None)
        self.assertEqual(get_response.body.status.code, 404)

    def test_grpc_delete_room_not_found(self):
        """测试删除不存在的面试间"""
        did = "did:example:delete-not-found-test"
        room_id = str(uuid.uuid4())
        
        delete_request = room_pb2.DeleteRoomRequest(
            header=message_pb2.MessageHeader(),
            body=room_pb2.DeleteRoomRequestBody(roomId=room_id, did=did)
        )
        
        delete_response = self.room_service.Delete(delete_request, None)
        self.assertEqual(delete_response.body.status.code, 404)

    def test_grpc_list_rooms(self):
        """测试列表面试间"""
        did = "did:example:list-test"
        
        # 清理可能存在的测试数据
        existing_rooms = self.room_service.getRoomsByDid(did)
        for room in existing_rooms:
            self.room_service.deleteRoom(did, room.roomId)
        
        # 创建3个房间用于测试
        room_ids = []
        for i in range(3):
            room_id = str(uuid.uuid4())
            room_ids.append(room_id)
            
            room_metadata = room_pb2.RoomMetadata(
                roomId=room_id,
                did=did,
                roomName=f"测试房间{i+1}",
                resumeId="resume-001",
                jobInfoId="job-001",
                contextId="context-001",
                experienceId="experience-001",
                knowledgeId="knowledge-001",
                createdAt=getCurrentUtcString(),
                updatedAt=getCurrentUtcString(),
                signature="signature"
            )
            create_request = room_pb2.CreateRoomRequest(
                header=message_pb2.MessageHeader(),
                body=room_pb2.CreateRoomRequestBody(room=room_metadata)
            )
            self.room_service.Create(create_request, None)
        
        # 测试列表（第一页，每页2个）
        list_request = room_pb2.ListRoomsRequest(
            header=message_pb2.MessageHeader(),
            body=room_pb2.ListRoomsRequestBody(did=did, page=1, pageSize=2)
        )
        
        list_response = self.room_service.List(list_request, None)
        self.assertEqual(list_response.body.status.code, 200)
        self.assertEqual(len(list_response.body.rooms), 2)
        self.assertEqual(list_response.body.total, 3)
        self.assertEqual(list_response.body.page, 1)
        self.assertEqual(list_response.body.pageSize, 2)
        
        # 测试第二页
        list_request.body.page = 2
        list_response = self.room_service.List(list_request, None)
        self.assertEqual(list_response.body.status.code, 200)
        self.assertEqual(len(list_response.body.rooms), 1)
        self.assertEqual(list_response.body.total, 3)
        
        # 清理
        for room_id in room_ids:
            self.room_service.deleteRoom(did, room_id)


if __name__ == '__main__':
    unittest.main()