#!/usr/bin/env python3
"""CLI for Claude Code to interact with the Discord bot's message queue."""

import argparse
import json
import os
import sqlite3
import sys
import time

DB_PATH = os.path.join(os.path.dirname(__file__), "messages.db")


def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def check(args):
    """Show unread messages."""
    conn = get_db()
    rows = conn.execute(
        "SELECT id, channel_id, channel_name, author, content, timestamp FROM inbox WHERE read = 0 ORDER BY timestamp"
    ).fetchall()
    conn.close()

    if not rows:
        print("No new messages.")
        return

    for row in rows:
        ts = time.strftime("%H:%M:%S", time.localtime(row["timestamp"]))
        print(f"[{row['id']}] {ts} #{row['channel_name']} | {row['author']}: {row['content']}")


def read(args):
    """Mark messages as read."""
    conn = get_db()
    if args.all:
        conn.execute("UPDATE inbox SET read = 1 WHERE read = 0")
    elif args.id:
        placeholders = ",".join("?" * len(args.id))
        conn.execute(f"UPDATE inbox SET read = 1 WHERE id IN ({placeholders})", args.id)
    conn.commit()
    conn.close()
    print("Marked as read.")


def send(args):
    """Queue a message to send to Discord."""
    conn = get_db()
    conn.execute(
        "INSERT INTO outbox (channel_id, content) VALUES (?, ?)",
        (args.channel, args.message),
    )
    conn.commit()
    conn.close()
    print(f"Queued message to channel {args.channel}.")


def channels(args):
    """List channels that have sent messages."""
    conn = get_db()
    rows = conn.execute(
        "SELECT DISTINCT channel_id, channel_name FROM inbox ORDER BY channel_name"
    ).fetchall()
    conn.close()

    if not rows:
        print("No channels seen yet.")
        return

    for row in rows:
        print(f"{row['channel_id']} #{row['channel_name']}")


def main():
    parser = argparse.ArgumentParser(description="Discord bot message CLI")
    sub = parser.add_subparsers(dest="command")

    sub.add_parser("check", help="Show unread messages")

    read_p = sub.add_parser("read", help="Mark messages as read")
    read_p.add_argument("--all", action="store_true", help="Mark all as read")
    read_p.add_argument("id", nargs="*", type=int, help="Message IDs to mark read")

    send_p = sub.add_parser("send", help="Send a message to a channel")
    send_p.add_argument("channel", help="Channel ID")
    send_p.add_argument("message", help="Message content")

    sub.add_parser("channels", help="List known channels")

    args = parser.parse_args()

    if args.command == "check":
        check(args)
    elif args.command == "read":
        read(args)
    elif args.command == "send":
        send(args)
    elif args.command == "channels":
        channels(args)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
