# disclaude

Discord ↔ Claude Code bridge. Remote-control a Claude Code CLI session via Discord messages.

## How it works

A Discord bot (`bot.py`) listens for messages and stores them in a local SQLite database. An injector (`injector.py`) polls the database and types incoming messages into a tmux session running Claude Code via `send-keys`. Claude can respond back to Discord using the CLI tool (`cli.py`).

```
Discord ──→ bot.py ──→ SQLite ──→ injector.py ──→ tmux (Claude Code)
                        ↑                              │
                        └──── cli.py send ◄────────────┘
```

## Setup

1. Copy `.env_template` to `.env` and fill in your bot token:
   ```
   cp .env_template .env
   ```

2. Ensure `tmux` and `claude` (Claude Code CLI) are installed.

3. Python dependencies (`discord.py`, `python-dotenv`) are handled automatically — see below.

## Usage

### Quick start (tmux mode)

```bash
./disclaude.sh
```

On first run, the script checks for the required Python modules. If they're missing, it offers to create a virtual environment (`.venv/`) and install them automatically. On subsequent runs it reuses the existing venv. You can also set up the venv manually:

```bash
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt
```

This starts the bot, injector, and Claude Code in a tmux session. Attach with:
```bash
tmux attach -t disclaude
```

### Manual / component-by-component

Start the bot:
```bash
python3 bot.py
```

Use the CLI to interact with the message queue:
```bash
python3 cli.py check              # Show unread messages
python3 cli.py channels           # List known channels
python3 cli.py send <channel_id> "message"  # Send a message
python3 cli.py read --all         # Mark all as read
```

### Claude Code skill

When running via `disclaude.sh`, the `/disclaude` Claude Code skill activates Discord response mode. The injector feeds incoming messages directly into Claude's tmux session, and the skill tells Claude how to parse them and reply via `cli.py send`. No polling needed — it's push-based. Install the skill by placing `SKILL.md` in `~/.claude/skills/disclaude/`.

## Files

| File | Purpose |
|------|---------|
| `bot.py` | Discord bot — listens for messages, writes to SQLite inbox |
| `cli.py` | CLI for Claude to read inbox, send replies, list channels |
| `injector.py` | Polls inbox and injects messages into a tmux Claude session |
| `disclaude.sh` | Launcher — starts bot + injector + Claude in tmux |
| `.env_template` | Template for required environment variables |
| `requirements.txt` | Python dependencies |

## License

MIT — see [LICENSE](LICENSE).
