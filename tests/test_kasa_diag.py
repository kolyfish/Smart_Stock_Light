import asyncio
from kasa import Discover, SmartPlug
import sys

async def test_kasa():
    print("🔍 正在掃描網路中的 Kasa 設備...")
    devices = await Discover.discover()
    if not devices:
        print("❌ 未找到任何 Kasa 設備。請確認設備已開啟且在同一 Wi-Fi。")
        return

    for ip, dev in devices.items():
        print(f"✅ 找到設備: {dev.alias} ({dev.model}) at {ip}")
        if "HS103" in dev.model or "Plug" in dev.model:
            print(f"🚀 嘗試切換 {ip} 的開關狀態...")
            try:
                p = SmartPlug(ip)
                await p.update()
                if p.is_on:
                    print("💡 目前狀態為 [開啟]，正在關閉...")
                    await p.turn_off()
                else:
                    print("💡 目前狀態為 [關閉]，正在開啟...")
                    await p.turn_on()
                print("✨ 操作成功！")
            except Exception as e:
                print(f"💥 操作失敗: {e}")

if __name__ == "__main__":
    asyncio.run(test_kasa())
