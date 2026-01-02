# 開發者設計精華日誌 (Developer Design Log)

## 🎯 專案定位：SmartStockLight (User Version)
本專案為面向一般投資者的智慧硬體監控系統，核心目標是「穩定、美觀、易用」。

## 🏗️ 軟體架構 (Software Architecture) - 2026-01-02 升級版

### 1. 專案檔案指南 (Project File Guide)
#### 🚀 啟動入口
- `main.py`: 系統主程式入口（整合監控與 Web 服務）。
- `gui.py`: 生成視窗介面（WebView）的圖形入口。

#### 📂 分層模組結構
- `core/`: 存放權衡決策中心（監控、價格代理、設定物件）。
- `devices/`: 硬體控制中心（封裝 Klap 協議，支援燈泡與插座）。
- `system/`: 系統維護中心（授權核驗、自動更新檢查）。
- `web/`: 前端介面提供中心（Flask Server 邏輯）。

#### ⚙️ 基礎建設檔案
- `config.json`: 使用者個人化設定（IP、帳密、標的）。
- `.license_key`: 授權憑證存檔。
- `MarketTradeAlertLight.spec`: 打包發布用的規格定義檔。
- `pyproject.toml` / `poetry.lock`: Python 生態系標準的相依套件管理。

### 2. 分層模組化架構 (Categorized Architecture)
- **核心設計**: 為了提升代碼的可維護性，我們將單一目錄結構重構為分群路徑。
- **目錄結構**:
    - `core/`: 核心監控邏輯與數據抓取 (`monitor.py`, `data_agent.py`, `config.py`)。
    - `devices/`: 硬體抽象層，隔離不同硬體協議 (`controller.py`, `scanner.py`)。
    - `system/`: 系統底層服務，如授權核驗與自動更新 (`license.py`, `updater.py`)。
    - `web/`: 網頁伺服器邏輯 (`server.py`)。

### 3. 混合式數據引擎 (Hybrid Data Engine)
- **架構描述**: 採用實時與輪詢結合的策略。
- **設計決策**: 
    - 虛擬貨幣使用高頻輪詢 (或 Websocket 橋接)，達成 0.5s - 1s 的響應速度。
    - 股票使用 REST API 輪詢，維持 10s 間隔以避免被 Rate Limit。

### 4. 多線程同步機制 (Multithreading & Locking)
- **挑戰**: 背景監控執行緒與 Web API 執行緒同時操作硬體會造成衝突。
- **解決方案**: 
    - 使用 `threading.Lock`。
    - 確保重要警報不會因為一般的狀態更新被鎖定。

### 5. 單一執行實體保護 (Single Instance Protection)
- **設計決策**: 為了防止使用者重複開啟程式導致多重監控緒爭搶硬體控制權。
- **實作**: 
    - 使用 `fcntl` (macOS/Linux) 建立文件鎖 `.app.lock`。
    - 啟動時檢查鎖定狀態，若已被佔用則強制退出並提示使用者。

### 6. 狀態變更驅動控制 (State-Change-Only Control)
- **設計決策**: 避免每一輪監控循環都發送硬體指令。
- **實作**: 
    - 在 `StockMonitor` 引入 `last_color_state`。
    - 只有在新舊顏色狀態不一致（如：黃燈轉綠燈）時才發送協議指令。
    - **效益**: 極大降低網絡負擔，並解決了「睡眠模式」被自動狀態巡檢覆蓋的問題。

## 💡 軟體架構師的重建建議
1. **單一職責模式**: 雖然已經模組化，但 `monitor.py` 仍承擔了較多判定邏輯，未來可進一步拆分 `DecisionEngine` 與 `ActionInvoker`。
2. **事件驅動**: 引入事件派發器，讓硬體動作與語音播放作為監聽者，而非硬編碼調用。

## 🚩 歷史坑位與警告 (Caveats)
- **IP 變動**: 家用裝置 IP 可能隨機跳動，掃描功能必須常保可用。
- **跨平台差異**: 語音指令在 Mac/Windows/Linux 上的實現路徑不同，需依賴 `pyttsx3` 或系統原生指令。

---
*更新於 2026-01-02 by Antigravity*
