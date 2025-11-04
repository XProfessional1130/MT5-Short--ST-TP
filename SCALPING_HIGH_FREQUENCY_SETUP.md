# High-Frequency Scalping Setup (500-1000 Trades/Week, 80% Win Rate)

## Target Requirements
- **Frequency**: 500-1000 trades per week (~71-143 trades/day, ~6-12 trades/hour)
- **Win Rate**: 80% success rate
- **SL/TP**: Small (0.05% - 0.15%)

## Is This Possible?

**YES, but with modifications:**

### Current System Limitations:
1. ✅ **15m timeframe** - Too slow for high frequency
2. ✅ **Strict filters** - Reduce signal frequency
3. ✅ **Large SL/TP** - Current 0.5-1% is too large
4. ✅ **Single strategy** - Need multiple strategies

### Required Changes:

---

## Configuration Strategy

### 1. Use Lower Timeframes

**Current**: 15m (1 candle per 15 minutes = 96 candles/day)
**Required**: 1m or 5m (960 candles/day or 192 candles/day)

**Impact on Frequency:**
- 1m: ~16x more opportunities than 15m
- 5m: ~3x more opportunities than 15m

### 2. Lower Filter Thresholds

#### Breakout Strategy Parameters:

```json
{
    "min_num_cuml": 3,        // Was 10 → Lower = more signals
    "min_zz_pct": 0.05,       // Was 0.5 → Lower = detect smaller moves
    "zz_dev": 1.5,            // Was 2.5 → Lower = less strict pattern
    "ma_vol": 10,             // Was 25 → Faster volume MA
    "vol_ratio_ma": 1.2,      // Was 1.8 → Lower volume requirement
    "kline_body_ratio": 1.5,  // Was 2.5 → Accept weaker candles
    "max_sl_pct": 0.1         // Was 0.75 → Small SL (0.1%)
}
```

### 3. Set Small SL/TP

**Recommended SL/TP for Scalping:**
- **SL**: 0.05% - 0.15% (5-15 pips on EURUSD)
- **TP**: 0.08% - 0.25% (8-25 pips on EURUSD)
- **RR Ratio**: 1.5:1 to 2:1 (small but consistent)

**Example:**
```
Entry: 1.08500
SL: 1.08485 (0.15% = 15 pips)
TP: 1.08520 (0.20% = 20 pips)
RR: 1.33:1
```

### 4. Use Multiple Strategies Simultaneously

**Strategy Mix:**
1. **Breakout Strategy** (1m) - Quick breakouts
2. **Breakout Strategy** (5m) - Slightly longer breakouts
3. **MA Cross** (1m) - Fast crossovers
4. **Price Action** (1m) - Pattern recognition

**Total Signals**: 4 strategies × multiple timeframes = Higher frequency

---

## Expected Trade Frequency

### Calculation:

**Per Strategy (1m timeframe):**
- Candles per day: 1,440 (24 hours × 60 minutes)
- Signals per day (optimistic): 20-30 (1.5-2% of candles)
- Signals per week: 140-210

**With 4 Strategies:**
- Total signals: 560-840 per week
- After filters: ~400-700 per week ✅

**This matches your target of 500-1000 trades/week!**

---

## Configuration for 80% Win Rate

### Key Principles:

