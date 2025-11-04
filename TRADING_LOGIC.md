# Trading Logic Documentation

## Overview

This trading system is an event-driven, multi-strategy automated trading bot that executes trades based on technical analysis indicators and pattern recognition. The system supports multiple trading strategies running simultaneously on different timeframes.

---

## Architecture

### High-Level Flow

```
Market Data (MT5) 
    ↓
TradeEngine (Scheduler)
    ↓
Trader (Per Symbol)
    ↓
Strategies (Multiple)
    ↓
Order Creation
    ↓
OMS (Order Management System)
    ↓
MT5 Exchange
```

### Components

1. **TradeEngine**: Main orchestrator, schedules data updates and monitors trades
2. **Trader**: Manages all strategies for a single trading symbol
3. **Strategy**: Contains trading logic, signal detection, and order management
4. **Order**: Represents a trade with entry, SL, TP, and status
5. **OMS**: Order Management System that interfaces with MT5

---

## Trading Flow

### 1. Initialization Phase

```
1. Load configuration files
   - Exchange config (MT5 credentials)
   - Symbols trading config (strategies, parameters)
   
2. Initialize MT5 connection
   - Login to broker account
   
3. Create Trader instances
   - One Trader per symbol
   - Load strategies from config
   
4. Initialize indicators
   - Calculate initial ZigZag points
   - Calculate moving averages
   - Calculate MACD, RSI, etc.
   
5. Load historical data
   - Initialize charts with required timeframes
   - Set start trading time
```

### 2. Live Trading Loop

```
Every minute (or when new candle closes):
    1. Check if new candle is available
    2. For each timeframe:
       - Fetch new kline data
       - Update charts
       - Call Trader.on_kline(tf, kline)
    3. For each strategy:
       - Update indicators (update_indicators)
       - Update order status (check if SL/TP hit)
       - Check for new signals (check_signal)
       - Check for exit signals (check_close_signal)
    4. Monitor active trades (every 15 seconds)
       - Adjust stop loss if needed
       - Check for manual close conditions
```

### 3. Signal Detection Flow

```
Strategy.update(tf):
    ↓
update_indicators(tf)  # Update technical indicators
    ↓
update_orders_status()  # Check if SL/TP hit
    ↓
check_close_signal()     # Check exit conditions
    ↓
check_signal()           # Check entry conditions
```

---

## Strategy Logic Patterns

### Pattern 1: Breakout Strategy (BreakStrategy)

**Concept**: Trade breakouts from consolidation patterns with volume confirmation.

**Entry Logic**:
```
1. Volume Filter:
   - Current volume > vol_ratio_ma × MA(volume)
   
2. ZigZag Analysis:
   - Identify consolidation pattern using ZigZag
   - Calculate up trend line and down trend line
   - Check if pattern is valid (min_num_cuml candles)
   
3. Candle Pattern:
   - For BUY: Green candle with strong body
     - Body > kline_body_ratio × average_body
     - Upper wick < 50% of candle range
   - For SELL: Red candle with strong body
     - Body > kline_body_ratio × average_body
     - Lower wick < 50% of candle range
   
4. Trend Confirmation:
   - BUY: Close > SMA(200) and Close > down_trend_line projection
   - SELL: Close < SMA(200) and Close < up_trend_line projection
   
5. Stop Loss:
   - BUY: Set at up_trend_line low point
   - SELL: Set at down_trend_line high point
   
6. Risk Management:
   - Apply max_sl_pct constraint
   - Adjust SL if needed (sl_fix_mode)
```

**Exit Logic**:
```
1. Reverse Signal:
   - Close BUY orders if uptrend reverses
   - Close SELL orders if downtrend reverses
   
2. Trend Line Break:
   - Close BUY if price breaks below up_trend_line
   - Close SELL if price breaks above down_trend_line
   
3. Stop Loss Adjustment:
   - Adjust SL to new ZigZag points as trend continues
```

### Pattern 2: MACD Divergence Strategy

**Concept**: Trade divergence between price and MACD indicator.

