# Complete Parameters Reference Guide

## Configuration Structure

```json
{
    "symbol": "EURUSD",           // Trading symbol
    "strategies": [...],           // Array of strategy configurations
    "months": [6],                 // Months to backtest (1-12)
    "year": 2025                   // Year to backtest
}
```

---

## Global Strategy Parameters

These parameters apply to ALL strategies:

### `tfs` (Timeframes)
```json
"tfs": {
    "tf": "15m"
}
```
- **Purpose**: Specifies which timeframe the strategy uses
- **Values**: `"1m"`, `"5m"`, `"15m"`, `"30m"`, `"1h"`, `"4h"`, `"1d"`
- **Impact**: Lower timeframes = more opportunities, more signals

### `max_sl_pct` (Maximum Stop Loss Percentage)
```json
"max_sl_pct": 0.15
```
- **Purpose**: Maximum allowed stop loss as percentage of entry price
- **Values**: `0.1` = 0.1%, `0.15` = 0.15%, `0.25` = 0.25%
- **Calculation**:
  - BUY: `max_sl = entry × (1 - max_sl_pct/100)`
  - SELL: `max_sl = entry × (1 + max_sl_pct/100)`
- **Impact**: Lower = tighter stops, smaller risk per trade
- **Example**: Entry 1.0850, max_sl_pct=0.15 → Max SL = 1.0837 (13 pips)

### `volume` (Position Size)
```json
"volume": 0.01
```
- **Purpose**: Position size in lots
- **Values**: `0.01` = micro lot, `0.1` = mini lot, `1.0` = standard lot
- **Impact**: Higher = larger position size, more profit/loss per trade

---

## Breakout Strategy Parameters

### `min_num_cuml` (Minimum Consolidation Candles)
```json
"min_num_cuml": 2
```
- **Purpose**: Minimum number of candles in consolidation pattern
- **Values**: `2` = very short, `3` = short, `5-10` = medium, `10+` = long
- **Impact on Frequency**: 
  - Lower = More signals (shorter patterns accepted)
  - Higher = Fewer signals (longer patterns required)
- **Your Config**: `2` (very aggressive) and `3` (moderate)

### `min_zz_pct` (Minimum ZigZag Percentage)
```json
"min_zz_pct": 0.03
```
- **Purpose**: Minimum price movement percentage for ZigZag swing points
- **Values**: `0.03` = 0.03% (3 pips), `0.05` = 0.05%, `0.5` = 0.5%
- **Impact on Frequency**:
  - Lower = More swing points detected, more signals
  - Higher = Fewer swing points, less noise, fewer signals
- **Your Config**: `0.03` (very sensitive) and `0.04` (sensitive)

### `zz_dev` (ZigZag Deviation Multiplier)
```json
"zz_dev": 1.2
```
- **Purpose**: Multiplier for pattern recognition threshold
- **Values**: `1.0` = very loose, `1.2-1.5` = loose, `2.0-2.5` = strict
- **Calculation**: `threshold = zz_dev × min_zz_pct`
- **Impact on Frequency**:
  - Lower = More patterns accepted, more signals
  - Higher = Stricter patterns, fewer signals
- **Your Config**: `1.2` (loose) and `1.3` (moderate)

### `ma_vol` (Volume Moving Average Period)
```json
"ma_vol": 5
```
- **Purpose**: Period for volume moving average
- **Values**: `5` = fast, `10` = medium, `25` = slow
- **Impact on Frequency**:
  - Lower = Faster response to volume changes, more signals
  - Higher = Smoother volume filter, fewer signals
- **Your Config**: `5` (very fast) and `8` (fast)

### `vol_ratio_ma` (Volume Ratio to MA)
```json
"vol_ratio_ma": 1.0
```
- **Purpose**: Minimum volume compared to moving average
- **Values**: `1.0` = normal volume, `1.2` = 20% above average, `1.8` = 80% above
- **Impact on Frequency**:
  - Lower = Accepts normal volume, more signals
  - Higher = Requires high volume, fewer but higher quality signals
- **Your Config**: `1.0` (accepts normal volume) and `1.1` (slight filter)

