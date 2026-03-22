import asyncio
import discord
import json
import os
import sqlite3
import time

from dotenv import load_dotenv

load_dotenv()

DB_PATH = os.path.join(os.path.dirname(__file__), "messages.db")


def init_db():
    conn = sqlite3.connect(DB_PATH)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS inbox (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            channel_id TEXT NOT NULL,
            channel_name TEXT,
            author TEXT NOT NULL,
            content TEXT NOT NULL,
            timestamp REAL NOT NULL,
            read INTEGER DEFAULT 0
        )
    """)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS outbox (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            channel_id TEXT NOT NULL,
            content TEXT NOT NULL,
            sent INTEGER DEFAULT 0
        )
    """)
    conn.commit()
    conn.close()


intents = discord.Intents.default()
intents.message_content = True
client = discord.Client(intents=intents)


@client.event
async def on_ready():
    print(f"Bot is online as {client.user}")


@client.event
async def setup_hook():
    client.loop.create_task(poll_outbox())


@client.event
async def on_message(message):
    if message.author == client.user:
        return

    conn = sqlite3.connect(DB_PATH)
    conn.execute(
        "INSERT INTO inbox (channel_id, channel_name, author, content, timestamp) VALUES (?, ?, ?, ?, ?)",
        (
            str(message.channel.id),
            getattr(message.channel, "name", "DM"),
            str(message.author),
            message.content,
            time.time(),
        ),
    )
    conn.commit()
    conn.close()
    print(f"[inbox] {message.channel.name} | {message.author}: {message.content}")


async def poll_outbox():
    await client.wait_until_ready()
    while not client.is_closed():
        try:
            conn = sqlite3.connect(DB_PATH)
            rows = conn.execute(
                "SELECT id, channel_id, content FROM outbox WHERE sent = 0"
            ).fetchall()

            for row_id, channel_id, content in rows:
                channel = client.get_channel(int(channel_id))
                if channel:
                    # Split long messages (Discord limit is 2000 chars)
                    while content:
                        chunk = content[:2000]
                        content = content[2000:]
                        await channel.send(chunk)
                    conn.execute("UPDATE outbox SET sent = 1 WHERE id = ?", (row_id,))
                    conn.commit()
                    print(f"[outbox] sent message {row_id} to {channel_id}")
                else:
                    print(f"[outbox] channel {channel_id} not found")

            conn.close()
        except Exception as e:
            print(f"[outbox] error: {e}")

        await asyncio.sleep(2)


def main():
    init_db()
    client.run(os.environ["BOT_TOKEN"])


if __name__ == "__main__":
    main()
