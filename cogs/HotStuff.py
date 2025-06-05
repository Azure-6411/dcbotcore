import discord
from discord.ext import commands
import aiohttp

class AutoModManager(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name="automod")
    @commands.has_permissions(administrator=True)
    async def create_automod_rules(self, ctx):
        """Create up to 5 AutoMod keyword rules (admin only)"""
        await ctx.send("Creating AutoMod rules...")

        guild_id = ctx.guild.id
        bot_token = self.bot.http.token

        # Define up to 5 keyword rules
        keyword_rules = [
            {"name": "No Swearing", "keywords": ["badword1", "badword2"]},
            {"name": "No Spam Links", "keywords": ["buy now", "free nitro"]},
            {"name": "No Discord Invites", "keywords": ["discord.gg/"]},
            {"name": "No Slurs", "keywords": ["slur1", "slur2"]},
            {"name": "No Caps Rage", "keywords": ["AAAAAAAA", "OMGOMG"]}
        ]

        created = 0

        async with aiohttp.ClientSession() as session:
            for rule in keyword_rules:
                payload = {
                    "name": rule["name"],
                    "event_type": 1,  # MESSAGE_SEND
                    "trigger_type": 1,  # KEYWORD
                    "trigger_metadata": {
                        "keyword_filter": rule["keywords"]
                    },
                    "enabled": True,
                    "actions": [
                        {
                            "type": 1,  # BLOCK_MESSAGE
                            "metadata": {
                                "custom_message": "🚫 AutoMod: Your message was blocked!"
                            }
                        }
                    ]
                }

                url = f"https://discord.com/api/v10/guilds/{guild_id}/auto-moderation/rules"
                headers = {
                    "Authorization": f"Bot {bot_token}",
                    "Content-Type": "application/json"
                }

                async with session.post(url, json=payload, headers=headers) as resp:
                    if resp.status == 201:
                        created += 1
                    else:
                        error = await resp.text()
                        await ctx.send(f"Failed to create rule `{rule['name']}`: {resp.status} — {error}")

        await ctx.send(f"✅ Created {created} AutoMod rule(s).")

    @create_automod_rules.error
    async def automod_error(self, ctx, error):
        if isinstance(error, commands.MissingPermissions):
            await ctx.send("❌ You must be an admin to use this command.")
        else:
            await ctx.send(f"An error occurred: {error}")

async def setup(bot):
    await bot.add_cog(AutoModManager(bot))