### `kline_body_ratio` (Candle Body Strength Ratio)
```json
"kline_body_ratio": 1.0
```
- **Purpose**: Minimum candle body size compared to average
- **Values**: `1.0` = average body, `1.5` = 1.5× average, `2.5` = 2.5× average
- **Impact on Frequency**:
  - Lower = Accepts weak candles, more signals
  - Higher = Requires strong candles, fewer signals
- **Your Config**: `1.0` (accepts average candles) and `1.2` (slight filter)

### `sl_fix_mode` (Stop Loss Fix Mode)
```json
"sl_fix_mode": "ADJ_SL"
```
- **Purpose**: How to handle stop loss when it violates max_sl_pct
- **Values**:
  - `"ADJ_SL"`: Adjust SL to meet max_sl_pct (most common)
  - `"ADJ_ENTRY"`: Adjust entry price, convert to limit order
  - `"IGNORE"`: Cancel order if SL too large
- **Impact**: `ADJ_SL` = most trades accepted, `IGNORE` = fewer trades

---

## MA Cross Strategy Parameters

### `fast_ma` (Fast Moving Average Period)
```json
"fast_ma": 3
```
- **Purpose**: Period for fast moving average
- **Values**: `3` = very fast, `5` = fast, `10` = medium, `20` = slow
- **Impact on Frequency**:
  - Lower = More crossovers, more signals
  - Higher = Fewer crossovers, more reliable signals
- **Your Config**: `3` (very fast), `5` (fast), `7` (medium)

### `slow_ma` (Slow Moving Average Period)
```json
"slow_ma": 8
```
- **Purpose**: Period for slow moving average
- **Values**: `8` = fast, `10` = medium, `20` = slow, `50` = very slow
- **Impact on Frequency**:
  - Lower = More crossovers, more signals
  - Higher = Fewer crossovers, more reliable
- **Your Config**: `8` (fast), `10` (medium), `14` (slower)

### `type` (Moving Average Type)
```json
"type": "SMA"
```
- **Purpose**: Type of moving average
- **Values**: `"SMA"` = Simple Moving Average, `"EMA"` = Exponential Moving Average
- **Impact**:
  - `SMA`: More stable, less sensitive
  - `EMA`: More responsive, more signals

---

## RSI Divergence Strategy Parameters

### `rsi_len` (RSI Period)
```json
"rsi_len": 14
```
- **Purpose**: Period for RSI calculation
- **Values**: `14` = standard, `9` = fast, `21` = slow
- **Impact**: Lower = more sensitive, more signals

### `delta_rsi` (RSI Delta Tolerance)
```json
"delta_rsi": 1
```
- **Purpose**: Tolerance for comparing RSI values
- **Values**: `1` = very loose, `2` = loose, `3` = strict
- **Impact on Frequency**:
  - Lower = More divergence detected, more signals
  - Higher = Stricter divergence, fewer signals
- **Your Config**: `1` (very loose, maximum signals)

### `delta_price_pct` (Price Delta Percentage)
```json
"delta_price_pct": 0.05
```
- **Purpose**: Minimum price change percentage for divergence
- **Values**: `0.05` = 0.05% (5 pips), `0.1` = 0.1%, `0.2` = 0.2%
- **Impact on Frequency**:
  - Lower = Smaller moves accepted, more signals
  - Higher = Larger moves required, fewer signals
- **Your Config**: `0.05` (very small moves, high frequency)

### `min_rr` (Minimum Risk/Reward Ratio)
```json
"min_rr": 1.5
```
- **Purpose**: Minimum risk/reward ratio required
- **Values**: `1.0` = 1:1, `1.5` = 1.5:1, `2.0` = 2:1, `3.0` = 3:1
- **Impact on Frequency**:
  - Lower = More trades accepted, more signals
  - Higher = Better trades only, fewer signals
- **Your Config**: `1.5` (moderate RR, good for scalping)

### `min_rw_pct` (Minimum Reward Percentage)
```json
"min_rw_pct": 0.15
```
- **Purpose**: Minimum take profit as percentage
- **Values**: `0.15` = 0.15% (15 pips), `0.5` = 0.5%, `1.0` = 1%
- **Impact**: Lower = smaller TP, easier to hit, more winning trades
- **Your Config**: `0.15` (small TP, scalping target)

