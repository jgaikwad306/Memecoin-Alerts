# Codex Project Context: Solana Memecoin Telegram Alert Bot

## Project Goal

Build a Python MVP that finds new/trending Solana memecoins, checks each token with RugCheck, and sends Telegram alerts when a token passes basic safety and momentum filters.

This bot is **alert-only**. It should **not** buy, sell, sign transactions, store wallet private keys, or execute trades.

## High-Level Architecture

```text
DexScreener Poller
        ↓
Basic Token Filters
        ↓
RugCheck Score Lookup
        ↓
Final Alert Filter
        ↓
Telegram Alert Sender
        ↓
SQLite Logging
```

## Core User Story

As a user, I want the bot to monitor new Solana memecoins and send me Telegram alerts with token name, address, RugCheck score, liquidity, volume, market cap, age, and links, so I can manually decide whether to investigate the coin.

## Suggested Tech Stack

- Python 3.11+
- `requests` or `httpx`
- `python-dotenv`
- `sqlite3` built-in for MVP
- `time` loop or `APScheduler`
- Telegram Bot API via HTTP
- Optional later: `pandas`, `SQLAlchemy`, `FastAPI`, `Streamlit`

## External Services

### DexScreener

Purpose:
- Discover new/trending/token-profile data.
- Pull token metadata, pair data, liquidity, volume, FDV/market cap, and DexScreener links.

Base idea:
- Use DexScreener public REST API endpoints.
- Focus on Solana only.
- Respect documented rate limits.

Useful API areas:
- Latest token profiles
- Latest boosted tokens
- Token pairs by token address
- Search pairs if needed

### RugCheck

Purpose:
- Take a Solana token mint address and return token safety/scam analysis.
- Use RugCheck’s own score/report as the main MVP safety signal.

Expected endpoint pattern:
```http
GET https://api.rugcheck.xyz/v1/tokens/{token_mint}/report
```

Codex should verify the exact response shape from the API/docs before hardcoding field names.

Important:
- RugCheck score should be treated as a signal, not a guarantee.
- The bot should still display important fields so the user can manually review.

### Telegram Bot API

Purpose:
- Send formatted alert messages to the user.

Expected endpoint:
```http
POST https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage
```

Required environment variables:
```env
TELEGRAM_BOT_TOKEN=
TELEGRAM_CHAT_ID=
```

## MVP Folder Structure

```text
memecoin-alert-bot/
  README.md
  .env.example
  requirements.txt
  src/
    main.py
    config.py
    dexscreener.py
    rugcheck.py
    filters.py
    telegram_bot.py
    db.py
    models.py
    utils.py
  data/
    bot.sqlite3
```

## Environment Variables

Create `.env.example`:

```env
TELEGRAM_BOT_TOKEN=replace_me
TELEGRAM_CHAT_ID=replace_me

POLL_INTERVAL_SECONDS=15

MIN_RUGCHECK_SCORE=80
MIN_LIQUIDITY_USD=5000
MIN_VOLUME_5M_USD=10000
MAX_PAIR_AGE_MINUTES=10
MIN_MARKET_CAP_USD=25000
MAX_MARKET_CAP_USD=500000

DEXSCREENER_BASE_URL=https://api.dexscreener.com
RUGCHECK_BASE_URL=https://api.rugcheck.xyz
```

## Data Model

Use SQLite for MVP.

### `tokens_seen`

Columns:
- `id` integer primary key
- `chain_id` text
- `token_address` text unique
- `pair_address` text
- `name` text
- `symbol` text
- `first_seen_at` text
- `last_checked_at` text
- `dex_url` text
- `rugcheck_url` text
- `rugcheck_score` real nullable
- `liquidity_usd` real nullable
- `volume_5m_usd` real nullable
- `market_cap_usd` real nullable
- `pair_age_minutes` real nullable
- `alerted` integer default 0
- `raw_dex_json` text nullable
- `raw_rugcheck_json` text nullable

## Basic Filtering Logic

Before RugCheck call, filter noisy tokens:

```python
def passes_basic_filters(pair):
    return (
        pair.chain_id == "solana"
        and pair.age_minutes <= MAX_PAIR_AGE_MINUTES
        and pair.liquidity_usd >= MIN_LIQUIDITY_USD
        and pair.volume_5m_usd >= MIN_VOLUME_5M_USD
        and MIN_MARKET_CAP_USD <= pair.market_cap_usd <= MAX_MARKET_CAP_USD
    )
```

