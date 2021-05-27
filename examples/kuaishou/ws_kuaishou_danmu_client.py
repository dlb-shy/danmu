# -*- coding: utf-8 -*-
import json
import random
import re
import time
from pprint import pprint
from typing import Optional
from aiohttp import ClientSession
from loguru import logger

from danmu_abc import WsConn, Client
from examples.kuaishou.util import MessageDecode
import blackboxprotobuf

logger.add('runtime.log')
class WsDanmuClient(Client):
    def __init__(
            self, room: str, area_id: int, cookie: str,
            session: Optional[ClientSession] = None, loop=None):
        heartbeat = 20.0
        conn = WsConn(
            url='wss://live-ws-pg-group6.kuaishou.com/websocket',
            receive_timeout=heartbeat + 10,
            session=session)
        super().__init__(
            area_id=area_id,
            conn=conn,
            heartbeat=heartbeat,
            loop=loop)
        self._room = room
        self.headers = {

            'content-type': 'application/json',
            'Cookie': cookie,
            'Host': 'live.kuaishou.com',
            'Origin': 'https://live.kuaishou.com',
            'Referer': 'https://live.kuaishou.com/u/3xpqb3iy87d3nhi',
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/90.0.4430.212 Safari/537.36'
        }

    def get_page_id(self):
        charset = "-_zyxwvutsrqponmlkjihgfedcba9876543210ZYXWVUTSRQPONMLKJIHGFEDCBA"
        page_id = ''
        for _ in range(0, 16):
            page_id += random.choice(charset)
        page_id += "_"
        page_id += str(int(time.time() * 1000))
        return page_id

    async def _one_hello(self) -> bool:
        # 获取stream_id
        async with ClientSession() as session:
            async with session.get(f'https://live.kuaishou.com/u/{self._room}', headers=self.headers) as resp:
                room_page = await resp.text()
                # print(room_page)
                if '主播尚未开播' not in room_page:
                    stream_id = re.findall('live-stream-id="(.*?)"', room_page)[0]
                    print(stream_id)
                else:
                    stream_id = ''
                    logger.info('主播尚未开播')
        if stream_id:
            # 获取token
            token_url = 'https://live.kuaishou.com/live_graphql'
            payload = {"operationName":"WebSocketInfoQuery","variables":{"liveStreamId":stream_id},"query":"query WebSocketInfoQuery($liveStreamId: String) {\n  webSocketInfo(liveStreamId: $liveStreamId) {\n    token\n    webSocketUrls\n    __typename\n  }\n}\n"}
            async with ClientSession() as session:
                async with session.post(token_url, data=json.dumps(payload), headers=self.headers) as resp:
                    token_json = await resp.json()
                    token = token_json['data']['webSocketInfo']['token']

            part1 = [0x08, 0xC8, 0x01, 0x1A, 0xDC, 0x01, 0x0A, 0xAC, 0x01]  # 可能与版本有关
            part2 = [ord(c) for c in token]
            part3 = [0x12, 0x0B]
            part4 = [ord(c) for c in stream_id]
            part5 = [0x3A, 0x1E]
            page_id = self.get_page_id()
            part6 = [ord(c) for c in page_id]
            d = part1 + part2 + part3 + part4 + part5 + part6
            # print(bytes(d))

            return await self._conn.send_bytes(bytes(d))
        else:
            print('')

    async def _one_heartbeat(self) -> bool:
        head = [0x08, 0x01, 0x1A, 0x07, 0x08]
        timestamp = int(time.time() * 1000)
        time_arr = MessageDecode.hex_(timestamp)
        heartbeat = head + time_arr
        return await self._conn.send_bytes(bytes(heartbeat))

    async def _one_read(self) -> bool:
        pack = await self._conn.read_bytes()

        if pack is None:
            return False

        return self.handle_danmu(pack)

    def handle_danmu(self, pack):
        message, typedef = blackboxprotobuf.protobuf_to_json(pack)

        message = json.loads(message)
        try:
            if '3' in message.keys():
                if '5' in message['3'].keys():
                    reply_list = message['3']['5']
                    if type(reply_list) == list:
                        for reply in reply_list:

                            if '2' in reply.keys():
                                logger.info(reply["2"]["2"] + ': ' + reply["3"])
                    else:
                        logger.info(reply_list["2"]["2"] + ': ' + reply_list["3"])
        except Exception as e:
            pprint(message)
            print(e)

        return True

    async def reset_roomid(self, room):
        async with self._opening_lock:
            # not None是判断是否已经连接了的(重连过程中也可以处理)
            await self._conn.close()
            if self._task_main is not None:
                await self._task_main
            # 由于锁的存在，绝对不可能到达下一个的自动重连状态，这里是保证正确显示当前监控房间号
            self._room = room
            print(f'{self._area_id} 号数据连接已经切换房间（{room}）')
