"""
監控「小水滴應援毛巾（洋流祭限定）」是否補貨，有貨就用 ntfy 推播到手機。
在 GitHub Actions 上執行：每次 workflow 會連續監控約 5 小時 50 分，每分鐘檢查一次。
TOPIC 從 GitHub Secrets（NTFY_TOPIC）讀取，避免公開 repo 外流。
"""
import os
import time
import urllib.request
from datetime import datetime, timedelta, timezone

URL = "https://puma.oen.tw/good/3LqtVpRKPQbM4Si9qNeH55xvcFL?from=puma_good"
TOPIC = os.environ["NTFY_TOPIC"]
INTERVAL = 60                                  # 每幾秒檢查一次
TW = timezone(timedelta(hours=8))
DEADLINE = datetime(2026, 11, 13, 12, 0, tzinfo=TW)
RUN_LIMIT = timedelta(hours=5, minutes=50)     # GitHub 單次 job 上限 6 小時
SOLD_OUT_TEXT = "已無庫存"


def now_tw() -> datetime:
    return datetime.now(TW)


def fetch_page() -> str:
    req = urllib.request.Request(URL, headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req, timeout=20) as r:
        return r.read().decode("utf-8", errors="ignore")


def notify(msg: str, title: str = "毛巾補貨了！", priority: str = "urgent") -> None:
    req = urllib.request.Request(
        f"https://ntfy.sh/{TOPIC}",
        data=msg.encode("utf-8"),
        headers={"Title": title.encode("utf-8"), "Priority": priority, "Click": URL},
    )
    urllib.request.urlopen(req, timeout=20)


def main() -> None:
    start = now_tw()
    stop_at = min(DEADLINE, start + RUN_LIMIT)
    if start >= DEADLINE:
        print("已過截止時間，不執行")
        return

    notify(f"監控中，本輪到 {stop_at:%m/%d %H:%M}", title="毛巾監控啟動", priority="low")

    while now_tw() < stop_at:
        t = now_tw().strftime("%H:%M:%S")
        try:
            html = fetch_page()
            if SOLD_OUT_TEXT in html:
                print(f"[{t}] 仍無庫存", flush=True)
            elif "小水滴" in html:          # 確認是正常頁面
                print(f"[{t}] 有貨！", flush=True)
                notify("有貨了，快點開連結！")
                time.sleep(300)             # 5 分鐘內不重複通知
                continue
            else:
                print(f"[{t}] 頁面內容異常，略過", flush=True)
        except Exception as e:
            print(f"[{t}] 錯誤：{e}", flush=True)
        time.sleep(INTERVAL)

    print("本輪結束")


if __name__ == "__main__":
    main()
