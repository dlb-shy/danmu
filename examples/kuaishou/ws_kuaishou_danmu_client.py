# -*- coding: utf-8 -*-
import json
import random
import re
import time
from pprint import pprint
from typing import Optional
from aiohttp import ClientSession

from danmu_abc import WsConn, Client
from examples.kuaishou.util import MessageDecode
import blackboxprotobuf


class WsDanmuClient(Client):
    def __init__(
            self, room: str, area_id: int, url: str, token: str,stream_id:str,
            session: Optional[ClientSession] = None, loop=None):
        heartbeat = 20.0

        conn = WsConn(
            url=url,
            receive_timeout=heartbeat + 10,
            session=session)
        super().__init__(
            area_id=area_id,
            conn=conn,
            heartbeat=heartbeat,
            loop=loop)
        self._room = room
        self.token = token
        self.stream_id = stream_id

    def get_page_id(self):
        charset = "-_zyxwvutsrqponmlkjihgfedcba9876543210ZYXWVUTSRQPONMLKJIHGFEDCBA"
        page_id = ''
        for _ in range(0, 16):
            page_id += random.choice(charset)
        page_id += "_"
        page_id += str(int(time.time() * 1000))
        return page_id

    async def _one_hello(self) -> bool:

        part1 = [0x08, 0xC8, 0x01, 0x1A, 0xDC, 0x01, 0x0A, 0xAC, 0x01]  # 可能与版本有关
        part2 = [ord(c) for c in self.token]
        part3 = [0x12, 0x0B]
        part4 = [ord(c) for c in self.stream_id]
        part5 = [0x3A, 0x1E]
        page_id = self.get_page_id()
        part6 = [ord(c) for c in page_id]
        d = part1 + part2 + part3 + part4 + part5 + part6
        # print(bytes(d))

        return await self._conn.send_bytes(bytes(d))

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
                                print(reply["2"]["2"] + ': ' + reply["3"])
                    else:
                        print(reply_list["2"]["2"] + ': ' + reply_list["3"])
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
