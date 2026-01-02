import os
import sys
import fcntl

class SingleInstance:
    def __init__(self, lockfile_path=".app.lock"):
        self.lockfile_path = lockfile_path
        self.fp = open(self.lockfile_path, 'w')
        try:
            # LOCK_EX: Exclusive lock
            # LOCK_NB: Non-blocking, raises BlockingIOError if already locked
            fcntl.lockf(self.fp, fcntl.LOCK_EX | fcntl.LOCK_NB)
            # Write current PID for debugging
            self.fp.write(str(os.getpid()))
            self.fp.flush()
        except BlockingIOError:
            print("\n" + "!" * 40)
            print("⚠️ 錯誤：SmartStockLight 已經在運行中！")
            print("請先關閉另一個視窗或進程再重新啟動。")
            print("!" * 40 + "\n")
            sys.exit(1)

    def __del__(self):
        try:
            fcntl.lockf(self.fp, fcntl.LOCK_UN)
            self.fp.close()
            if os.path.exists(self.lockfile_path):
                os.remove(self.lockfile_path)
        except Exception:
            pass