**Entry Logic**:
```
1. ZigZag Analysis:
   - Identify swing highs/lows using ZigZag
   - Minimum zigzag strength: min_zz_pct
   
2. MACD Calculation:
   - Calculate MACD, Signal, Histogram
   - Use specified type (MACD, MACD_SIGNAL, or MACD_HIST)
   
3. Divergence Detection:
   - Regular Divergence (trend reversal):
     * Price makes higher high, MACD makes lower high → SELL
     * Price makes lower low, MACD makes higher low → BUY
   - Hidden Divergence (trend continuation):
     * Price makes higher low, MACD makes lower low → BUY
     * Price makes lower high, MACD makes higher high → SELL
   
4. Trend Confirmation:
   - Check trend using n_trend_point ZigZag points
   - Minimum trend percentage: min_trend_pct
   - Trend line fit: min_updown_ratio
   
5. Risk/Reward:
   - Minimum risk/reward ratio: min_rr
   - Minimum reward: min_rw_pct
   
6. Stop Loss:
   - Based on ZigZag points
   - Apply sl_fix_mode constraints
```

### Pattern 3: RSI Divergence Strategy

**Concept**: Similar to MACD divergence but using RSI indicator.

**Entry Logic**:
```
1. RSI Calculation:
   - RSI length: rsi_len (default 14)
   
2. Divergence Detection:
   - Compare RSI values at swing points
   - Delta RSI: delta_rsi (tolerance for comparison)
   - Delta Price: delta_price_pct (tolerance for price comparison)
   
3. Overbought/Oversold:
   - Regular divergence: os_rsi (25), ob_rsi (70)
   
4. Fibonacci Retracement:
   - fib_retr_lv: Fibonacci level for entry
   
5. Risk Management:
   - Similar to MACD divergence strategy
```

---

## Order Lifecycle

### Order States

```
PENDING → FILLED → [HIT_SL | HIT_TP | STOPPED]
```

1. **PENDING**: Limit order waiting to be filled
2. **FILLED**: Order executed, position opened
3. **HIT_SL**: Stop loss triggered, position closed at loss
4. **HIT_TP**: Take profit triggered, position closed at profit
5. **STOPPED**: Manual exit signal, position closed manually

### Order Creation Process

```python
# 1. Strategy detects signal
order = Order(
    OrderType.MARKET,      # or LIMIT
    OrderSide.BUY,         # or SELL
    entry_price,
    tp=take_profit,        # optional
    sl=stop_loss,          # optional
    status=OrderStatus.FILLED  # or PENDING for limit orders
)

# 2. Add metadata
order["FILL_TIME"] = current_time
order["strategy"] = strategy_name
order["description"] = strategy_description

# 3. Risk management adjustment
order = trader.fix_order(order, sl_fix_mode, max_sl_pct)

# 4. Create trade in OMS
trader.create_trade(order, volume)
```

### Order Status Updates

```python
# Every candle update:
order.update_status(kline)

# Checks:
# - If PENDING: Check if price touched entry (limit order)
# - If FILLED: Check if price hit SL or TP
# - Update order status accordingly
```

---

## Risk Management

### Stop Loss Fix Modes

1. **ADJ_SL**: Adjust stop loss to meet max_sl_pct constraint
   ```python
   if sl violates max_sl_pct:
       sl = adjust_to_max_sl(entry, max_sl_pct)
   ```

2. **ADJ_ENTRY**: Adjust entry price to meet max_sl_pct constraint
   ```python
   if sl violates max_sl_pct:
       entry = adjust_entry_from_sl(sl, max_sl_pct)
       order.type = LIMIT  # Change to limit order
       order.status = PENDING
   ```

3. **IGNORE**: Cancel order if SL violates max_sl_pct
   ```python
   if sl violates max_sl_pct:
       return None  # Order not created
   ```

### Max SL Percentage

```
max_sl_pct = 0.75  # 0.75%

For BUY order:
  max_sl = (1 - 0.0075) × entry = 0.9925 × entry
  SL cannot be below this level

For SELL order:
  max_sl = (1 + 0.0075) × entry = 1.0075 × entry
  SL cannot be above this level
```

