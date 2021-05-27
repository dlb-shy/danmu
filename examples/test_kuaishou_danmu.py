import asyncio

from examples.kuaishou.ws_kuaishou_danmu_client import WsDanmuClient

room_id = '3x5tr2y938qzhx2'
cookie = ''
area_id = 0


async def test_danmu_client(client):
    connection = client(room_id, area_id, cookie)
    asyncio.ensure_future(connection.run_forever())
    await asyncio.sleep(2000)
    await connection.reset_roomid(952595)
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
