import asyncio
from plugp100.common.credentials import AuthCredential
from plugp100.new.device_factory import connect, DeviceConnectConfiguration

class TapoController:
    def __init__(self):
        # 使用者提供的憑據
        self.username = "kolyfish2@gmail.com"
        self.password = "WWuu0921"
        self.ip_address = "192.168.100.150"
        
        # 使用 v5.x 推薦的連線配置
        self.credentials = AuthCredential(self.username, self.password)
        self.config = DeviceConnectConfiguration(
            host=self.ip_address,
            credentials=self.credentials,
            device_type="SMART.TAPOBULB"
        )
        self.device = None

    async def _ensure_connected(self):
        """確保裝置已連線且協定已協商。"""
        try:
            if self.device is None:
                print(f"[{self.ip_address}] 正在初始化連線 (自動協商協定)...")
                self.device = await connect(self.config)
                print(f"[{self.ip_address}] 連線實體已建立。")

            # 關鍵修正：檢查 _protocol 是否為類別而非實例
            client = self.device.client
            # 獲取實際的協定物件 (檢查其是否可調用 send_request 且非類別)
            import inspect
            if inspect.isclass(client.protocol) or client.protocol is None:
                print(f"[{self.ip_address}] 偵測到協定類型錯誤 ({type(client.protocol)})，正在手動初始化 KlapProtocol...")
                from plugp100.protocol.klap import klap_handshake_v2
                from plugp100.protocol.klap.klap_protocol import KlapProtocol
                
                # 手動建立協定實例
                protocol = KlapProtocol(
                    auth_credential=self.credentials,
                    url=f"http://{self.ip_address}/app",
                    klap_strategy=klap_handshake_v2()
                )
                # 注入實例
                client._protocol = protocol
                print(f"[{self.ip_address}] 協定實例已重置。")

            await self.device.update()
            # print(f"[{self.ip_address}] 裝置狀態已更新。")
        except Exception as e:
            print(f"[{self.ip_address}] 連線或初始化失敗: {e}")
            self.device = None # 重設以便下次重連
            raise e

    async def _set_brightness(self, level: int):
        """設定燈泡亮度 (1-100)。"""
        try:
            await self._ensure_connected()
            await self.device.set_brightness(level)
        except Exception as e:
            print(f"[{self.ip_address}] 設定亮度失敗: {e}")

    async def _set_color_hs(self, hue: int, saturation: int):
        """設定彩色燈泡顏色 (色相/飽和度)。"""
        try:
            await self._ensure_connected()
            color_name = "綠色" if hue==120 else ("黃色" if hue==60 else "紅色")
            print(f"[{self.ip_address}] 正在切換顏色為: {color_name}")
            
            # 更新狀態並開啟
            await self.device.update()
            await self.device.turn_on()
            
            # 設定顏色 (Hue: 0-360, Saturation: 0-100)
            result = await self.device.set_hue_saturation(hue, saturation)
            if result.is_failure():
                from plugp100.new.components.light_component import LightComponent
                await self.device.get_component(LightComponent).set_hue_saturation(hue, saturation)
                
            print(f"[{self.ip_address}] 顏色切換成功 ({color_name})。")
        except Exception as e:
            print(f"[{self.ip_address}] 操控失敗: {e}")

    async def _test_sequence(self):
        """執行一鍵測試序列：漸暗 -> 關閉 -> 變色迴圈 -> 回歸黃色。"""
        try:
            await self._ensure_connected()
            print("開始執行燈光測試序列...")
            
            # 1. 漸暗效果
            for b in [70, 40, 10]:
                await self.device.set_brightness(b)
                await asyncio.sleep(0.3)
            
            # 2. 暫時關閉
            await self.device.turn_off()
            await asyncio.sleep(0.5)
            
            # 3. 變色開啟
            await self.device.turn_on()
            # 快速紅綠黃切換
            for h in [0, 120, 60]:
                await self.device.set_hue_saturation(h, 100)
                await self.device.set_brightness(100)
                await asyncio.sleep(0.6)
            
            print("測試序列執行完畢。")
        except Exception as e:
            print(f"測試序列出錯: {e}")

    def turn_on_green(self):
        """觸發警報：轉為綠色。"""
        asyncio.run(self._set_color_hs(120, 100))

    def turn_on_red(self):
        """監控中：轉為紅色。"""
        asyncio.run(self._set_color_hs(0, 100))

    def turn_on_yellow(self):
        """常態/待機：轉為黃色。"""
        asyncio.run(self._set_color_hs(60, 100))

    def run_test_sequence(self):
        """執行完整測試序列。"""
        asyncio.run(self._test_sequence())

    async def _turn_off(self):
        """關閉裝置。"""
        try:
            await self._ensure_connected()
            print(f"[{self.ip_address}] Web 請求：正在執行關閉指令...")
            await self.device.update()
            await self.device.turn_off()
            print(f"[{self.ip_address}] 裝置已成功關閉。")
        except Exception as e:
            print(f"[{self.ip_address}] 關閉執行失敗: {e}")

    def turn_off(self):
        """手動關閉。"""
        asyncio.run(self._turn_off())

if __name__ == "__main__":
    controller = TapoController()
    print("測試紅燈...")
    controller.turn_on_red()
    import time
    time.sleep(3)
    print("測試關閉...")
    controller.turn_off()
