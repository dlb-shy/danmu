import asyncio

from examples.kuaishou.ws_kuaishou_danmu_client import WsDanmuClient

room_id = 'qiming188'
cookie = 'kuaishou.live.bfb1s=9b8f70844293bed778aade6e0a8f9942; clientid=3; did=web_b6f8677f8da2be1b0d4676a94c935b71; client_key=65890b29; kpn=GAME_ZONE; didv=1621585129979; userId=1683867653; userId=1683867653; kuaishou.live.web_st=ChRrdWFpc2hvdS5saXZlLndlYi5zdBKgAa3fL0oe9btghG0h13myuNfJhdg6kaIQEd8MK3yYWZ9YubmPry75nmVV5IbM2LCHHJMyiq6ZEHP4a0VTQiSrXjyYxpZ94q-kp2utBUMuQd5KeU_upDMuHCW8ujjGGlYHSv7nBGMrvhWdfU-8IiLFIMoFQQRpbxuo1mNbU2sXVw9Cr2iAc9Pg4WS5pebrcEX9JNhfBPHlARsxNpLnDCphqZ4aEurKvNghXkU0vIm_W_UXPUfuwSIgbBoJfmFoSldBiQLUySuekh_XB7FU7kHwfKv3DRbEIh4oBTAB; kuaishou.live.web_ph=a1c15df05aa2bf92e41cf50bd1a96563db2e'
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
