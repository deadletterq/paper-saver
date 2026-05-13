# Paper Saver

A Telegram bot that turns web articles into clean, print-friendly PDFs.

Send it a URL. Get back a PDF stripped of images, ads, navigation, and pop-ups — formatted to save paper and ink when you actually print it. Designed to run on a Raspberry Pi Zero 2W sitting on your home network.

## How it works

1. You send a URL to the bot in Telegram.
2. It fetches the page over plain HTTP (no headless browser).
3. It extracts the main article body using the same Reader Mode algorithm Firefox uses.
4. It strips images, scripts, link underlines, and inline styling.
5. It renders the result to a print-optimized A4 PDF and sends it back.

## What it works on

Server-rendered pages: news articles, blogs, documentation, wikis, recipes, long-form essays.

**Not** SPAs (Twitter/X, Instagram, anything that needs JavaScript to render content). This is an accepted tradeoff — running a headless browser on 512 MB of RAM is not worth it. If you need that, point a different tool at it.

## Why it exists

Printing a web article straight from the browser wastes paper on navigation chrome, wastes ink on hero images and ad backgrounds, and gives you tiny body text wrapped around floated junk. This bot exists to print articles like articles.

## Tech stack

| Component | Library |
|---|---|
| Bot framework | `python-telegram-bot` (async, v22+) |
| HTTP client | `httpx` |
| Content extraction | `readability-lxml` |
| HTML cleanup | `beautifulsoup4` |
| PDF rendering | `weasyprint` |
| Packaging | `uv` + `hatchling` |

The codebase is structured as ports & adapters (hexagonal): the `ConvertUrlToPdf` use case in `application/` depends only on port interfaces, with concrete adapters for Telegram, httpx, readability, and WeasyPrint wired up at the composition root in `app.py`.

## Running it

Target hardware: Raspberry Pi Zero 2W (ARM64), Raspberry Pi OS Lite.

### Deploy to a Pi

```bash
cp .env.example .env
# Fill in TELEGRAM_BOT_TOKEN (from @BotFather) and RPI_HOST / RPI_USER / RPI_PASSWORD.
./scripts/deploy.sh
```

`scripts/deploy.sh` installs system dependencies, syncs the source tree with `rsync --delete`, runs `uv sync` on the Pi, and installs a systemd unit (`paper-saver.service`) that restarts on failure.

Follow the logs with:

```bash
ssh pi@raspberrypi.local 'journalctl -u paper-saver -f'
```

### Run locally

```bash
uv sync
echo "TELEGRAM_BOT_TOKEN=..." > .env
uv run paper-saver
```

## Tests

```bash
uv run pytest
```
