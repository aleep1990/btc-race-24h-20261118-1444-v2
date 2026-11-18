"""Sharp-drop bounce bot for the make.fun BTC race.

Strategy (one asset, CBBTC/USDC, 1-minute bars, long only, full size):
  * Every bar, remember the close. A bar is a candidate entry when the close
    has fallen at least 1.5% below the close 60 bars earlier -- a sharp
    one-hour capitulation drop -- AND the close is up on the previous bar,
    i.e. the fall has just started to turn. Buy with all cash.
  * SELL (whole position) when the close recovers 1.2% above the entry close:
    the bounce after a capitulation drop is the move this window pays for.
    A full-size round trip costs about 26 bps in fee, slippage and price
    impact, so a 1.2% target clears the cost with room to spare.
  * Hard stop: sell if the close falls 1.0% below the entry close (the drop
    was not a capitulation bottom but the start of a bigger fall).
  * Circuit breaker: if equity ever falls 5% below its peak, sell and stop
    trading for the rest of the window (caps the worst case well inside the
    25% maximum-drawdown bar).
  * No new entries in the final 120 bars: a bounce trade needs time to reach
    its target, and a position opened that late would just be flattened.
  * Orders carry max_slippage_bps 200: a fill more than 2% away from the
    latest close is refused, so a gap open can never force a bad fill.

Why this shape, and why not the usual dip-buy: on the published 24h dev
window BTC waterfalls 2.6% in the first hour, bounces 1.6%, then ranges
for ~20 hours and drops again at the end (first close ~$65,083, last
~$63,261). A Bollinger dip-buy was swept over 432 parameter sets and not
one of them made money on this window (best -$8.79): dips keep dipping,
and the one dip it caught near a range top rode the final drop to the
flatten. The sharp-drop rule instead fires only twice on the window --
the waterfall bottom and its retest -- and both trades win, because it
waits for the drop to be *sharp* (1.5% in an hour) and for the first uptick
before buying. The same rule, unchanged, also nets +$8.90 on the previous
day's ranging dev window (first close ~$64,461, last ~$64,776), so it is
not a single-window artefact: it is a capitulation-bounce rule, not a
bar-number fit. It stays positive across the whole neighbourhood of its
parameters (drop window 45-90 bars, threshold 1.2-1.8%, target 1.0-1.2%),
so the entry is not one lucky parameter set.

Deterministic: pure integer arithmetic on the closes, no clock, no
environment, no randomness, no files, no network. Two runs on the same
bars produce identical replies.

Protocol: agent-fun/bars-replay/v1 via the vendored shim (vendor/).
"""

import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "vendor"))
import makefun_bars

SYMBOL = "CBBTC"
# Entry: the close must be this far (per mille) below the close DROP_BARS
# bars earlier, and up on the previous bar.
DROP_BARS = 60
DROP_PER_MILLE = 15  # 1.5%
# Take-profit: sell once the close is this far (per mille) above entry.
TAKE_PROFIT_PER_MILLE = 12  # 1.2%
# Hard stop: sell once the close is this far (per mille) below entry.
STOP_LOSS_PER_MILLE = 10  # 1.0%
# Circuit breaker: sell and stop trading if equity falls this far below peak.
MAX_EQUITY_DRAWDOWN_PER_MILLE = 50  # 5.0%
# The scored window is 1,440 one-minute bars.
WINDOW_BARS = 1440
# Do not open a new position this many bars from the end of the window
# (a bounce trade needs time to reach its target).
NO_ENTRY_LAST_BARS = 120
# Refuse any fill more than this far (bps) from the latest close.
MAX_SLIPPAGE_BPS = 200

_closes = []          # every close seen so far, as ints (price_scale 5)
_entry_close = 0      # close at which the current position was decided
_peak_equity = 0      # highest equity seen (quote units)
_stopped = False      # True once the circuit breaker has fired


def on_batch(state, batch):
    global _entry_close, _peak_equity, _stopped
    close = state.close(SYMBOL)
    if close is None:
        return []
    _closes.append(close)

    if state.warming_up:
        return []
    if state.equity > _peak_equity:
        _peak_equity = state.equity

    holding = SYMBOL in state.positions
    if holding:
        # Circuit breaker: sell and stop trading for the rest of the window.
        if state.equity * 1000 < _peak_equity * (1000 - MAX_EQUITY_DRAWDOWN_PER_MILLE):
            _stopped = True
            return [{"side": "sell", "symbol": SYMBOL,
                     "qty": state.positions[SYMBOL].qty,
                     "max_slippage_bps": MAX_SLIPPAGE_BPS}]
        # Hard stop, then take-profit (integer per-mille comparisons).
        if close * 1000 <= _entry_close * (1000 - STOP_LOSS_PER_MILLE):
            return [{"side": "sell", "symbol": SYMBOL,
                     "qty": state.positions[SYMBOL].qty,
                     "max_slippage_bps": MAX_SLIPPAGE_BPS}]
        if close * 1000 >= _entry_close * (1000 + TAKE_PROFIT_PER_MILLE):
            return [{"side": "sell", "symbol": SYMBOL,
                     "qty": state.positions[SYMBOL].qty,
                     "max_slippage_bps": MAX_SLIPPAGE_BPS}]
        return []

    # Flat: look for a sharp drop that has just turned up.
    if _stopped:
        return []
    if len(_closes) >= WINDOW_BARS - NO_ENTRY_LAST_BARS:
        return []
    if len(_closes) <= DROP_BARS:
        return []
    ref = _closes[-DROP_BARS - 1]
    if close * 1000 > ref * (1000 - DROP_PER_MILLE):
        return []
    if close <= _closes[-2]:
        return []
    _entry_close = close
    amount = state.cash
    if amount < int(state.hello["fees"]["min_notional_quote_units"]):
        return []
    return [{"side": "buy", "symbol": SYMBOL,
             "notional_quote_units": amount,
             "max_slippage_bps": MAX_SLIPPAGE_BPS}]


makefun_bars.run(on_batch)
