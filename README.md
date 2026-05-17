# Solana Memecoin Telegram Alert Bot

Python MVP that polls DexScreener for recent Solana token profiles and boosts,
filters noisy pairs, checks RugCheck, sends Telegram alerts, and logs seen tokens
to SQLite.

The bot is alert-only. It does not buy, sell, sign transactions, store private
keys, or execute trades.

## Setup

```bash
cp .env.example .env
```

Edit `.env` with your Telegram bot token and chat ID.

This MVP uses only the Python standard library. Use Python 3.11 or newer.

## Run

```bash
python3.12 main.py
```

The SQLite database is created at `data/bot.sqlite3` by default.

Useful one-off commands:

```bash
python3.12 main.py --test-telegram
python3.12 main.py --once
python3.12 main.py --once --max-alerts 1
```

## How It Works

1. Fetch latest Solana token profiles and boosted tokens from DexScreener.
2. Fetch pair data for those token mints.
3. Skip tokens already recorded in SQLite.
4. Apply liquidity, 5m volume, age, and market cap filters.
5. Fetch RugCheck's token report.
6. Send a Telegram alert when the RugCheck score meets the configured minimum.

RugCheck is treated as a signal, not a guarantee. Always manually verify tokens
before trading.
