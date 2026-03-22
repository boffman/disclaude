#!/usr/bin/env python3
"""Polls the Discord inbox and injects messages into a tmux session via send-keys."""

import os
import sqlite3
import subprocess
import sys
import time

DB_PATH = os.path.join(os.path.dirname(__file__), "messages.db")
TMUX_SESSION = os.environ.get("DISCLAUDE_TMUX_SESSION", "disclaude")
POLL_INTERVAL = 3  # seconds


def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def inject_message(text):
    """Send text to the tmux session as keyboard input."""
    subprocess.run(
        ["tmux", "send-keys", "-t", TMUX_SESSION, "-l", text],
        check=True,
    )
    # Send Enter key separately (not literal)
    subprocess.run(
        ["tmux", "send-keys", "-t", TMUX_SESSION, "Enter"],
        check=True,
    )


def format_message(row):
    """Format an inbox row into the string injected into Claude."""
    content = row["content"].replace("\n", " ")
    channel_name = row["channel_name"] or "DM"
    return f'[Discord #{channel_name} | {row["author"]} (ch:{row["channel_id"]})]: {content}'


def wait_for_db():
    """Wait until the inbox table exists (created by bot.py)."""
    print("[injector] waiting for database...")
    while True:
        try:
            conn = get_db()
            conn.execute("SELECT 1 FROM inbox LIMIT 1")
            conn.close()
            return
        except Exception:
            time.sleep(1)


def poll():
    """Main polling loop."""
    wait_for_db()
    print(f"[injector] watching inbox, injecting into tmux session '{TMUX_SESSION}'")
    while True:
        try:
            conn = get_db()
            rows = conn.execute(
                "SELECT id, channel_id, channel_name, author, content, timestamp "
                "FROM inbox WHERE read = 0 ORDER BY timestamp"
            ).fetchall()

            for row in rows:
                msg = format_message(row)
                print(f"[injector] injecting: {msg}")
                inject_message(msg)
                conn.execute("UPDATE inbox SET read = 1 WHERE id = ?", (row["id"],))
                conn.commit()
                # Small delay between messages to avoid overwhelming the input
                time.sleep(0.5)

            conn.close()
        except Exception as e:
            print(f"[injector] error: {e}")

        time.sleep(POLL_INTERVAL)


if __name__ == "__main__":
    poll()
