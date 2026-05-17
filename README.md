# Solana Memecoin Telegram Alert Bot

Python MVP that polls DexScreener for recent Solana token profiles and boosts,
filters noisy pairs, checks RugCheck, sends Telegram alerts, and logs seen tokens
to SQLite locally or Postgres in production.

The bot is alert-only. It does not buy, sell, sign transactions, store private
keys, or execute trades.

## Setup

```bash
cp .env.example .env
```

Edit `.env` with your Telegram bot token and chat ID.

Use Python 3.11 or newer. Install dependencies when deploying with Postgres:

```bash
pip install -r requirements.txt
```

## Run

```bash
python3.12 main.py
```

The SQLite database is created at `data/bot.sqlite3` by default. Set
`DATABASE_URL` to use Postgres instead.

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

## GitHub Actions + Supabase

For a low-cost deployment, use Supabase Postgres for persistence and GitHub
Actions to run one alert cycle every 15 minutes.

1. Create a Supabase project.
2. Copy the Postgres connection string. Use the pooler/session connection string
   if Supabase recommends it for external clients.
3. In GitHub, open this repo's **Settings > Secrets and variables > Actions**.
4. Add these repository secrets:

```text
TELEGRAM_BOT_TOKEN
TELEGRAM_CHAT_ID
DATABASE_URL
```

The workflow lives at `.github/workflows/memecoin-alerts.yml`. It also supports
manual runs from the **Actions** tab through `workflow_dispatch`.

## Render Alternative

Render works too, but an always-on worker may cost money. If you use Render,
create a Background Worker connected to this repo.

Build command:

```bash
pip install -r requirements.txt
```

Start command:

```bash
python main.py
```
