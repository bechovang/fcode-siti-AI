"""Test Tìm Nắng: vision judge + WS flow (master start → scoreboard, station nhận round)."""
import sys, os, io, base64, asyncio, json
sys.stdout.reconfigure(encoding="utf-8")  # Windows console mặc định cp1252 → crash khi in tiếng Việt
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
import websockets
from PIL import Image

# ---- Vision test (ảnh mẫu) ----
import timnang_master as M
from timnang_data import OBJECTS

async def vision_test():
    # ảnh 1: vàng-xanh (hơi giống bóng tennis) — object ball
    img1 = Image.new("RGB", (320, 320), (210, 235, 70))
    buf = io.BytesIO(); img1.save(buf, "JPEG", quality=70)
    b64_1 = base64.b64encode(buf.getvalue()).decode()
    # ảnh 2: đỏ (không phải bóng tennis)
    img2 = Image.new("RGB", (320, 320), (220, 40, 40))
    buf2 = io.BytesIO(); img2.save(buf2, "JPEG", quality=70)
    b64_2 = base64.b64encode(buf2.getvalue()).decode()
    print("=== VISION TEST (object = bóng tennis) ===")
    r1 = await M.judge_vision(b64_1, OBJECTS[0])
    r2 = await M.judge_vision(b64_2, OBJECTS[0])
    print(f"  ảnh vàng-xanh (gần bóng): {r1}  (False OK — ảnh rỗng, quan trọng API trả bool)")
    print(f"  ảnh đỏ               : {r2}")
    print(f"  API works: {r1 is not None or r2 is not None}")

async def ws_test():
    print("\n=== WS FLOW TEST ===")
    m = await websockets.connect("ws://127.0.0.1:8001/ws/master")
    await m.send(json.dumps({"type": "op", "action": "start"}))
    got_playing = False
    for _ in range(8):
        try:
            msg = json.loads(await asyncio.wait_for(m.recv(), timeout=20))
        except asyncio.TimeoutError:
            break
        if msg.get("type") == "scoreboard":
            print(f"  master scoreboard: phase={msg['phase']} round={msg['round']} object={msg.get('object')}")
            if msg["phase"] == "playing": got_playing = True; break
    print(f"  master nhận phase playing: {got_playing}")
    # station
    s = await websockets.connect("ws://127.0.0.1:8001/ws/station/A")
    first = json.loads(await asyncio.wait_for(s.recv(), timeout=10))
    print(f"  station A nhận: type={first.get('type')} object={first.get('object')}")

    # ---- recognize round-trip: gửi ảnh mẫu (gần đen), chờ kết quả chấm ----
    img = Image.new("RGB", (120, 120), (10, 10, 10))
    buf = io.BytesIO(); img.save(buf, "JPEG", quality=70)
    sample = "data:image/jpeg;base64," + base64.b64encode(buf.getvalue()).decode()
    await s.send(json.dumps({"type": "recognize", "image": sample}))
    got_result = None
    for _ in range(8):
        try:
            rmsg = json.loads(await asyncio.wait_for(s.recv(), timeout=20))
        except asyncio.TimeoutError:
            break
        if rmsg.get("type") == "result":
            got_result = rmsg
            break
    if got_result:
        print(f"  station A result: correct={got_result.get('correct')} msg={got_result.get('msg')}")
    else:
        print("  station A: KHÔNG nhận được result (timeout)")

    await m.send(json.dumps({"type": "op", "action": "restart"}))
    await asyncio.sleep(0.5)
    await m.close(); await s.close()

async def main():
    await vision_test()
    await ws_test()

asyncio.run(main())