After RugCheck:

```python
def passes_rugcheck_filter(report):
    return report.score >= MIN_RUGCHECK_SCORE
```

For the MVP, do not create custom ML scoring. Use RugCheck’s score plus simple DexScreener liquidity/volume/age filters.

## Telegram Alert Format

Send a message like:

```text
🚀 New Solana Meme Alert

Name: {name} ({symbol})
RugCheck Score: {score}/100
Liquidity: ${liquidity_usd}
5m Volume: ${volume_5m_usd}
Market Cap/FDV: ${market_cap_usd}
Age: {pair_age_minutes} min

Token:
{token_address}

DexScreener:
{dex_url}

RugCheck:
https://rugcheck.xyz/tokens/{token_address}

Not financial advice. Manually verify before trading.
```

## Main Loop Pseudocode

```python
def main():
    init_db()

    while True:
        try:
            pairs = get_candidate_solana_pairs()

            for pair in pairs:
                if has_seen_token(pair.token_address):
                    continue

                save_seen_token(pair)

                if not passes_basic_filters(pair):
                    continue

                report = get_rugcheck_report(pair.token_address)
                update_token_with_rugcheck(pair.token_address, report)

                if passes_rugcheck_filter(report):
                    send_telegram_alert(pair, report)
                    mark_alerted(pair.token_address)

        except Exception as exc:
            log_error(exc)

        sleep(POLL_INTERVAL_SECONDS)
```

## Important Implementation Notes for Codex

1. Keep this bot alert-only.
2. Never request or store wallet seed phrases, private keys, or trading credentials.
3. Do not add auto-buy or auto-sell functionality.
4. Use environment variables for secrets.
5. Add timeouts to all HTTP requests.
6. Add retry/backoff for temporary API failures.
7. Respect API rate limits.
8. Deduplicate tokens using SQLite so the bot does not spam repeated alerts.
9. Log skipped tokens and reasons for debugging.
10. Do not assume RugCheck field names. Inspect response shape and handle missing fields safely.
11. Treat DexScreener `fdv` as market cap fallback if true market cap is missing.
12. Use defensive parsing because meme token data is often incomplete.

## Error Handling Requirements

The bot should not crash permanently if:
- DexScreener is down.
- RugCheck is down.
- Telegram send fails.
- A token response is missing liquidity or volume fields.
- JSON response shape changes.
- SQLite duplicate insert occurs.

Use structured logging:
```text
[INFO] Found candidate token...
[SKIP] Failed liquidity filter...
[SKIP] RugCheck score too low...
[ALERT] Sent Telegram alert...
[ERROR] RugCheck request failed...
```

## Possible First Milestones

### Milestone 1: Print candidates only
- Pull Solana token/pair data.
- Print name, token address, liquidity, volume, and DexScreener URL.

### Milestone 2: Add SQLite dedupe
- Store seen tokens.
- Do not process same token twice.

### Milestone 3: Add RugCheck lookup
- Query RugCheck report by token mint.
- Print score and major risk warnings.

### Milestone 4: Add Telegram alerts
- Send alert only when score and filters pass.

### Milestone 5: Add logging and config
- Move thresholds to `.env`.
- Add better error handling and logs.

## Later Enhancements

- Paper trading simulator.
- Track token price after alert at 5m, 15m, 1h, 4h.
- Backtest which filters would have worked.
- Add holder growth tracking.
- Add whale/dev wallet monitoring.
- Add Streamlit dashboard.
- Add Discord alerts.
- Add Helius or Solana websocket feed for faster discovery.
- Add custom risk score on top of RugCheck.

## README Requirements

The README should include:
- What the project does.
- What it does not do.
- Setup instructions.
- How to create a Telegram bot with BotFather.
- How to get `TELEGRAM_CHAT_ID`.
- How to run locally.
- Example alert screenshot/message.
- Risk disclaimer.

## Safety / Risk Disclaimer

This tool is for educational and research purposes only. It does not provide financial advice, does not guarantee scam detection, and should not execute trades automatically. Memecoins are extremely risky and can lose most or all value quickly.
