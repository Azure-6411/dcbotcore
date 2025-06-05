import discord
from discord.ext import commands
from discord import app_commands
from PIL import Image, ImageDraw, ImageFont
from io import BytesIO
import os

TRASH_IMAGE_PATH = "trash-pandemic-covid-19-01.png"  # Make sure this file is present or update path
OUTPUT_DIR = "trash_shame"  # Folder to save trashed user images

class TrashBot(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        os.makedirs(OUTPUT_DIR, exist_ok=True)

    @commands.command(name="trashpile")
    @commands.has_permissions(manage_messages=True)
    async def trashpile(self, ctx, member: discord.Member):
        await self.trash_user(member, ctx.channel, ctx)

    @trashpile.error
    async def trashpile_error(self, ctx, error):
        if isinstance(error, commands.MissingPermissions):
            await ctx.send("❌ You don't have permission to use this command.")
        else:
            await ctx.send("⚠️ Unexpected error.")
            print("[Trashpile Command Error]", error)

    @app_commands.command(name="trashpile", description="Trash a user by generating a funny image.")
    @app_commands.describe(member="The member to trash")
    async def TrashStuffPile(self, interaction: discord.Interaction, member: discord.Member):
        if not interaction.user.guild_permissions.manage_messages:
            await interaction.response.send_message("❌ You don't have permission to use this command.", ephemeral=True)
            return
        await self.trash_user(member, interaction.channel, interaction)
    
    @TrashStuffPile.error
    async def TrashStuffPile_error(self, interaction: discord.Interaction, error):
        await interaction.response.send_message("⚠️ Something went wrong with the slash command.", ephemeral=True)
        print("[Slash Trashpile Error]", error)

    async def trash_user(self, member: discord.Member, channel: discord.TextChannel, ctx_or_interaction=None):
        try:
            base = Image.open(TRASH_IMAGE_PATH).convert("RGBA")

            pfp_bytes = await member.display_avatar.read()
            pfp_img = Image.open(BytesIO(pfp_bytes)).convert("RGBA").resize((200, 200))

            base.paste(pfp_img, (900, 900), pfp_img)

            draw = ImageDraw.Draw(base)
            font = ImageFont.load_default()
            text = f"🚫 Caught Trashin': {member.name}"
            draw.text((860, 1120), text, font=font, fill="white")

            file_obj = BytesIO()
            base.save(file_obj, format="PNG")
            file_obj.seek(0)

            embed = discord.Embed(
                title="🗑️ User Trashed!",
                description=f"{member.mention} has been officially dumped in the pile.",
                color=discord.Color.dark_red(),
            )

            if ctx_or_interaction is None:
                await channel.send(embed=embed, file=discord.File(file_obj, filename=f"{member.id}_trash.png"))
            else:
                # Check if ctx_or_interaction is commands.Context or discord.Interaction
                if isinstance(ctx_or_interaction, commands.Context):
                    await ctx_or_interaction.send(embed=embed, file=discord.File(file_obj, filename=f"{member.id}_trash.png"))
                else:
                    await ctx_or_interaction.response.send_message(embed=embed, file=discord.File(file_obj, filename=f"{member.id}_trash.png"))

        except Exception as e:
            if ctx_or_interaction is None:
                await channel.send("⚠️ Something went wrong trashing the user.")
            else:
                if isinstance(ctx_or_interaction, commands.Context):
                    await ctx_or_interaction.send("⚠️ Something went wrong trashing the user.")
                else:
                    await ctx_or_interaction.response.send_message("⚠️ Something went wrong trashing the user.", ephemeral=True)
            print("[TrashUser Error]", e)

    @commands.Cog.listener()
    async def on_message_delete(self, message):
        if message.author.bot:
            return
        if message.mentions:
            mentioned_users = ", ".join(user.mention for user in message.mentions)
            await message.channel.send(f"👻 Ghost ping detected! {message.author.mention} mentioned {mentioned_users} and deleted the message.")
            await self.trash_user(message.author, message.channel)

async def setup(bot):
    cog = TrashBot(bot)
    await bot.add_cog(cog)
    # Register slash command globally
    bot.tree.add_command(cog.TrashStuffPile)
