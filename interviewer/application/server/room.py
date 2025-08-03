"""
面试间gRPC服务实现
文件：interviewer/application/server/room.py
"""

from __future__ import annotations

import logging
from typing import Optional, List, Tuple

import yeying.api.interviewer.room_pb2 as room_pb2
import yeying.api.common.message_pb2 as message_pb2
from interviewer.domain.model.room import Room
from interviewer.infrastructure.repository.room_repository import RoomRepository
from interviewer.infrastructure.db.instance import Instance
from interviewer.application.model.room_dto import (
    convertRoomFrom, convertRoomTo, convertRoomListFrom,
    createResponseStatus
)
from interviewer.tool.date import getCurrentUtcString

logger = logging.getLogger(__name__)


class RoomService:
    """面试间服务"""

    def __init__(self, authenticate, db_instance: Instance):
        self.authenticate = authenticate
        self.repository = RoomRepository(db_instance)

    # ========== gRPC接口实现 ==========

    def Create(self, request: room_pb2.CreateRoomRequest, context) -> room_pb2.CreateRoomResponse:
        """创建面试间"""
        try:
            # 转换为领域模型
            room = convertRoomTo(request.body.room)

            # 业务验证
            room.validate()

            # 设置时间戳
            current_time = getCurrentUtcString()
            room.createdAt = current_time
            room.updatedAt = current_time

            # 保存到数据库
            self.repository.add(room)

            # 返回响应
            return room_pb2.CreateRoomResponse(
                header=request.header,
                body=room_pb2.CreateRoomResponseBody(
                    status=createResponseStatus(200, "创建成功"),
                    room=convertRoomFrom(room)
                )
            )

        except ValueError as e:
            logger.warning(f"创建面试间参数错误: {str(e)}")
            return room_pb2.CreateRoomResponse(
                header=request.header,
                body=room_pb2.CreateRoomResponseBody(
                    status=createResponseStatus(400, f"参数错误: {str(e)}")
                )
            )
        except Exception as e:
            logger.error(f"创建面试间失败: {str(e)}")
            return room_pb2.CreateRoomResponse(
                header=request.header,
                body=room_pb2.CreateRoomResponseBody(
                    status=createResponseStatus(500, "内部服务错误")
                )
            )

    def Get(self, request: room_pb2.GetRoomRequest, context) -> room_pb2.GetRoomResponse:
        """获取面试间"""
        try:
            room = self.repository.get_by_id(request.body.did, request.body.roomId)

            if room is None:
                return room_pb2.GetRoomResponse(
                    header=request.header,
                    body=room_pb2.GetRoomResponseBody(
                        status=createResponseStatus(404, "面试间不存在")
                    )
                )

            return room_pb2.GetRoomResponse(
                header=request.header,
                body=room_pb2.GetRoomResponseBody(
                    status=createResponseStatus(200, "获取成功"),
                    room=convertRoomFrom(room)
                )
            )

        except Exception as e:
            logger.error(f"获取面试间失败: {str(e)}")
            return room_pb2.GetRoomResponse(
                header=request.header,
                body=room_pb2.GetRoomResponseBody(
                    status=createResponseStatus(500, "内部服务错误")
                )
            )

    def Update(self, request: room_pb2.UpdateRoomRequest, context) -> room_pb2.UpdateRoomResponse:
        """更新面试间（只允许修改房间名称）"""
        try:
            # 先获取现有房间
            existing_room = self.repository.get_by_id(request.body.did, request.body.roomId)
            if existing_room is None:
                return room_pb2.UpdateRoomResponse(
                    header=request.header,
                    body=room_pb2.UpdateRoomResponseBody(
                        status=createResponseStatus(404, "面试间不存在")
                    )
                )

            # 只更新房间名称
            existing_room.roomName = request.body.roomName
            existing_room.updatedAt = getCurrentUtcString()

            # 验证更新后的数据
            existing_room.validate()

            # 保存更新
            self.repository.update(existing_room)

            return room_pb2.UpdateRoomResponse(
                header=request.header,
                body=room_pb2.UpdateRoomResponseBody(
                    status=createResponseStatus(200, "更新成功"),
                    room=convertRoomFrom(existing_room)
                )
            )

        except ValueError as e:
            logger.warning(f"更新面试间参数错误: {str(e)}")
            return room_pb2.UpdateRoomResponse(
                header=request.header,
                body=room_pb2.UpdateRoomResponseBody(
                    status=createResponseStatus(400, f"参数错误: {str(e)}")
                )
            )
        except Exception as e:
            logger.error(f"更新面试间失败: {str(e)}")
            return room_pb2.UpdateRoomResponse(
                header=request.header,
                body=room_pb2.UpdateRoomResponseBody(
                    status=createResponseStatus(500, "内部服务错误")
                )
            )

    def Delete(self, request: room_pb2.DeleteRoomRequest, context) -> room_pb2.DeleteRoomResponse:
        """删除面试间"""
        try:
            success = self.repository.delete(request.body.did, request.body.roomId)

            if not success:
                return room_pb2.DeleteRoomResponse(
                    header=request.header,
                    body=room_pb2.DeleteRoomResponseBody(
                        status=createResponseStatus(404, "面试间不存在")
                    )
                )

            return room_pb2.DeleteRoomResponse(
                header=request.header,
                body=room_pb2.DeleteRoomResponseBody(
                    status=createResponseStatus(200, "删除成功")
                )
            )

        except Exception as e:
            logger.error(f"删除面试间失败: {str(e)}")
            return room_pb2.DeleteRoomResponse(
                header=request.header,
                body=room_pb2.DeleteRoomResponseBody(
                    status=createResponseStatus(500, "内部服务错误")
                )
            )

    def List(self, request: room_pb2.ListRoomsRequest, context) -> room_pb2.ListRoomsResponse:
        """列出面试间"""
        try:
            page = max(1, request.body.page)  # 页码最小为1
            page_size = max(1, min(100, request.body.pageSize))  # 限制页面大小

            rooms, total = self.repository.list_by_did(request.body.did, page, page_size)

            return room_pb2.ListRoomsResponse(
                header=request.header,
                body=room_pb2.ListRoomsResponseBody(
                    status=createResponseStatus(200, "获取成功"),
                    rooms=convertRoomListFrom(rooms),
                    total=total,
                    page=page,
                    pageSize=page_size
                )
            )

        except Exception as e:
            logger.error(f"列出面试间失败: {str(e)}")
            return room_pb2.ListRoomsResponse(
                header=request.header,
                body=room_pb2.ListRoomsResponseBody(
                    status=createResponseStatus(500, "内部服务错误"),
                    rooms=[],
                    total=0,
                    page=1,
                    pageSize=10
                )
            )

    # ========== 测试辅助方法 ==========
    
    def addRoom(self, room: Room) -> None:
        """添加面试间 (测试辅助方法)"""
        self.repository.add(room)

    def getRoom(self, did: str, room_id: str) -> Optional[Room]:
        """获取面试间 (测试辅助方法)"""
        return self.repository.get_by_id(did, room_id)

    def getRoomsByDid(self, did: str) -> List[Room]:
        """获取用户所有面试间 (测试辅助方法)"""
        return self.repository.get_by_did(did)

    def deleteRoom(self, did: str, room_id: str) -> bool:
        """删除面试间 (测试辅助方法)"""
        return self.repository.delete(did, room_id)