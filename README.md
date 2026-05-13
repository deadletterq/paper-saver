# Paper-Saver Telegram Bot

A Telegram bot that runs on a Raspberry Pi Zero 2W. Send it a URL, get back a clean, print-optimized PDF — stripped of images, ads, navigation, and clutter — formatted to save paper.

## What It Does

1. User sends a URL via Telegram
2. Bot fetches the page (HTTP only, no browser)
3. Extracts main article content using Reader Mode algorithm
4. Strips images, fixes margins, applies print-friendly typography
5. Renders to PDF and saves it locally

## Constraints & Design Decisions

- **HTML-only**: No headless browser. Works on server-rendered content (articles, blogs, docs, wikis, recipes). Will not work on SPAs (Twitter, Instagram, etc.) — this is an accepted tradeoff for running on 512MB RAM.
- **Python**: Best fit for the Pi Zero 2W and the available libraries.
- **Single-file bot**: Simple to deploy and maintain. No database needed.

## Tech Stack

| Component | Library | Purpose |
|---|---|---|
| Telegram interface | `python-telegram-bot` (v20+, async) | Bot framework |
| HTTP client | `httpx` | Fetch URLs, follow redirects, handle encoding |
| Content extraction | `readability-lxml` | Firefox Reader Mode algorithm |
| HTML cleanup | `beautifulsoup4` | Remove residual elements (images, scripts) |
| PDF generation | `weasyprint` | Print-optimized HTML → PDF |

## Hardware Target

- Raspberry Pi Zero 2W (512MB RAM, ARM64)
- Raspberry Pi OS Lite (64-bit recommended)

## Setup on Raspberry Pi

```bash
sudo apt update
sudo apt install -y python3-pip python3-venv \
    libpango-1.0-0 libpangoft2-1.0-0 libcairo2 libharfbuzz0b
git clone <this-repo>
cd paper-saver-bot
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
# Edit .env and add your TELEGRAM_BOT_TOKEN
python bot.py
```

Get a bot token from [@BotFather](https://t.me/BotFather) on Telegram.

## Running as a Service

A `systemd` unit file is included to run the bot on boot and restart on failure. See `paper-saver.service`.

```bash
sudo cp paper-saver.service /etc/systemd/system/
sudo systemctl enable --now paper-saver
```

## Project Structure

```
paper-saver-bot/
├── bot.py                  # Main bot entry point
├── fetcher.py              # URL fetching with httpx
├── extractor.py            # Readability + BS4 cleanup
├── pdf_renderer.py         # WeasyPrint + print CSS
├── print_styles.css        # Print-optimized stylesheet
├── requirements.txt
├── .env.example
├── paper-saver.service     # systemd unit
└── README.md
```

---

## Prompt for Claude Code

Copy everything below this line into Claude Code to build the project.

---

Build a complete Telegram bot project called `paper-saver-bot` according to the specification in this README. The bot runs on a Raspberry Pi Zero 2W and converts web articles to print-friendly PDFs.

### Requirements

**Core functionality:**
- Accept URLs sent as messages to the bot
- Reply with a PDF of the article, stripped of images and ads, with print-optimized margins and typography
- Handle errors gracefully and reply to the user with helpful messages (invalid URL, fetch failed, no extractable content, etc.)
- Show a "Working on it..." message while processing, then edit it or follow up with the PDF

**Architecture:**
- Use `python-telegram-bot` v20+ with async/await throughout
- Split into the modules listed in the Project Structure section above
- Each module should have a single clear responsibility and be independently testable
- No global state. Pass config explicitly.

**Fetcher (`fetcher.py`):**
- Use `httpx.AsyncClient` with a 15-second timeout
- Send a realistic User-Agent and standard Accept headers
- Follow redirects
- Reject non-HTML responses (check Content-Type)
- Reject responses larger than 5MB to protect the Pi
- Return the decoded HTML string and the final URL after redirects

**Extractor (`extractor.py`):**
- Use `readability-lxml` to extract the main article body and title
- Post-process with BeautifulSoup to:
    - Remove all `<img>`, `<picture>`, `<figure>`, `<video>`, `<iframe>`, `<svg>` elements
    - Remove all `<script>` and `<style>` tags
    - Strip inline `style` attributes
    - Unwrap `<a>` tags so links become plain text (saves clutter when printed)
- Return a dict with `title`, `content_html`, and `source_url`

**PDF Renderer (`pdf_renderer.py`):**
- Use WeasyPrint to render the cleaned HTML to PDF
- Wrap the extracted content in a minimal HTML template that includes:
    - The article title as `<h1>`
    - A small source URL line beneath the title
    - The article content
    - A footer with the date generated
- Load print CSS from `print_styles.css` (do not inline it in Python)
- Write the PDF to a temporary file and return the path
- Make sure temp files are cleaned up after the bot sends them

**Print CSS (`print_styles.css`):**
- A4 page size with 2cm margins
- Body: Georgia or similar serif, 11pt, line-height 1.5
- H1: 18pt; H2: 14pt; H3: 12pt
- Hide images defensively (`img, figure { display: none; }`)
- Black text on white, no background colors
- Avoid orphans/widows (`orphans: 3; widows: 3;`)
- Sensible page-break rules so headings don't get stranded
- Source URL styled small and gray

**Bot (`bot.py`):**
- Read `TELEGRAM_BOT_TOKEN` from a `.env` file using `python-dotenv`
- `/start` command: explain what the bot does in 2-3 sentences
- `/help` command: same as `/start`
- Default message handler: detect URLs in the message text using a simple regex, process the first valid URL found
- If the message contains no URL, reply with a friendly hint
- Use logging (Python's `logging` module) at INFO level, log to stdout so systemd captures it
- On any unhandled exception, log the traceback and send the user a generic error message — never crash

**Configuration:**
- `.env.example` with `TELEGRAM_BOT_TOKEN=your_token_here`
- `requirements.txt` pinned to known-working major versions
- `paper-saver.service` systemd unit file targeting a user named `pi`, working directory `/home/pi/paper-saver-bot`, running `.venv/bin/python bot.py`, with `Restart=on-failure` and `RestartSec=10`

### Quality Bar

- Type hints on all function signatures
- Docstrings on all public functions and modules
- No bare `except:` clauses — catch specific exceptions
- Clean separation between async code (bot, fetcher) and sync code (extractor, renderer); call sync code via `asyncio.to_thread` from the bot handler so it doesn't block the event loop
- Keep the total dependency footprint small — only the libraries listed in the Tech Stack table

### Deliverables

Create all files listed in the Project Structure section, plus a working `.env.example`. Do not create a `.env` file with a real token. Do not write tests in this pass — keep the focus on a clean, deployable v1.

When done, print a summary of what was built and the exact commands the user needs to run on the Pi to deploy it.