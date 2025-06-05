import io
import discord
from discord.ext import commands
from discord import app_commands
from playwright.async_api import async_playwright

TEST_GUILD_ID = 1375977504703119430  # Your test server ID

class ScreenshotModal(discord.ui.Modal, title="Enter URL for Screenshot"):
    url = discord.ui.TextInput(
        label="Webpage URL",
        placeholder="https://example.com",
        style=discord.TextStyle.short,
        max_length=200,
    )

    def __init__(self, bot: commands.Bot, interaction: discord.Interaction):
        super().__init__()
        self.bot = bot
        self.interaction = interaction

    async def on_submit(self, interaction: discord.Interaction):
        await interaction.response.defer()
        url = self.url.value

        try:
            async with async_playwright() as p:
                browser = await p.chromium.launch()
                page = await browser.new_page()
                await page.goto(url, timeout=15000)
                screenshot_bytes = await page.screenshot(full_page=True)
                await browser.close()

            file = discord.File(io.BytesIO(screenshot_bytes), filename="screenshot.png")
            await interaction.followup.send(file=file)
        except Exception as e:
            await interaction.followup.send(f"❌ Failed to take screenshot: {e}")

class Screenshot(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(
        name="screenshot",
        description="Take a screenshot of a webpage",
    )
    async def screenshot(self, interaction: discord.Interaction):
        modal = ScreenshotModal(self.bot, interaction)
        await interaction.response.send_modal(modal)

async def setup(bot):
    await bot.add_cog(Screenshot(bot))
