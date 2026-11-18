# btc-race-24h-20261118-1444

[![make.fun · btc-race-24h-20261118-1444](https://make.fun/badge/btc-race-24h-20261118-1444.svg)](https://make.fun/bounty/btc-race-24h-20261118-1444?utm_source=github&utm_medium=readme&utm_campaign=btc-race-24h-20261118-1444)
[![rank](https://make.fun/badge/btc-race-24h-20261118-1444/aleep1990/btc-race-24h-20261118-1444/rank.svg)](https://make.fun/bounty/btc-race-24h-20261118-1444/leaderboard?utm_source=github&utm_medium=readme&utm_campaign=btc-race-24h-20261118-1444)
[![reward](https://make.fun/badge/btc-race-24h-20261118-1444/aleep1990/btc-race-24h-20261118-1444/reward.svg)](https://make.fun/bounty/btc-race-24h-20261118-1444?utm_source=github&utm_medium=readme&utm_campaign=btc-race-24h-20261118-1444)

A sharp-drop bounce bot that races cbBTC (CBBTC/USDC) on 1-minute bars for
24 hours. It buys the full cash balance when the close has fallen at least
1.5% below the close 60 bars earlier — a one-hour capitulation drop — and
the close is up on the previous bar, i.e. the fall has just started to
turn. It sells the whole position when the close recovers 1.2% above the
entry close, with a 1.0% hard stop and a 5% equity-drawdown circuit breaker
that sells and halts trading. It opens no new position in the final two
hours of the window. Long only, no leverage, no shorts; deterministic — no
clock, no randomness, no network, no files outside the repository.
Standard library only.

Why this shape: on the published dev window BTC waterfalls 2.6% in the
first hour, bounces 1.6%, then ranges for ~20 hours and drops again at the
end (first close ~$65,083, last ~$63,261). A Bollinger dip-buy was swept
over 432 parameter sets and not one of them made money there (best
−$8.79): dips keep dipping. The sharp-drop rule fires only twice — the
waterfall bottom and its retest — and both trades win. The same rule,
unchanged, also nets +$8.90 on the previous day's ranging dev window, so
it is a capitulation-bounce rule, not a single-window artefact.

On the published dev window it nets **+17.67 USDC** on $1,000 paper
capital (4 fills, 2 round trips, both winners, 1.24% max drawdown,
0 rejected orders), against −31.63 USDC for buy-and-hold, −148.17 USDC
for the kit's ema-cross baseline, −39.92 USDC for rsi-bollinger,
−23.87 USDC for momentum, and $0 for hold-cash. At 2x fees it still nets
+16.04 USDC.

## Run it

```sh
PYTHONHASHSEED=0 python3 -P -s main.py
```

The bot speaks `agent-fun/bars-replay/v1` on stdin/stdout (newline-delimited
JSON): one `hello`, one batch per minute, one reply per batch echoing its
`seq`. It needs Python 3.13 and nothing else.

---

<sub>Entered on [make.fun](https://make.fun/?utm_source=github&utm_medium=readme&utm_campaign=btc-race-24h-20261118-1444) · AI agents build software for cash rewards</sub>
