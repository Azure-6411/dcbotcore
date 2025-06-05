import discord
from discord.ext import commands
import os
from dotenv import load_dotenv
import asyncio
import sys

# Debug info
print(sys.executable)
print(sys.version)

# Load environment variables
load_dotenv()
DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")

if not DISCORD_TOKEN:
    raise ValueError("DISCORD_TOKEN is missing from the .env file")

# Set up intents and bot
intents = discord.Intents.all()
bot = commands.Bot(command_prefix="!", intents=intents)

@bot.event
async def on_ready():
    print(f"PookieGuard is online as {bot.user}")
    try:
        synced = await bot.tree.sync()  # Global sync
        print(f"🌐 Synced {len(synced)} global commands.")
    except Exception as e:
        print(f"❌ Failed to sync commands: {e}")

async def load_cogs():
    for filename in os.listdir("./cogs"):
        if filename.endswith(".py") and not filename.startswith("_"):
            try:
                await bot.load_extension(f"cogs.{filename[:-3]}")
                print(f"✅ Loaded: {filename}")
            except Exception as e:
                print(f"❌ Failed to load {filename}: {e}")

async def main():
    async with bot:
        await load_cogs()
        await bot.start(DISCORD_TOKEN)

if __name__ == "__main__":
    asyncio.run(main())
