import discord
from discord.ext import commands
from discord import app_commands
from discord.ui import View, Select
from PIL import Image, ImageDraw, ImageFont, ImageFilter
from io import BytesIO
import json
import os

CONFIG_FILE = "welcome_config.json"
WELCOME_IMAGE_PATH = "Assets/WelcomeTrash.png"

# Ensure config file exists
if not os.path.exists(CONFIG_FILE):
    with open(CONFIG_FILE, "w") as f:
        json.dump({}, f)

def load_config():
    with open(CONFIG_FILE, "r") as f:
        return json.load(f)

def save_config(data):
    with open(CONFIG_FILE, "w") as f:
        json.dump(data, f, indent=4)

def get_text_size(font, text):
    bbox = font.getbbox(text)
    width = bbox[2] - bbox[0]
    height = bbox[3] - bbox[1]
    return width, height

def draw_text_with_background(draw, position, text, font, padding=10):
    text_width, text_height = get_text_size(font, text)
    x, y = position

    bg_x0 = x - padding
    bg_y0 = y - padding
    bg_x1 = x + text_width + padding
    bg_y1 = y + text_height + padding

    temp_img = Image.new("RGBA", (bg_x1 - bg_x0, bg_y1 - bg_y0), (0, 0, 0, 0))
    temp_draw = ImageDraw.Draw(temp_img)

    radius = padding
    # Draw rounded red background
    temp_draw.ellipse((0, 0, radius*2, radius*2), fill=(255, 0, 0, 255))
    temp_draw.ellipse((temp_img.width - radius*2, 0, temp_img.width, radius*2), fill=(255, 0, 0, 255))
    temp_draw.ellipse((0, temp_img.height - radius*2, radius*2, temp_img.height), fill=(255, 0, 0, 255))
    temp_draw.ellipse((temp_img.width - radius*2, temp_img.height - radius*2, temp_img.width, temp_img.height), fill=(255, 0, 0, 255))

    temp_draw.rectangle([radius, 0, temp_img.width - radius, temp_img.height], fill=(255, 0, 0, 255))
    temp_draw.rectangle([0, radius, temp_img.width, temp_img.height - radius], fill=(255, 0, 0, 255))

    outline_img = temp_img.filter(ImageFilter.MaxFilter(5))
    # Paste outline behind
    draw.bitmap((bg_x0, bg_y0), outline_img, fill=None)
    # Paste background
    draw.bitmap((bg_x0, bg_y0), temp_img, fill=None)
    # Draw text on top
    draw.text((x, y), text, font=font, fill="black")

class ChannelDropdown(Select):
    def __init__(self, bot, guild):
        options = [
            discord.SelectOption(label=ch.name, value=str(ch.id))
            for ch in guild.text_channels if ch.permissions_for(guild.me).send_messages
        ]
        super().__init__(placeholder="Select a channel for welcome messages...", options=options)
        self.bot = bot
        self.guild = guild

    async def callback(self, interaction: discord.Interaction):
        chosen_channel_id = int(self.values[0])
        config = load_config()
        config[str(self.guild.id)] = {"welcome_channel": chosen_channel_id}
        save_config(config)

        await interaction.response.send_message(
            f"✅ Welcome channel set to <#{chosen_channel_id}>!",
            ephemeral=True
        )

class SetupWelcomeView(View):
    def __init__(self, bot, guild):
        super().__init__(timeout=60)
        self.add_item(ChannelDropdown(bot, guild))

class WelcomeCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="welcomesetup", description="Set the welcome channel")
    @app_commands.checks.has_permissions(administrator=True)
    async def welcomesetup(self, interaction: discord.Interaction):
        """Slash command to setup welcome channel"""
        await interaction.response.send_message(
            "👇 Select the channel where welcome messages will be sent:",
            view=SetupWelcomeView(self.bot, interaction.guild),
            ephemeral=True
        )

    @welcomesetup.error
    async def welcomesetup_error(self, interaction: discord.Interaction, error):
        if isinstance(error, app_commands.errors.MissingPermissions):
            await interaction.response.send_message("❌ You need Administrator permissions to use this command.", ephemeral=True)
        else:
            await interaction.response.send_message("⚠️ An error occurred.", ephemeral=True)

    @commands.Cog.listener()
    async def on_member_join(self, member):
        config = load_config()
        guild_conf = config.get(str(member.guild.id))
        if not guild_conf:
            return  # no config set yet

        channel = member.guild.get_channel(guild_conf["welcome_channel"])
        if not channel:
            return

        try:
            base = Image.open(WELCOME_IMAGE_PATH).convert("RGBA")

            avatar_bytes = await member.display_avatar.read()
            avatar_img = Image.open(BytesIO(avatar_bytes)).convert("RGBA").resize((200, 200))

            outline = Image.new("RGBA", (210, 210), (0, 0, 0, 255))
            outline.paste(avatar_img, (5, 5), avatar_img)
            base.paste(outline, (30, 180), outline)

            draw = ImageDraw.Draw(base)
            font = ImageFont.truetype("arial.ttf", 40)

            welcome_text = f"Welcome to {member.guild.name}!\nGet trashed soon."
            draw_text_with_background(draw, (260, 200), welcome_text, font)

            invite_info = "Invited by unknown"
            try:
                invites = await member.guild.invites()
                for inv in invites:
                    if inv.inviter and inv.uses:
                        invite_info = f"Invited by {inv.inviter.name} | Link used {inv.uses} times"
                        break
            except:
                pass

            draw_text_with_background(draw, (30, 350), invite_info, font)

            buffer = BytesIO()
            base.save(buffer, format="PNG")
            buffer.seek(0)

            file = discord.File(buffer, filename="welcome.png")
            await channel.send(content=f"Welcome {member.mention}! 🗑️", file=file)

        except Exception as e:
            print("[Welcome Error]", e)

    @app_commands.command(name="testwelcome", description="Send a test welcome message")
    @app_commands.checks.has_permissions(administrator=True)
    @app_commands.describe(member="Member to simulate joining (defaults to you)")
    async def testwelcome(self, interaction: discord.Interaction, member: discord.Member = None):
        member = member or interaction.user

        config = load_config()
        guild_conf = config.get(str(interaction.guild.id))
        if not guild_conf:
            await interaction.response.send_message("❌ Welcome channel is not set. Use `/welcomesetup` first.", ephemeral=True)
            return

        channel = interaction.guild.get_channel(guild_conf["welcome_channel"])
        if not channel:
            await interaction.response.send_message("❌ The configured welcome channel doesn't exist or is invalid.", ephemeral=True)
            return

        try:
            base = Image.open(WELCOME_IMAGE_PATH).convert("RGBA")

            avatar_bytes = await member.display_avatar.read()
            avatar_img = Image.open(BytesIO(avatar_bytes)).convert("RGBA").resize((200, 200))

            outline = Image.new("RGBA", (210, 210), (0, 0, 0, 255))
            outline.paste(avatar_img, (5, 5), avatar_img)
            base.paste(outline, (30, 180), outline)

            draw = ImageDraw.Draw(base)
            font = ImageFont.truetype("arial.ttf", 40)

            welcome_text = f"Welcome to {interaction.guild.name}!\nGet trashed soon."
            draw_text_with_background(draw, (260, 200), welcome_text, font)

            invite_info = "Invited by unknown"
            draw_text_with_background(draw, (30, 350), invite_info, font)

            buffer = BytesIO()
            base.save(buffer, format="PNG")
            buffer.seek(0)

            file = discord.File(buffer, filename="welcome.png")
            await channel.send(content=f"Welcome {member.mention}! 🗑️ (Test welcome)", file=file)

            await interaction.response.send_message(f"✅ Sent test welcome message in {channel.mention}", ephemeral=True)

        except Exception as e:
            print("[Test Welcome Error]", e)
            await interaction.response.send_message(f"❌ Failed to send test welcome: {e}", ephemeral=True)

async def setup(bot):
    await bot.add_cog(WelcomeCog(bot))
