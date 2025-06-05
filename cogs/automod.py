import discord
from discord.ext import commands, tasks
import json
import asyncio
from datetime import datetime, timedelta

class AutoMod(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.rules = self.load_rules()
        self.cooldowns = {}
        self.load_config()

    def load_rules(self):
        try:
            with open("automod_rules.json", "r") as f:
                return json.load(f)
        except FileNotFoundError:
            return {}

    def save_rules(self):
        with open("automod_rules.json", "w") as f:
            json.dump(self.rules, f, indent=4)

    def load_config(self):
        try:
            with open("config.json", "r") as f:
                self.config = json.load(f)
        except FileNotFoundError:
            self.config = {"log_channel": None}

    async def log_action(self, guild, message, reason):
        log_channel_id = self.config.get("log_channel")
        if not log_channel_id:
            return
        channel = guild.get_channel(log_channel_id)
        if channel:
            await channel.send(f"[AutoMod] {message.author.mention} triggered rule: {reason}\nContent: `{message.content}`")

    def is_on_cooldown(self, user_id):
        now = datetime.utcnow()
        if user_id in self.cooldowns:
            cooldown_end = self.cooldowns[user_id]
            if now < cooldown_end:
                return True
        return False

    def set_cooldown(self, user_id, seconds=10):
        self.cooldowns[user_id] = datetime.utcnow() + timedelta(seconds=seconds)

    @commands.Cog.listener()
    async def on_message(self, message):
        if message.author.bot:
            return

        if self.is_on_cooldown(message.author.id):
            return

        for rule in self.rules.values():
            for keyword in rule["keywords"]:
                if keyword.lower() in message.content.lower():
                    action = rule.get("action", "delete")
                    reason = rule.get("reason", keyword)
                    if action == "delete":
                        await message.delete()
                    elif action == "warn":
                        await message.channel.send(f"{message.author.mention}, please avoid saying that.", delete_after=5)
                    elif action == "timeout":
                        if isinstance(message.author, discord.Member):
                            until = discord.utils.utcnow() + timedelta(seconds=30)
                            await message.author.timeout(until, reason=reason)

                    await self.log_action(message.guild, message, reason)
                    self.set_cooldown(message.author.id)
                    return

    @commands.command()
    @commands.has_permissions(manage_messages=True)
    async def addrule(self, ctx, name: str, action: str, *, keywords: str):
        """Add a new AutoMod rule."
        Actions: delete, warn, timeout"""
        self.rules[name] = {
            "action": action.lower(),
            "keywords": [k.strip() for k in keywords.split(",")],
            "reason": f"Rule {name} triggered"
        }
        self.save_rules()
        await ctx.send(f"Rule `{name}` added with action `{action}`.")

    @commands.command()
    @commands.has_permissions(manage_messages=True)
    async def removerule(self, ctx, name: str):
        """Remove an AutoMod rule by name."""
        if name in self.rules:
            del self.rules[name]
            self.save_rules()
            await ctx.send(f"Rule `{name}` removed.")
        else:
            await ctx.send("No such rule found.")

    @commands.command()
    async def listrules(self, ctx):
        """List all active AutoMod rules."""
        if not self.rules:
            await ctx.send("No rules active.")
            return
        desc = ""
        for name, rule in self.rules.items():
            desc += f"**{name}** — `{rule['action']}` for: {', '.join(rule['keywords'])}\n"
        await ctx.send(desc)

    @commands.command()
    @commands.has_permissions(administrator=True)
    async def setlog(self, ctx, channel: discord.TextChannel):
        """Set the AutoMod log channel."""
        self.config["log_channel"] = channel.id
        with open("config.json", "w") as f:
            json.dump(self.config, f, indent=4)
        await ctx.send(f"Log channel set to {channel.mention}")


def setup(bot):
    bot.add_cog(AutoMod(bot))