### `min_trend_pct` (Minimum Trend Percentage)
```json
"min_trend_pct": 0.3
```
- **Purpose**: Minimum price movement to confirm trend
- **Values**: `0.3` = 0.3%, `0.5` = 0.5%, `1.0` = 1%
- **Impact on Frequency**:
  - Lower = Weaker trends accepted, more signals
  - Higher = Strong trends only, fewer signals
- **Your Config**: `0.3` (weak trends, more signals)

### `min_updown_ratio` (Trend Line Fit Ratio)
```json
"min_updown_ratio": 0.5
```
- **Purpose**: How well price follows trend lines (0-1)
- **Values**: `0.5` = 50% fit, `0.65` = 65% fit, `0.8` = 80% fit
- **Impact on Frequency**:
  - Lower = Looser fit, more signals
  - Higher = Tighter fit, fewer but better signals
- **Your Config**: `0.5` (loose fit, more signals)

### `n_last_point` (Number of Last Points to Analyze)
```json
"n_last_point": 3
```
- **Purpose**: How many recent swing points to check for divergence
- **Values**: `3` = few points, `5` = standard, `10` = many
- **Impact on Frequency**:
  - Lower = Fewer points to check, faster, more signals
  - Higher = More thorough analysis, slower, fewer signals
- **Your Config**: `3` (quick analysis, high frequency)

### `n_trend_point` (Number of Points for Trend Analysis)
```json
"n_trend_point": 10
```
- **Purpose**: How many ZigZag points to determine trend
- **Values**: `10` = short-term trend, `14` = medium, `20-40` = long-term
- **Impact on Frequency**:
  - Lower = Shorter trend analysis, more signals
  - Higher = Longer trend analysis, fewer signals
- **Your Config**: `10` (short-term) and `20` (medium-term)

### `ob_rsi` (Overbought RSI Level)
```json
"ob_rsi": 70
```
- **Purpose**: RSI level considered overbought
- **Values**: `70` = standard, `75` = strict, `80` = very strict
- **Impact**: Only affects regular divergence strategy

### `os_rsi` (Oversold RSI Level)
```json
"os_rsi": 30
```
- **Purpose**: RSI level considered oversold
- **Values**: `25` = strict, `30` = standard, `35` = loose
- **Impact**: Only affects regular divergence strategy
- **Your Config**: `30` (standard level)

### `fib_retr_lv` (Fibonacci Retracement Level)
```json
"fib_retr_lv": 1
```
- **Purpose**: Fibonacci level for entry (only in regular divergence)
- **Values**: `1` = 100% retracement, `0.618` = 61.8%, `0.5` = 50%
- **Impact**: Entry point calculation

### `zz_type` (ZigZag Type)
```json
"zz_type": "ZZ_DRC"
```
- **Purpose**: Type of ZigZag algorithm
- **Values**: 
  - `"ZZ_DRC"`: Standard ZigZag (more points)
  - `"ZZ_CONV"`: Convergent ZigZag (smoother, fewer points)
- **Impact on Frequency**:
  - `ZZ_DRC` = More swing points, more signals
  - `ZZ_CONV` = Fewer swing points, smoother signals

### `zz_conv_size` (ZigZag Convergent Size)
```json
"zz_conv_size": 3
```
- **Purpose**: Kernel size for convergent ZigZag (only if zz_type = "ZZ_CONV")
- **Values**: `3` = small, `5` = medium, `7` = large
- **Impact**: Larger = smoother, fewer points

---

## Price Action Strategy Parameters

Uses same parameters as Breakout Strategy:
- `min_num_cuml`
- `min_zz_pct`
- `zz_dev`
- `ma_vol`
- `vol_ratio_ma`
- `kline_body_ratio`
- `sl_fix_mode`

---

## Parameter Optimization Guide

### To Increase Frequency (More Trades):

