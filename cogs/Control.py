import discord
from discord.ext import commands
from discord import app_commands

OWNER_ID = 1142597052623228928  # Replace with your Discord user ID

class Control(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    # Check if user is owner (used in app commands)
    async def cog_app_command_check(self, interaction: discord.Interaction) -> bool:
        return interaction.user.id == OWNER_ID

    # Normal ping for everyone
    @app_commands.command(name="ping2", description="Check bot latency")
    async def ping2(self, interaction: discord.Interaction):
        latency_ms = round(self.bot.latency * 1000)
        await interaction.response.send_message(f"Pong! Latency: {latency_ms}ms")

    # Owner only commands:

    @app_commands.command(name="say", description="Send a message as the bot (owner only)")
    async def say(self, interaction: discord.Interaction, channel: discord.TextChannel, message: str):
        if interaction.user.id != OWNER_ID:
            await interaction.response.send_message("❌ You are not allowed to use this command.", ephemeral=True)
            return

        await channel.send(message)
        await interaction.response.send_message("✅ Message sent.", ephemeral=True)

    @app_commands.command(name="dm", description="DM a user (owner only)")
    async def dm(self, interaction: discord.Interaction, user: discord.User, message: str):
        if interaction.user.id != OWNER_ID:
            await interaction.response.send_message("❌ You are not allowed to use this command.", ephemeral=True)
            return

        try:
            await user.send(message)
            await interaction.response.send_message(f"📨 DM sent to {user}.", ephemeral=True)
        except discord.Forbidden:
            await interaction.response.send_message("❌ Cannot DM that user.", ephemeral=True)

    @app_commands.command(name="reply", description="Reply to a message by ID (owner only)")
    async def reply(self, interaction: discord.Interaction, message_id: str, content: str):
        if interaction.user.id != OWNER_ID:
            await interaction.response.send_message("❌ You are not allowed to use this command.", ephemeral=True)
            return

        if not interaction.guild:
            await interaction.response.send_message("❌ This command can only be used in a server.", ephemeral=True)
            return

        for channel in interaction.guild.text_channels:
            try:
                msg = await channel.fetch_message(int(message_id))
                await msg.reply(content)
                await interaction.response.send_message("💬 Replied.", ephemeral=True)
                return
            except Exception:
                continue
        await interaction.response.send_message("❌ Message not found.", ephemeral=True)

    @app_commands.command(name="eval", description="Evaluate Python code (owner only, dangerous!)")
    async def eval(self, interaction: discord.Interaction, code: str):
        if interaction.user.id != OWNER_ID:
            await interaction.response.send_message("❌ You are not allowed to use this command.", ephemeral=True)
            return

        try:
            result = eval(code)
            if hasattr(result, '__await__'):
                result = await result
            await interaction.response.send_message(f"✅ `{result}`", ephemeral=True)
        except Exception as e:
            await interaction.response.send_message(f"❌ `{e}`", ephemeral=True)

async def setup(bot: commands.Bot):
    await bot.add_cog(Control(bot))
