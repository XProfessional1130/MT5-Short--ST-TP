"""
Download historical data from MetaTrader 5 for backtesting.
This script uses the MT5 Python API to download the same historical data
that MT5 Strategy Tester uses.
"""
import os
import time
import calendar
import argparse
import json
from datetime import datetime, timezone
import pandas as pd
import MetaTrader5 as mt5


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


def initialize_mt5(exchange_config):
    """Initialize and login to MT5."""
    if not mt5.initialize():
        print("[-] MT5 initialize() failed, error code =", mt5.last_error())
        return False
    
    account = exchange_config["account"]
    server = exchange_config["server"]
    
    authorized = mt5.login(account, server=server)
    if authorized:
        account_info = mt5.account_info()
        if account_info:
            print(f"[+] MT5 login successful")
            print(f"    Account: {account_info.login}")
            print(f"    Server: {account_info.server}")
            print(f"    Balance: {account_info.balance}")
            return True
        else:
            print("[-] Failed to get account info")
            return False
    else:
        print(f"[-] MT5 login failed, error code = {mt5.last_error()}")
        return False


def download_monthly_data(symbol, interval, month, year, output_dir):
    """Download historical data for a specific month."""
    tf = TIMEFRAME_MAP.get(interval)
    if tf is None:
        print(f"[-] Unsupported interval: {interval}")
        return False
    
    # Calculate date range for the month
    from_date = datetime(year, month, 1).replace(tzinfo=timezone.utc).timestamp()
    last_day = calendar.monthrange(year, month)[1]
    to_date = datetime(year, month, last_day, 23, 59, 59).replace(tzinfo=timezone.utc).timestamp()
    
    try:
        # Download data from MT5
        rates = mt5.copy_rates_range(symbol, tf, from_date, to_date)
        
        if rates is None or len(rates) == 0:
            print(f"    [-] No data available for {symbol} {interval} {year}-{month:02d}")
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
        os.makedirs(output_dir, exist_ok=True)
        
        # Save to CSV
        filename = f"{symbol}-{interval}-{year}-{month:02d}.csv"
        filepath = os.path.join(output_dir, filename)
        df.to_csv(filepath, index=False)
        
        print(f"    [+] Downloaded: {filename} ({len(df)} bars, {df.iloc[0]['Open time']} to {df.iloc[-1]['Open time']})")
        return True
        
    except Exception as e:
        print(f"    [-] Error downloading {symbol} {interval} {year}-{month:02d}: {e}")
        return False


def download_from_config(exchange_config_file, symbols_config_file, output_dir):
    """Download data based on symbols trading configuration."""
    # Load exchange config
    with open(exchange_config_file) as f:
        exchange_configs = json.load(f)
    
    # Initialize MT5 (use 'mt5' key from config)
    if "mt5" not in exchange_configs:
        print("[-] MT5 configuration not found in exchange config")
        return False
    
    if not initialize_mt5(exchange_configs["mt5"]):
        return False
    
    # Load symbols config
    with open(symbols_config_file) as f:
        symbols_config = json.load(f)
    
    print(f"\n[*] Starting data download...")
    print(f"    Output directory: {output_dir}\n")
    
    total_files = 0
    successful = 0
    
    for symbol_cfg in symbols_config:
        symbol = symbol_cfg["symbol"]
        year = symbol_cfg["year"]
        months = symbol_cfg["months"]
        
        print(f"[+] Downloading data for {symbol} ({year}, months: {months})")
        
        # Get unique intervals from all strategies
        intervals = set()
        for strategy in symbol_cfg["strategies"]:
            tf = strategy["tfs"].get("tf")
            if tf:
                intervals.add(tf)
        
        # Download data for each interval and month
        for interval in intervals:
            for month in sorted(months):
                total_files += 1
                if download_monthly_data(symbol, interval, month, year, output_dir):
                    successful += 1
        
        print()
    
    print(f"[*] Download complete: {successful}/{total_files} files downloaded successfully")
    
    mt5.shutdown()
    return successful == total_files


def main():
    parser = argparse.ArgumentParser(description="Download historical data from MT5 for backtesting")
    parser.add_argument("--exch_cfg_file", required=True, type=str, 
                       help="Path to exchange config file (e.g., configs/exchange_config.json)")
    parser.add_argument("--sym_cfg_file", required=True, type=str,
                       help="Path to symbols trading config file (e.g., configs/symbols_trading_config.json)")
    parser.add_argument("--output_dir", required=True, type=str,
                       help="Output directory for CSV files (e.g., ./data)")
    
    args = parser.parse_args()
    
    download_from_config(args.exch_cfg_file, args.sym_cfg_file, args.output_dir)


if __name__ == "__main__":
    main()

