# 開發者設計精華日誌 (Developer Design Log)

## 🎯 專案定位：SmartStockLight (User Version)
本專案為面向一般投資者的智慧硬體監控系統，核心目標是「穩定、美觀、易用」。不同於「指揮官版本 (BUMP Version)」，此版本不包含中央集權控制邏輯，純粹服務於使用者個人的投資監測需求。

## 🏗️ 軟體架構 (Software Architecture)

### 1. 混合式數據引擎 (Hybrid Data Engine)
- **架構描述**: 採用實時與輪詢結合的策略。
- **設計決策**: 
    - 虛擬貨幣使用高頻輪詢 (或 Websocket 橋接)，達成 0.5s - 1s 的響應速度。
    - 股票使用 REST API 輪詢，維持 10s 間隔以避免被 Rate Limit。
- **架構師提示**: 若要重新設計，應引入更完善的 Websocket 服務器，將數據抓取與前端推送完全解耦。

### 2. 跨裝置控制層 (Hardware Abstraction Layer)
- **核心設計**: `TapoController` 被設計為一個抽象層，封裝了 Klap 協議與裝置差異。
- **支援設備**:
    - **彩色燈泡**: TP-Link Tapo L530 系列。
    - **智慧插座**: **TP-Link Kasa Mini HS103** (已實測驗證)。
- **最新演進 (2025-12-29)**: 
    - 引入了 `device_type` (bulb/plug) 的動態切換。
    - **燈泡模式**: 支援 HSL 顏色切換 (紅/綠/黃/紫)。
    - **插座模式**: 映射顏色指令至開關行為 (警報=開, 待機=關)，讓投資者可以外接警報器或大功率燈俱。
- **雙裝置獨立控制 (2025-12-30)**:
    - **設計決策**: 將 Bulb 與 Plug 的 IP 配置完全解耦。
    - **核心實作**: `SharedConfig` 拆分為 `bulb_ip` 與 `plug_ip`；`TapoController` 根據動作目標自動選擇對應 IP。
    - **UI 優化**: 前端改為雙 IP 輸入與獨立掃描，解決了同時擁有燈泡與插座時的控制衝突。

### 3. 多線程同步機制 (Multithreading & Locking)
- **挑戰**: 背景監控緒與 Web API 緒同時操作硬體會造成衝突。
- **解決方案**: 
    - 使用 `threading.Lock`。
    - **優化記錄**: 借鑒自 BUMP 版本的「鎖超時 (Blocking Timeout)」機制，確保重要警報 (Mission/Alert) 不會因為一般的狀態更新被擋在門外。

## 💡 軟體架構師的重建建議
如果我要重新從零開始設計類似專案，我會：
1. **單一職責模式**: 將 `StockMonitor` 拆分為 `DataFetcher` (純數據) 與 `AlertProcessor` (邏輯判定)，目前兩者混在一個 Thread 裡，擴展性受限。
2. **事件驅動架構**: 使用像 `EventEmitter` 的模式，讓硬體動作 (Tapo) 與語音 (TTS) 作為訂閱者監聽警報事件，而不是在 `StockMonitor` 裡直接調用方法。
3. **PWA 優先**: 前端應完全轉向 PWA，提供離線狀態提示與更好的手機推送支持。

## 🚩 歷史坑位與警告 (Caveats)
- **Tapo 協議坑**: Klap 手路 (Handshake) 經常失效，必須手動修正 Protocol 類型。
- **TTS 阻塞**: 在 Mac 上，`say` 指令是同步的，若不啟用獨立執行緒會導致監控迴圈卡死。
- **IP 變動**: 家用路由器常會重配 IP，必須維持「掃描 (Scan)」功能的可用性。

---
## 🚀 最新進度與部署 (2025-12-30)
- **穩定性強化**: 完成 Smart Socket 與 Smart Bulb 的完全兼容，優化了前端顯示邏輯，根據裝置類型自動隱藏無效欄位。
- **部署準備**: 整理了 `Release_MarketTradeAlertLight` 目錄，確保專案可供一般使用者透過 `setup_and_run.sh` 快速啟動。
- **文件優化**: 在 `README.md` 中加入手動查詢 Tapo 裝置 IP 的教學實作，降低使用門檻。

---
*更新於 2025-12-30 by Antigravity*

