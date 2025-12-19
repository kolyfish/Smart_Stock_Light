import threading

class SharedConfig:
    def __init__(self, default_symbol="2330.TW", default_target=950.0):
        self._symbol = default_symbol
        self._target_price = default_target
        self._lock = threading.Lock()

    @property
    def symbol(self):
        with self._lock:
            return self._symbol

    @symbol.setter
    def symbol(self, value):
        with self._lock:
            self._symbol = value.strip().upper()

    @property
    def target_price(self):
        with self._lock:
            return self._target_price

    @target_price.setter
    def target_price(self, value):
        with self._lock:
            try:
                self._target_price = float(value)
            except ValueError:
                print(f"Invalid target price: {value}. Ignoring.")

    def get_config(self):
        with self._lock:
            return {
                "symbol": self._symbol,
                "target_price": self._target_price
            }

    def update_config(self, symbol, target_price):
        with self._lock:
            if symbol:
                self._symbol = symbol.strip().upper()
            if target_price is not None:
                try:
                    self._target_price = float(target_price)
                except ValueError:
                    pass