### Dynamic Stop Loss Adjustment

Some strategies adjust SL as price moves favorably:

```python
# BreakStrategy example
def adjust_sl(self):
    # Get latest ZigZag point
    last_main_zz = self.zz_points[self.main_zz_idx[-1]]
    
    # For SELL orders: Move SL to new peak
    if last_main_zz.ptype == PEAK_POINT:
        for sell_order in opening_orders:
            if order.sl > last_main_zz.pline.high:
                order.adjust_sl(last_main_zz.pline.high)
                trader.adjust_sl(order, new_sl)
    
    # For BUY orders: Move SL to new low
    else:
        for buy_order in opening_orders:
            if order.sl < last_main_zz.pline.low:
                order.adjust_sl(last_main_zz.pline.low)
                trader.adjust_sl(order, new_sl)
```

---

## Signal Detection Examples

### Example 1: Breakout BUY Signal

```
Conditions:
1. Volume: 5000 > 1.8 × 2500 (MA volume) ✓
2. ZigZag: Found consolidation pattern with 15 candles ✓
3. Candle: Green, body = 50 pips, avg_body = 15 pips ✓
   Body ratio: 50/15 = 3.3 > 2.5 ✓
   Upper wick: 10 pips < 50% of range (60 pips) ✓
4. Price: Close = 1.0850, SMA(200) = 1.0800 ✓
5. Trend line: Close > down_trend_line projection ✓
6. Stop loss: Set at up_trend_line low = 1.0820
   Risk: (1.0850 - 1.0820) / 1.0850 = 0.28% < 0.75% ✓

→ CREATE BUY ORDER
```

### Example 2: MACD Hidden Divergence BUY Signal

```
Conditions:
1. ZigZag: Found swing low at index 100 (price = 1.0800)
   Found swing low at index 150 (price = 1.0820)
   Price: Higher low ✓ (1.0820 > 1.0800)
   
2. MACD: At index 100, MACD = -0.0010
   At index 150, MACD = -0.0015
   MACD: Lower low ✓ (-0.0015 < -0.0010)
   
3. Delta check: Price delta = 0.2% > 0.1% ✓
   MACD delta = 0.0005 > 0.0002 ✓
   
4. Trend: Uptrend confirmed (14 ZigZag points) ✓
   Trend strength: 2% > 0.5% ✓
   
5. Risk/Reward: 
   Risk = 0.5% (SL distance)
   Reward = 1.2% (TP distance)
   RR = 1.2 / 0.5 = 2.4 > 2.0 ✓

→ CREATE BUY ORDER
```

---

## Order Execution Flow

### Live Trading

```
1. Strategy detects signal
   ↓
2. Create Order object
   ↓
3. Apply risk management (fix_order)
   ↓
4. Trader.create_trade(order, volume)
   ↓
5. OMS.create_trade(order, volume)
   ↓
6. MT5 API: order_send(params)
   ↓
7. Order tracked in OMS
   ↓
8. Monitor for SL/TP hits
   ↓
9. Close trade when triggered
```

### Backtesting

```
1. Strategy detects signal
   ↓
2. Create Order object
   ↓
3. Apply risk management (fix_order)
   ↓
4. Order added to strategy.orders_opening
   ↓
5. Every candle: order.update_status(kline)
   ↓
6. Check if SL/TP hit in candle
   ↓
7. If hit: Move to orders_closed
   ↓
8. Calculate PnL statistics
```

---

## Key Technical Indicators

### ZigZag Indicator
- **Purpose**: Identify swing highs/lows, eliminate market noise
- **Parameters**: 
  - `min_zz_pct`: Minimum percentage change for a swing point
  - `zz_dev`: Deviation multiplier for pattern recognition
- **Types**:
  - `ZZ_DRC`: Standard ZigZag
  - `ZZ_CONV`: Convergent ZigZag (smoother)

### Moving Averages
- **SMA(200)**: Long-term trend filter
- **MA(Volume)**: Volume confirmation
- Used in various strategies for trend confirmation