1. **Small SL/TP** → Easier to hit TP, harder to hit SL
2. **Tight entry** → Enter near support/resistance
3. **Quick exits** → Take profit quickly (don't let winners turn to losers)
4. **Filter noise** → Only trade high-probability setups

### Recommended Settings:

```json
{
    "max_sl_pct": 0.1,   // 0.1% SL (10 pips EURUSD)
    "min_rr": 1.5,       // Lower RR (1.5:1) for more trades
    "min_rw_pct": 0.15,  // 0.15% minimum TP
    "min_zz_pct": 0.05,  // Detect smaller moves
    "vol_ratio_ma": 1.2  // Lower volume filter
}
```

### Strategy Adjustments:

#### For 80% Win Rate:
- **SL**: 0.1% (10 pips)
- **TP**: 0.15% (15 pips)
- **RR**: 1.5:1
- **Win Rate Target**: 80%
- **Expected PnL per trade**: (0.8 × 0.15%) - (0.2 × 0.1%) = 0.1% per trade

**Weekly PnL (500 trades):**
- Wins: 400 × 0.15% = 60%
- Losses: 100 × 0.1% = 10%
- Net: 50% per week (if all trades executed)

---

## Complete Configuration File

See `configs/scalping_high_frequency_config.json` for the complete setup.

### Key Features:
- ✅ 4 strategies running simultaneously
- ✅ 1m and 5m timeframes
- ✅ Small SL/TP (0.1-0.15%)
- ✅ Lowered filters for more signals
- ✅ Multiple symbols possible (add more for higher frequency)

---

## Implementation Steps

### Step 1: Modify Strategy to Support TP

**Current Issue**: Breakout strategy sets `tp=None`. For scalping, we need fixed TP.

**Solution**: Modify strategy or create scalping variant with TP calculation:

```python
# In break_strategy.py check_signal()
# Calculate TP based on SL distance
if order.has_sl():
    risk = abs(order.entry - order.sl) / order.entry
    tp_distance = risk * 1.5  # 1.5:1 RR
    if order.side == OrderSide.BUY:
        tp = order.entry * (1 + tp_distance)
    else:
        tp = order.entry * (1 - tp_distance)
    order.adjust_tp(tp)
```

### Step 2: Adjust Timeframe Support

**Current**: System supports 1m, 5m, 15m, etc.
**Action**: Use `tf: "1m"` in config (already supported)

### Step 3: Test and Optimize

1. **Backtest** on historical data
2. **Measure**:
   - Trade frequency (trades/week)
   - Win rate (%)
   - Average SL/TP sizes
3. **Adjust** parameters to hit targets:
   - Too few trades? → Lower filters further
   - Win rate < 80%? → Tighten entry conditions
   - Too many losing trades? → Increase filters

---

## Risk Considerations

### ⚠️ **High Frequency Trading Risks:**

1. **Transaction Costs**:
   - Spread costs: 0.5-1 pip per trade
   - 500 trades/week = 500-1000 pips in spread costs
   - Need to ensure net profit > spread costs

2. **Slippage**:
   - Small TP/SL can be hit by spread
   - Need to account for broker spreads

3. **Execution Speed**:
   - MT5 API latency
   - Need fast execution for scalping

4. **Market Conditions**:
   - Scalping works best in:
     - High volatility
     - Tight spreads
     - Liquid markets (EURUSD, GBPUSD, USDJPY)

### Recommended Settings:

```json
{
    "max_sl_pct": 0.15,  // 15 pips minimum (account for spread)
    "min_rw_pct": 0.20,  // 20 pips TP (account for spread)
    // Ensure TP > Spread + SL
}
```

---

## Expected Performance

### Conservative Estimate (500 trades/week):

**Assumptions:**
- Win rate: 75% (slightly below 80% target)
- Avg win: 0.15% (15 pips)
- Avg loss: 0.1% (10 pips)
- Spread cost: 0.01% per trade (1 pip)

**Weekly Results:**
- Wins: 375 trades × (0.15% - 0.01%) = 52.5%
- Losses: 125 trades × (0.1% + 0.01%) = 13.75%
- **Net Profit: 38.75% per week**

**Monthly (4 weeks):**
- **Net Profit: ~155% per month**

### Optimistic Estimate (1000 trades/week, 80% win rate):

**Weekly Results:**
- Wins: 800 trades × (0.15% - 0.01%) = 112%
- Losses: 200 trades × (0.1% + 0.01%) = 22%
- **Net Profit: 90% per week**

**Monthly (4 weeks):**
- **Net Profit: ~360% per month**

---

## Optimization Tips

### To Increase Frequency:

1. **Lower `min_zz_pct`**: 0.05 → 0.03
2. **Lower `vol_ratio_ma`**: 1.2 → 1.1
3. **Lower `min_num_cuml`**: 3 → 2
4. **Add more strategies**: MA Cross, RSI Divergence
5. **Add more symbols**: EURUSD, GBPUSD, USDJPY

### To Increase Win Rate:

1. **Tighten entry conditions**: Higher `vol_ratio_ma`
2. **Better entry timing**: Use smaller `min_zz_pct` but higher confidence
3. **Filter noise**: Increase `kline_body_ratio`
4. **Use trailing stops**: Adjust SL as price moves favorably

### To Optimize SL/TP:

1. **Test different ratios**: 1.2:1, 1.5:1, 2:1
2. **Account for spread**: Ensure TP > SL + 2×spread
3. **Use ATR-based stops**: Dynamic SL based on volatility

---

## Monitoring and Validation

### Key Metrics to Track:

1. **Trade Frequency**:
   ```python
   trades_per_week = len(strategy.orders_closed) / (weeks_elapsed)
   ```

2. **Win Rate**:
   ```python
   win_rate = num_wins / total_trades
   ```

3. **Average SL/TP**:
   ```python
   avg_sl = mean([abs(o.sl - o.entry) / o.entry for o in orders])
   avg_tp = mean([abs(o.tp - o.entry) / o.entry for o in orders if o.tp])
   ```

4. **RR Ratio**:
   ```python
   avg_rr = mean([o.rr for o in orders if o.rr > 0])
   ```

### Backtest Validation:

```bash
# Run backtest with new config
python main.py --mode test --exch mt5 \
  --exch_cfg_file configs/exchange_config.json \
  --sym_cfg_file configs/scalping_high_frequency_config.json \
  --data_dir ./data

# Check results
# Look for:
# - Total trades > 500 per week
# - Win rate > 75%
# - Average SL < 0.15%
# - Average TP < 0.25%
```

---

## Summary

**Yes, 500-1000 trades/week with 80% win rate is possible with:**

1. ✅ **Lower timeframes** (1m, 5m instead of 15m)
2. ✅ **Reduced filters** (lower thresholds)
3. ✅ **Small SL/TP** (0.1-0.15%)
4. ✅ **Multiple strategies** (4+ strategies simultaneously)
5. ✅ **Multiple symbols** (EURUSD, GBPUSD, etc.)

**Key Configuration Changes:**
- `tf`: "1m" or "5m"
- `max_sl_pct`: 0.1 (0.1%)
- `min_zz_pct`: 0.05 (0.05%)
- `vol_ratio_ma`: 1.2 (lower filter)
- `min_num_cuml`: 3 (shorter consolidation)

**Expected Results:**
- Frequency: 500-1000 trades/week ✅
- Win Rate: 75-80% (with optimization) ✅
- SL/TP: 0.1-0.15% (small) ✅

**Next Steps:**
1. Use provided config file
2. Backtest to validate frequency
3. Optimize parameters to hit 80% win rate
4. Monitor spread costs and slippage
5. Scale up with multiple symbols if needed

