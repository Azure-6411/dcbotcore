import discord
from discord.ext import commands
from discord import app_commands
import json
import os

DATA_FILE = "cloud_data.json"

def load_data():
    if not os.path.exists(DATA_FILE):
        return {}
    with open(DATA_FILE, "r") as f:
        return json.load(f)

def save_data(data):
    with open(DATA_FILE, "w") as f:
        json.dump(data, f, indent=2)

class Cloud(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.data = load_data()

    @app_commands.command(name="upload", description="Upload a file link to your cloud")
    @app_commands.describe(label="Label for your file", attachment="Upload the file")
    async def upload(self, interaction: discord.Interaction, label: str, attachment: discord.Attachment):
        user_id = str(interaction.user.id)
        self.data.setdefault(user_id, {})[label] = attachment.url
        save_data(self.data)
        await interaction.response.send_message(f"✅ Uploaded `{label}` to your cloud.", ephemeral=True)

    @app_commands.command(name="list", description="List your uploaded files")
    async def list_files(self, interaction: discord.Interaction):
        user_id = str(interaction.user.id)
        files = self.data.get(user_id, {})
        if not files:
            await interaction.response.send_message("❌ You have no files uploaded.", ephemeral=True)
            return

        options = [
            discord.SelectOption(label=label, description=url[:100]) for label, url in files.items()
        ]

        select = discord.ui.Select(placeholder="Select a file", options=options)

        async def callback(i: discord.Interaction):
            label = select.values[0]
            await i.response.send_message(f"📎 **{label}**: {files[label]}", ephemeral=True)

        select.callback = callback
        view = discord.ui.View()
        view.add_item(select)

        embed = discord.Embed(
            title=f"{interaction.user.name}'s Cloud Files",
            description="Select one below to get its link.",
            color=discord.Color.blurple()
        )
        await interaction.response.send_message(embed=embed, view=view, ephemeral=True)

async def setup(bot):
    await bot.add_cog(Cloud(bot))