### MACD
- **Components**: MACD line, Signal line, Histogram
- **Usage**: Divergence detection, trend confirmation
- **Parameters**: fast_len, slow_len, signal

### RSI
- **Purpose**: Overbought/oversold levels, divergence detection
- **Default**: 14 periods
- **Levels**: Overbought (70), Oversold (25)

---

## Strategy Configuration

Each strategy requires:

```json
{
  "name": "strategy_name",
  "params": {
    // Strategy-specific parameters
  },
  "tfs": {
    "tf": "15m"  // Timeframe
  },
  "max_sl_pct": 0.75,  // Maximum stop loss percentage
  "volume": 0.01        // Position size in lots
}
```

### Common Parameters

- `sl_fix_mode`: `"ADJ_SL"`, `"ADJ_ENTRY"`, or `"IGNORE"`
- `min_rr`: Minimum risk/reward ratio
- `min_rw_pct`: Minimum reward percentage
- `min_zz_pct`: Minimum ZigZag strength
- `delta_price_pct`: Price comparison tolerance
- `n_last_point`: Number of recent points to analyze
- `n_trend_point`: Number of points for trend analysis

---

## Performance Metrics

Each strategy tracks:

- **LONG/SHORT**: Number of long/short trades
- **LONG_TP_PnL(%)**: Total profit from winning long trades
- **LONG_SL_PnL(%)**: Total loss from losing long trades
- **LONG_PnL(%)**: Net PnL from long trades
- **NUM_LONG_TP**: Number of winning long trades
- **LONG_TP_PCT**: Win rate for long trades
- **TOTAL**: Total number of trades
- **TOTAL_TP_PCT**: Overall win rate
- **TOTAL_PnL(%)**: Total net PnL
- **AVG(%)**: Average PnL per trade

---

## Error Handling

### Order Validation
- Checks if TP/SL are on correct side relative to entry
- Validates risk/reward ratios
- Ensures max_sl_pct constraints are met

### Data Validation
- Checks if required indicators are calculated
- Validates ZigZag points exist before using
- Ensures sufficient historical data

### Connection Handling
- Retries MT5 connection on failure
- Logs all trading actions for debugging
- Graceful shutdown on interruption

---

## Best Practices

1. **Multiple Strategies**: Run different strategies simultaneously for diversification
2. **Risk Management**: Always set max_sl_pct to limit maximum loss
3. **Backtesting**: Always backtest strategies before live trading
4. **Parameter Tuning**: Use tuning.py to optimize parameters
5. **Monitoring**: Review HTML visualizations to understand strategy behavior
6. **Logging**: Check logs regularly for errors and performance

---

## Custom Strategy Development

To create a new strategy:

1. Inherit from `BaseStrategy`
2. Implement required methods:
   - `init_indicators()`: Initialize technical indicators
   - `update_indicators(tf)`: Update indicators on new candle
   - `check_signal()`: Detect entry signals
   - `check_close_signal()`: Detect exit signals
   - `is_params_valid()`: Validate parameters
3. Register in `strategy_utils.py`
4. Add parameter schema in `configs/strategies_def.py`

Example structure:

```python
class MyStrategy(BaseStrategy):
    def init_indicators(self):
        # Calculate indicators
        pass
    
    def update_indicators(self, tf):
        # Update indicators on new candle
        pass
    
    def check_signal(self):
        # Check for entry signals
        if conditions_met:
            order = Order(...)
            self.trader.create_trade(order, self.volume)
            self.orders_opening.append(order)
    
    def check_close_signal(self):
        # Check for exit signals
        pass
```

---

## Summary

This trading system provides:

- **Modular architecture** for easy strategy development
- **Risk management** with configurable SL/TP
- **Multiple timeframe support** for comprehensive analysis
- **Backtesting capability** for strategy validation
- **Live trading** with real-time execution
- **Performance tracking** with detailed statistics
- **Visualization** with HTML charts

The system is designed to be flexible, extensible, and production-ready for automated trading operations.

