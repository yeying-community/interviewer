import argparse
import asyncio
import logging
import os
from concurrent import futures

import grpc
from google.protobuf import json_format

from interviewer.application.server.interceptor import SignatureInterceptor
from interviewer.application.server.room import RoomService
from interviewer.configs.config import Config
from interviewer.domain.mapper.entities import (
    UserDO, UserStateDO, ResumeDO, JobInfoDO, InterviewRoomDO,
    InterviewSessionDO, InterviewSessionRoundDO, InterviewReportDO, TaskDO
)  # 面试数据模型
from interviewer.domain.model.identity import verifyIdentity
from interviewer.infrastructure.db.instance import Instance, ensure_migrated
from interviewer.tool.authenticate import Authenticate
from interviewer.tool.crypto import decrypt, computeHash, decodeBase64, encodeString
from interviewer.tool.file import read
from interviewer.tool.object import safeGet
from yeying.api import web3
from yeying.api.web3 import BlockAddress
import yeying.api.interviewer.room_pb2_grpc as room_pb2_grpc


class Runner(object):

    def __init__(self, identity, blockAddress, config):
        self.identity = identity
        self.blockAddress = blockAddress
        self.config = config
        self.db_instance = Instance(self.config.get_database())
        self.server = None

    async def serve(self):
        self.server = grpc.aio.server(
            migration_thread_pool=futures.ThreadPoolExecutor(max_workers=100),
            interceptors=[SignatureInterceptor(identity=self.identity)],
            options=[
                ('grpc.keepalive_time_ms', 30000),
                ('grpc.keepalive_timeout_ms', 10000),
                ('grpc.keepalive_permit_without_calls', 1),
            ])

        db_instance = Instance(self.config.get_database())
        # 暂时没有业务服务，等后续实现

        server_config = self.config.get_server()

        if not os.path.exists(server_config.cacheDir):
            os.makedirs(server_config.cacheDir)

        authenticate = Authenticate(blockAddress=self.blockAddress)

        # 创建面试间服务
        room_service = RoomService(authenticate=authenticate, db_instance=db_instance)

        # 注册gRPC服务
        room_pb2_grpc.add_RoomServicer_to_server(room_service, self.server)

        endpoint = f'[::]:{server_config.port}'
        if self.config.get_credential().enable:
            logging.info('With credential.')
            self.server.add_secure_port(endpoint, self.createCredentials())
        else:
            logging.info('Without credential.')
            self.server.add_insecure_port(endpoint)

        await self.server.start()
        logging.info('The interviewer={} has been started successfully.'.format(endpoint))
        await self.server.wait_for_termination()

    def createCredentials(self):
        cert_dir = self.config.get_credential().certDir
        ca_path = os.path.join(cert_dir, 'ca.crt')

        if not os.path.exists(ca_path):
            logging.info('Not exist the ca path={}'.format(ca_path))
            with open(ca_path, 'w') as file:
                file.write(safeGet(self.identity, 'metadata', 'extend', 'ca'))
        ca = read(ca_path)

        cert_path = os.path.join(cert_dir, 'fullchain.pem')
        if not os.path.exists(cert_path):
            logging.info('Not exist the cert path={}'.format(cert_path))
            with open(cert_path, 'w') as file:
                file.write(safeGet(self.identity, 'metadata', 'extend', 'crt'))
        cert = read(cert_path)
        key = read(os.path.join(cert_dir, 'privkey.pem'))
        return grpc.ssl_server_credentials([(key, cert)], root_certificates=ca)


def parseArgs():
    parser = argparse.ArgumentParser(description='Loading interviewer service parameters.')
    parser.add_argument('--config', type=str, default='config/config.toml', help='Please set the interviewer service config.')
    parser.add_argument('--env', type=str, default='dev', help='Please set the runtime environment.')
    parser.add_argument('--debug', action='store_true', help='Set debug mode.')
    parser.add_argument('--port', type=str, default='0', help='Please set the port of interviewer service.')
    parser.add_argument('--identityFile', type=str, default='', help='Please set identity file for interviewer service.')
    parser.add_argument('--password', type=str, default='', help='Please input password to decrypted the identity file')
    parser.add_argument('--certDir', type=str, default='', help='Please set cert directory of interviewer service.')
    return parser.parse_args()


def deserializeIdentity(password, identity_file):
    key = computeHash(read(password))
    identity = web3.Identity()
    json_format.Parse(str(read(identity_file), 'utf-8'), identity)
    success = verifyIdentity(identity=identity)
    if not success:
        logging.error(f'The identity={identity} is invalid')
        return None

    nonce = decodeBase64(encodeString(identity.securityConfig.algorithm.iv))
    blockAddress = BlockAddress()
    blockAddress.ParseFromString(decrypt(key=key, nonce=nonce, b=decodeBase64(encodeString(identity.blockAddress))))
    return identity, blockAddress


def run(args):
    if args.debug:
        import pydevd
        pydevd.settrace('localhost', port=54321, stdoutToServer=True, stderrToServer=True, suspend=False)

    config = Config(args.config)
    config.configLog()
    if args.certDir != '':
        config.update_cert_dir(args.certDir)
    if args.port != 0:
        config.update_port(args.port)

    identity, blockAddress = deserializeIdentity(args.password, args.identityFile)
    if identity is None:
        return

    # 使用面试官的数据模型进行迁移
    ensure_migrated(config.get_database(), [
        UserDO, UserStateDO,           # 保留agent兼容的用户模型
        ResumeDO,                      # 简历表
        JobInfoDO,                     # 职位信息表
        InterviewRoomDO,               # 面试间表
        InterviewSessionDO,            # 面试会话表
        InterviewSessionRoundDO,       # 面试轮次表
        InterviewReportDO,             # 面试报告表
        TaskDO,                        # 任务表
    ])

    runner = Runner(identity=identity, blockAddress=blockAddress, config=config)
    asyncio.run(runner.serve())


if __name__ == '__main__':
    run(parseArgs())