from discord import app_commands
from discord.ext import commands
import discord

BADGE_EMOJIS = {
    "staff": "<:DiscordStaffBadge:1379523370152099912>",
    "partner": "<:Discordpartnerserverowner:1379523368319189165>",
    "hypesquad": "<:HypesquadEvents:1379523384366338049>",
    "bug_hunter": "<:DiscordBugHunter:1379523362287521912>",
    "bug_hunter_level_2": "<:GoldenBughunterbadge:1379523374614581509>",
    "hypesquad_bravery": "<:HypesquadBraveryHouse:1379523379400544336>",
    "hypesquad_brilliance": "<:Hypesquadbrilliancehouse:1379523382441410651>",
    "hypesquad_balance": "<:HypesquadBalancehouse:1379523377399730437>",
    "verified_bot": "<:Discordearlyverifiedbotbadge:1379523364716281976>",
    "early_supporter": "<:EarlySupporter:1379523371800465559>",
    "verified_bot_developer": "<:Discordearlyverifiedbotbadge:1379523364716281976>",
    "active_developer": "<:DiscordActiveDeveloper:1379523359540514836>",
    "discord_certified_moderator": "<:Discordmodprogramalumnibadge:1379523366670827661>"
}

class ProfileCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="avatar", description="Show someone's avatar in full size.")
    @app_commands.describe(user="The user to show avatar of")
    async def avatar(self, interaction: discord.Interaction, user: discord.User = None):
        user = user or interaction.user
        avatar_url = user.display_avatar.url
        embed = discord.Embed(
            title=f"{user.name}'s Avatar",
            color=discord.Color.blurple()
        )
        embed.set_image(url=avatar_url)
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="profile", description="Show detailed info about a user.")
    @app_commands.describe(user="The user to show profile of")
    async def profile(self, interaction: discord.Interaction, user: discord.User = None):
        await interaction.response.defer()
        user = user or interaction.user
        embed = discord.Embed(
            title=f"{user.name}'s Profile",
            color=discord.Color.blurple()
        )
        embed.set_thumbnail(url=user.display_avatar.url)
        embed.add_field(name="Username", value=f"{user}", inline=True)
        embed.add_field(name="ID", value=f"`{user.id}`", inline=True)
        embed.add_field(name="Bot?", value="🤖 Yes" if user.bot else "👤 No", inline=True)
        embed.add_field(name="Created", value=discord.utils.format_dt(user.created_at, style='F'), inline=False)

        flags = user.public_flags
        badge_text = []
        for flag in discord.UserFlags.__members__:
            if getattr(flags, flag, False):
                emoji = BADGE_EMOJIS.get(flag, "🏅")
                badge_text.append(f"{emoji} {flag.replace('_', ' ').title()}")
        if badge_text:
            embed.add_field(name="Badges", value="\n".join(badge_text), inline=False)

        if isinstance(user, discord.Member):
            if user.joined_at:
                embed.add_field(name="Joined Server", value=discord.utils.format_dt(user.joined_at, style='F'), inline=False)
            embed.add_field(name="Status", value=str(user.status).title(), inline=True)

            roles = [role.mention for role in user.roles if role.name != "@everyone"]
            if roles:
                embed.add_field(name=f"Roles [{len(roles)}]", value=", ".join(roles), inline=False)

            for activity in user.activities:
                if isinstance(activity, discord.Game):
                    embed.add_field(name="🎮 Playing", value=activity.name, inline=False)
                elif isinstance(activity, discord.Spotify):
                    embed.add_field(name="🎵 Listening to", value=f"{activity.title} by {activity.artist}", inline=False)
                elif isinstance(activity, discord.CustomActivity):
                    embed.add_field(name="💬 Status", value=activity.name or activity.state, inline=False)

        await interaction.followup.send(embed=embed)

async def setup(bot):
    await bot.add_cog(ProfileCog(bot))
