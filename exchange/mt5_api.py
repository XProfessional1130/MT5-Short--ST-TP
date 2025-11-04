import time
import logging
from datetime import datetime, timedelta
import pandas as pd
import MetaTrader5 as mt5

bot_logger = logging.getLogger("bot_logger")


class MT5API:
    def __init__(self, config):
        self.config = config

    def initialize(self):
        # connect to MetaTrader 5
        if not mt5.initialize():
            mt5.shutdown()
            return False
        return True

    def login(self):
        # connect to the trade account specifying a server
        authorized = mt5.login(self.config["account"], server=self.config["server"])
        if authorized:
            bot_logger.info("[+] Login success, account info: ")
            account_info = mt5.account_info()._asdict()
            bot_logger.info(account_info)
            return True
        else:
            bot_logger.info("[-] Login failed, check account infor")
            return False

    def round_price(self, symbol, price):
        symbol_info = mt5.symbol_info(symbol)
        return round(price, symbol_info.digits)
    
    def get_filling_mode(self, symbol):
        """Get the appropriate filling mode for a symbol based on broker support.
        
        Filling mode bitmask values:
        - SYMBOL_FILLING_FOK = 1 (bit 0)
        - SYMBOL_FILLING_IOC = 2 (bit 1)
        - SYMBOL_FILLING_RETURN = 4 (bit 2)
        """
        symbol_info = mt5.symbol_info(symbol)
        if symbol_info is None:
            bot_logger.warning("[-] Cannot get symbol info for {}, using default FOK".format(symbol))
            return mt5.ORDER_FILLING_FOK
        
        # Check which filling modes are supported
        # filling_mode is a bitmask where:
        # - Bit 0 (1) = FOK
        # - Bit 1 (2) = IOC
        # - Bit 2 (4) = RETURN
        filling_mode = symbol_info.filling_mode
        
        # Try in order of preference: IOC, FOK, RETURN
        if filling_mode & 2:  # SYMBOL_FILLING_IOC
            return mt5.ORDER_FILLING_IOC
        elif filling_mode & 1:  # SYMBOL_FILLING_FOK
            return mt5.ORDER_FILLING_FOK
        elif filling_mode & 4:  # SYMBOL_FILLING_RETURN
            return mt5.ORDER_FILLING_RETURN
        else:
            # Default to FOK if unknown
            bot_logger.warning("[-] Unknown filling mode for {}, using FOK".format(symbol))
            return mt5.ORDER_FILLING_FOK

    def get_assets_balance(self, assets=["USD"]):
        assets = {}
        return assets

    def tick_ask_price(self, symbol):
        return mt5.symbol_info_tick(symbol).ask

    def tick_bid_price(self, symbol):
        return mt5.symbol_info_tick(symbol).bid

    def klines(self, symbol: str, interval: str, **kwargs):
        symbol_rates = mt5.copy_rates_from_pos(
            symbol, getattr(mt5, "TIMEFRAME_" + (interval[-1:] + interval[:-1]).upper()), 0, kwargs["limit"]
        )
        df = pd.DataFrame(symbol_rates)
        df["time"] += -time.timezone
        df["time"] = pd.to_datetime(df["time"], unit="s")
        df.columns = ["Open time", "Open", "High", "Low", "Close", "Volume", "Spread", "Real_Volume"]
        df = df[["Open time", "Open", "High", "Low", "Close", "Volume"]]
        return df

    def place_order(self, params):
        return mt5.order_send(params)

    def history_deals_get(self, position_id):
        return mt5.history_deals_get(position=position_id)
