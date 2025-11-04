import os
import time
import calendar
from datetime import datetime, timedelta, timezone
import logging
import json
import shutil
from typing import List, Set, Tuple
import pandas as pd
import MetaTrader5 as mt5
from trader import Trader
from utils import tf_cron, NUM_KLINE_INIT, CANDLE_COLUMNS
from utils import get_pretty_table


bot_logger = logging.getLogger("bot_logger")

# Map interval string to MT5 timeframe constant
TIMEFRAME_MAP = {
    "1m": mt5.TIMEFRAME_M1,
    "5m": mt5.TIMEFRAME_M5,
    "15m": mt5.TIMEFRAME_M15,
    "30m": mt5.TIMEFRAME_M30,
    "1h": mt5.TIMEFRAME_H1,
    "4h": mt5.TIMEFRAME_H4,
    "1d": mt5.TIMEFRAME_D1,
    "1w": mt5.TIMEFRAME_W1,
    "1mn": mt5.TIMEFRAME_MN1,
}


class BackTest:
    def __init__(self, exch, symbols_trading_cfg_file, data_dir, exchange_config_file=None):
        self.exch = exch
        self.data_dir = data_dir
        self.exchange_config_file = exchange_config_file
        self.bot_traders: List[Trader] = []
        self.symbols_trading_cfg_file = symbols_trading_cfg_file
        self.debug_dir = os.environ["DEBUG_DIR"]

    def load_mt5_klines_monthly_data(self, symbol, interval, month, year):
        csv_data_path = os.path.join(self.data_dir, "{}-{}-{}-{:02d}.csv".format(symbol, interval, year, month))
        if not os.path.exists(csv_data_path):
            bot_logger.warning("    [-] Data file not found: {}".format(csv_data_path))
            return pd.DataFrame(columns=["Open time", "Open", "High", "Low", "Close", "Volume"])
        df = pd.read_csv(csv_data_path)
        if len(df) == 0:
            bot_logger.warning("    [-] Empty data file: {}".format(csv_data_path))
            return pd.DataFrame(columns=["Open time", "Open", "High", "Low", "Close", "Volume"])
        df["Open time"] = pd.to_datetime(df["Open time"])
        return df

    def load_klines_monthly_data(self, symbol, interval, month, year):
        return self.load_mt5_klines_monthly_data(symbol, interval, month, year)

    def get_required_data_files(self) -> Set[Tuple[str, str, int, int]]:
        """Get set of required data files: (symbol, interval, year, month)."""
        required_files = set()
        
        with open(self.symbols_trading_cfg_file) as f:
            symbols_config = json.load(f)
        
        for symbol_cfg in symbols_config:
            symbol = symbol_cfg["symbol"]
            year = symbol_cfg["year"]
            months = symbol_cfg["months"]
            
            # Get unique intervals from all strategies
            intervals = set()
            for strategy in symbol_cfg["strategies"]:
                tf = strategy["tfs"].get("tf")
                if tf:
                    intervals.add(tf)
            
            # Add all required files
            for interval in intervals:
                for month in months:
                    required_files.add((symbol, interval, year, month))
        
        return required_files

    def check_data_files_exist(self) -> Tuple[bool, List[Tuple[str, str, int, int]]]:
        """Check which required data files exist. Returns (all_exist, missing_files)."""
        required_files = self.get_required_data_files()
        missing_files = []
        
        for symbol, interval, year, month in required_files:
            filename = f"{symbol}-{interval}-{year}-{month:02d}.csv"
            filepath = os.path.join(self.data_dir, filename)
            
            if not os.path.exists(filepath):
                missing_files.append((symbol, interval, year, month))
        
        all_exist = len(missing_files) == 0
        return all_exist, missing_files

    def initialize_mt5(self, exchange_config):
        """Initialize and login to MT5."""
        if not mt5.initialize():
            bot_logger.error("[-] MT5 initialize() failed, error code = {}".format(mt5.last_error()))
            return False
        
        account = exchange_config["account"]
        server = exchange_config["server"]
        
        authorized = mt5.login(account, server=server)
        if authorized:
            account_info = mt5.account_info()
            if account_info:
                bot_logger.info("[+] MT5 login successful for data download")
                return True
            else:
                bot_logger.error("[-] Failed to get account info")
                return False
        else:
            bot_logger.error("[-] MT5 login failed, error code = {}".format(mt5.last_error()))
            return False

    def download_missing_data(self, missing_files: List[Tuple[str, str, int, int]]):
        """Download missing historical data files from MT5."""
        if not self.exchange_config_file:
            bot_logger.error("[-] Exchange config file not provided, cannot download data")
            return False
        
        # Load exchange config
        with open(self.exchange_config_file) as f:
            exchange_configs = json.load(f)
        
        if "mt5" not in exchange_configs:
            bot_logger.error("[-] MT5 configuration not found in exchange config")
            return False
        
        if not self.initialize_mt5(exchange_configs["mt5"]):
            return False
        
        bot_logger.info("[*] Downloading missing historical data...")
        bot_logger.info("    Output directory: {}".format(self.data_dir))
        
        successful = 0
        total = len(missing_files)
        
        # Group by symbol for better logging
        files_by_symbol = {}
        for symbol, interval, year, month in missing_files:
            if symbol not in files_by_symbol:
                files_by_symbol[symbol] = []
            files_by_symbol[symbol].append((interval, year, month))
        
        for symbol, file_list in files_by_symbol.items():
            bot_logger.info("[+] Downloading data for {} ({} files)".format(symbol, len(file_list)))
            
            for interval, year, month in file_list:
                if self._download_monthly_data(symbol, interval, month, year):
                    successful += 1
        
        bot_logger.info("[*] Download complete: {}/{} files downloaded successfully".format(successful, total))
        
        mt5.shutdown()
        return successful == total

    def _download_monthly_data(self, symbol, interval, month, year):
        """Download historical data for a specific month."""
        tf = TIMEFRAME_MAP.get(interval)
        if tf is None:
            bot_logger.error("    [-] Unsupported interval: {}".format(interval))
            return False
        
        # Calculate date range for the month
        from_date = datetime(year, month, 1).replace(tzinfo=timezone.utc).timestamp()
        last_day = calendar.monthrange(year, month)[1]
        to_date = datetime(year, month, last_day, 23, 59, 59).replace(tzinfo=timezone.utc).timestamp()
        
        try:
            # Download data from MT5
            rates = mt5.copy_rates_range(symbol, tf, from_date, to_date)
            
            if rates is None or len(rates) == 0:
                bot_logger.warning("    [-] No data available for {} {} {}-{:02d}".format(symbol, interval, year, month))
                return False
            
            # Convert to DataFrame
            df = pd.DataFrame(rates)
            
            # Adjust timezone
            df["time"] += -time.timezone
            df["time"] = pd.to_datetime(df["time"], unit="s")
            
            # Rename columns to match project format
            df.columns = ["Open time", "Open", "High", "Low", "Close", "Volume", "Spread", "Real_Volume"]
            df = df[["Open time", "Open", "High", "Low", "Close", "Volume"]]
            
            # Create output directory if it doesn't exist
            os.makedirs(self.data_dir, exist_ok=True)
            
            # Save to CSV
            filename = f"{symbol}-{interval}-{year}-{month:02d}.csv"
            filepath = os.path.join(self.data_dir, filename)
            df.to_csv(filepath, index=False)
            
            bot_logger.info("    [+] Downloaded: {} ({} bars, {} to {})".format(
                filename, len(df), df.iloc[0]['Open time'], df.iloc[-1]['Open time']
            ))
            return True
            
        except Exception as e:
            bot_logger.error("    [-] Error downloading {} {} {}-{:02d}: {}".format(symbol, interval, year, month, e))
            return False

    def ensure_data_files(self):
        """Check for required data files and download if missing."""
        bot_logger.info("[*] Checking for required historical data files...")
        
        all_exist, missing_files = self.check_data_files_exist()
        
        if all_exist:
            bot_logger.info("[+] All required data files exist")
            return True
        
        bot_logger.info("[!] Missing {} data file(s), attempting to download...".format(len(missing_files)))
        
        if not self.exchange_config_file:
            bot_logger.error("[-] Cannot download data: exchange config file not provided")
            bot_logger.error("    Please provide --exch_cfg_file when running backtest")
            return False
        
        return self.download_missing_data(missing_files)

    def backtest_bot_trader(self, symbol_cfg):
        bot_trader = Trader(symbol_cfg)
        bot_trader.init_strategies()
        tfs_chart = {}
        # Load kline data for all required timeframes
        for tf in bot_trader.get_required_tfs():
            monthly_data = []
            for month in sorted(symbol_cfg["months"]):
                month_data = self.load_klines_monthly_data(symbol_cfg["symbol"], tf, month, symbol_cfg["year"])
                if len(month_data) > 0:
                    monthly_data.append(month_data)
            
            if len(monthly_data) == 0:
                bot_logger.error(
                    "[-] No data found for {} {} in months {}".format(
                        symbol_cfg["symbol"], tf, symbol_cfg["months"]
                    )
                )
                raise ValueError(
                    "No data available for {} {}: Please download historical data using download_data.py".format(
                        symbol_cfg["symbol"], tf
                    )
                )
            
            chart_df = pd.concat(monthly_data, ignore_index=True)
            # Sort by time to ensure correct order
            chart_df = chart_df.sort_values("Open time").reset_index(drop=True)
            tfs_chart[tf] = chart_df
            
            # Check if we have enough data
            if len(chart_df) < NUM_KLINE_INIT:
                bot_logger.error(
                    "[-] Insufficient data for {} {}: found {} candles, need at least {}".format(
                        symbol_cfg["symbol"], tf, len(chart_df), NUM_KLINE_INIT
                    )
                )
                bot_logger.error(
                    "    Please download more historical data or use a longer time period"
                )
                bot_logger.error(
                    "    For 1m timeframe, you need at least {} candles (about {} days)".format(
                        NUM_KLINE_INIT, NUM_KLINE_INIT / (24 * 60)
                    )
                )
                bot_logger.error(
                    "    For 5m timeframe, you need at least {} candles (about {} days)".format(
                        NUM_KLINE_INIT, NUM_KLINE_INIT / (24 * 12)
                    )
                )
                raise ValueError(
                    "Insufficient data for {} {}: need at least {} candles, found {}".format(
                        symbol_cfg["symbol"], tf, NUM_KLINE_INIT, len(chart_df)
                    )
                )
        max_time = max([tf_chart.iloc[NUM_KLINE_INIT - 1]["Open time"] for tf_chart in tfs_chart.values()])
        end_time = max([tf_chart.iloc[-1]["Open time"] for tf_chart in tfs_chart.values()])
        tfs_chart_init = {}
        for tf, tf_chart in tfs_chart.items():
            tfs_chart_init[tf] = tf_chart[tf_chart["Open time"] <= max_time][-NUM_KLINE_INIT:]
            tfs_chart[tf] = tf_chart[tf_chart["Open time"] > max_time]
            start_index = tfs_chart_init[tf].index[0]
            tfs_chart_init[tf].index -= start_index
            tfs_chart[tf].index -= start_index
        bot_trader.init_chart(tfs_chart_init)
        bot_trader.attach_oms(None)  # for backtesting don't need oms

        timer = max_time
        end_time = end_time
        bot_logger.info("   [+] Start timer from: {} to {}".format(timer, end_time))
        required_tfs = [tf for tf in tf_cron.keys() if tf in bot_trader.get_required_tfs()]
        # c = 0
        while timer <= end_time:
            timer += timedelta(seconds=60)
            hour, minute = timer.hour, timer.minute
            for tf in required_tfs:
                cron_time = tf_cron[tf]
                if ("hour" not in cron_time or hour in cron_time["hour"]) and (
                    "minute" not in cron_time or minute in cron_time["minute"]
                ):
                    last_kline = tfs_chart[tf][:1]
                    tfs_chart[tf] = tfs_chart[tf][1:]
                    bot_trader.on_kline(tf, last_kline)
            #         c += 1
            # if c > 1000:
            #     break
        return bot_trader

    def start(self):
        # Check and download missing data files before starting backtest
        if not self.ensure_data_files():
            bot_logger.error("[-] Failed to ensure all required data files are available")
            return
        
        with open(self.symbols_trading_cfg_file) as f:
            symbols_config = json.load(f)
        c = 0
        bot_logger.info("[*] Start backtesting ...")
        for symbol_cfg in symbols_config:
            bot_logger.info("[+] Backtest bot for symbol: {}".format(symbol_cfg["symbol"]))
            bot_trader = self.backtest_bot_trader(symbol_cfg)
            self.bot_traders.append(bot_trader)
            c += 1
            if c >= 2:
                break
        bot_logger.info("[*] Backtesting finished")

    def summary_trade_result(self):
        final_backtest_stats = []
        for bot_trader in self.bot_traders:
            bot_trader.close_opening_orders()
            backtest_stats = bot_trader.statistic_trade()
            bot_logger.info(get_pretty_table(backtest_stats, bot_trader.get_symbol_name(), transpose=True, tran_col="NAME"))
            backtest_stats.loc[len(backtest_stats) - 1, "NAME"] = bot_trader.get_symbol_name()
            final_backtest_stats.append(backtest_stats.loc[len(backtest_stats) - 1 :])

            bot_trader.log_orders()
            bot_trader.plot_strategy_orders()

        table_stats = pd.concat(final_backtest_stats, axis=0, ignore_index=True)
        s = table_stats.sum(axis=0)
        table_stats.loc[len(table_stats)] = s
        table_stats.loc[len(table_stats) - 1, "NAME"] = "TOTAL"
        bot_logger.info(get_pretty_table(table_stats, "SUMMARY", transpose=True, tran_col="NAME"))
        return table_stats

    def stop(self):
        pass