**Breakout/Price Action:**
- ✅ Lower `min_num_cuml`: `2` instead of `3`
- ✅ Lower `min_zz_pct`: `0.03` instead of `0.05`
- ✅ Lower `vol_ratio_ma`: `1.0` instead of `1.2`
- ✅ Lower `kline_body_ratio`: `1.0` instead of `1.5`
- ✅ Lower `zz_dev`: `1.2` instead of `1.5`
- ✅ Lower `ma_vol`: `5` instead of `10`

**RSI Divergence:**
- ✅ Lower `delta_rsi`: `1` instead of `2`
- ✅ Lower `delta_price_pct`: `0.05` instead of `0.1`
- ✅ Lower `min_rr`: `1.5` instead of `2.0`
- ✅ Lower `min_rw_pct`: `0.15` instead of `0.5`
- ✅ Lower `n_last_point`: `3` instead of `5`
- ✅ Lower `n_trend_point`: `10` instead of `14`

**MA Cross:**
- ✅ Lower `fast_ma`: `3` instead of `5`
- ✅ Lower `slow_ma`: `8` instead of `10`

### To Increase Quality (Higher Win Rate):

**Breakout/Price Action:**
- ⬆️ Increase `min_num_cuml`: `5` instead of `2`
- ⬆️ Increase `vol_ratio_ma`: `1.5` instead of `1.0`
- ⬆️ Increase `kline_body_ratio`: `2.0` instead of `1.0`
- ⬆️ Increase `zz_dev`: `2.0` instead of `1.2`

**RSI Divergence:**
- ⬆️ Increase `delta_rsi`: `2` instead of `1`
- ⬆️ Increase `min_rr`: `2.0` instead of `1.5`
- ⬆️ Increase `min_trend_pct`: `0.5` instead of `0.3`
- ⬆️ Increase `n_last_point`: `5` instead of `3`

---

## Your Current Configuration Summary

### Strategy Mix:
- **2x Breakout** strategies (different parameters)
- **3x MA Cross** strategies (3/8, 5/10, 7/14)
- **2x Price Action** strategies (different parameters)
- **2x RSI** strategies (hidden + regular divergence)

**Total: 9 strategies** = Maximum frequency setup

### Parameter Settings (Aggressive for High Frequency):

| Parameter | Value | Impact |
|-----------|-------|--------|
| `min_num_cuml` | 2-3 | ⚡ Very short consolidation |
| `min_zz_pct` | 0.03-0.04 | ⚡ Very sensitive swing detection |
| `vol_ratio_ma` | 1.0-1.1 | ⚡ Accepts normal volume |
| `kline_body_ratio` | 1.0-1.2 | ⚡ Accepts weak candles |
| `max_sl_pct` | 0.1-0.15 | ⚡ Small stops (10-15 pips) |
| `min_rr` | 1.5 | ⚡ Moderate RR for scalping |
| `min_rw_pct` | 0.15 | ⚡ Small TP (15 pips) |

### Expected Results:

- **Frequency**: 150-300 trades/week (with 9 strategies on 15m)
- **Win Rate Target**: 75-80% (with proper optimization)
- **SL/TP**: 0.1-0.15% (10-15 pips)

---

## Quick Reference: Parameter Meanings

| Parameter | Lower Value = | Higher Value = |
|-----------|--------------|----------------|
| `min_num_cuml` | More signals | Fewer, better signals |
| `min_zz_pct` | More sensitive | Less sensitive |
| `vol_ratio_ma` | More signals | Higher quality only |
| `kline_body_ratio` | Accept weak candles | Require strong candles |
| `zz_dev` | More patterns | Stricter patterns |
| `min_rr` | More trades | Better RR only |
| `delta_rsi` | More divergence | Stricter divergence |
| `max_sl_pct` | Smaller stops | Larger stops allowed |

---

## Testing Recommendations

1. **Start with current config** → Backtest and measure
2. **If too few trades**: Lower thresholds further
3. **If win rate < 80%**: Increase quality filters
4. **If too many losing trades**: Tighten `vol_ratio_ma` or `kline_body_ratio`
5. **Optimize per strategy**: Some strategies may need different parameters

All parameters are optimized for **maximum frequency** while maintaining reasonable quality. Adjust based on backtest results!

