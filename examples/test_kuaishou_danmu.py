import asyncio
import json
import re

from aiohttp import ClientSession

from examples.kuaishou.ws_kuaishou_danmu_client import WsDanmuClient

room_id = 'LYue19981010'
cookie = 'clientid=3; did=web_b6f8677f8da2be1b0d4676a94c935b71; client_key=65890b29; kpn=GAME_ZONE; didv=1621585129979; kuaishou.live.bfb1s=7206d814e5c089a58c910ed8bf52ace5; userId=1683867653; kuaishou.live.web_st=ChRrdWFpc2hvdS5saXZlLndlYi5zdBKgAccdwV-EgNNtBytfU-e_4D2GLBmQstApVfzEYZObngdb37QWUCurstRpXn0CLAzZtANXnJenVvbO0g_7swAy25-50bKP8gz46yP8XG119nB39RZjGbSJvYZ2P5-FugMHqKngbFtBh196BgTKAYLF2fn8A4l4HaKJcsBwMRrDJtebkIkaDMDsWni979Pi6e9oogqTJoinyFsr5wiqot9-pQIaEm-zwBmcbUA4lm5ejQnh9kVjySIgXfCFdLloc771UsS6muRv9g3Xn87unJ2IQ3HJRIO3c1ooBTAB; kuaishou.live.web_ph=239ae61502cb7c46986862da49d9a51d1bb6; userId=1683867653'
area_id = 0
headers = {

    'content-type': 'application/json',
    'Cookie': cookie,
    'Host': 'live.kuaishou.com',
    'Origin': 'https://live.kuaishou.com',
    'Referer': 'https://live.kuaishou.com/u/3xpqb3iy87d3nhi',
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/90.0.4430.212 Safari/537.36',

}


async def test_danmu_client(client):
    # 获取stream_id
    async with ClientSession() as session:
        async with session.get(f'https://live.kuaishou.com/u/{room_id}', headers=headers) as resp:
            room_page = await resp.text()
            stream_id = re.findall('live-stream-id="(.*?)"', room_page)[0]
    # 获取token
    token_url = 'https://live.kuaishou.com/live_graphql'
    payload = {"operationName": "WebSocketInfoQuery", "variables": {"liveStreamId": stream_id},
               "query": "query WebSocketInfoQuery($liveStreamId: String) {\n  webSocketInfo(liveStreamId: $liveStreamId) {\n    token\n    webSocketUrls\n    __typename\n  }\n}\n"}
    async with ClientSession() as session:
        async with session.post(token_url, data=json.dumps(payload), headers=headers) as resp:
            token_json = await resp.json()
            token = token_json['data']['webSocketInfo']['token']
            url = token_json['data']['webSocketInfo']['webSocketUrls'][0]
    connection = client(room=room_id, area_id=area_id, url=url, token=token, stream_id=stream_id)
    asyncio.ensure_future(connection.run_forever())
    await asyncio.sleep(2000)
    # await connection.reset_roomid(952595)
    print('RESTED')
    connection.pause()
    await asyncio.sleep(200)
    print('resume')
    connection.resume()
    await asyncio.sleep(20)
    print('close')
    await connection.close()
    print('END')


async def test_tcp_danmu_client():
    await test_danmu_client(0)


async def test_ws_danmu_client():
    await test_danmu_client(WsDanmuClient)


loop = asyncio.new_event_loop()
asyncio.set_event_loop(loop)
loop.run_until_complete(test_ws_danmu_client())
loop.close()
