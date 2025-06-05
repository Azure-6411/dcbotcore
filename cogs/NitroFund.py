import discord
from discord.ext import commands
from discord import app_commands
import json
import os
import random
from datetime import datetime, timedelta

DATA_FILE = "nitro_codes.json"
VOTES_FILE = "nitro_votes.json"
EXPIRATION_DAYS = 30


def load_json(file):
    if not os.path.exists(file):
        return [] if file == DATA_FILE else {}
    with open(file, "r") as f:
        return json.load(f)


def save_json(file, data):
    with open(file, "w") as f:
        json.dump(data, f, indent=2)


def is_valid_code(code: str):
    return 15 <= len(code) <= 24 and all(c.isalnum() or c in "-_" for c in code)


def format_expiration(donated_at_iso: str) -> str:
    donated_at = datetime.fromisoformat(donated_at_iso)
    expire_at = donated_at + timedelta(days=EXPIRATION_DAYS)
    remaining = expire_at - datetime.utcnow()
    if remaining.total_seconds() <= 0:
        return "**Expired**"
    hours = int(remaining.total_seconds() // 3600)
    return f"Expires in {hours} hours"


class NitroVoteView(discord.ui.View):
    def __init__(self, cog, code, donor_id):
        super().__init__(timeout=None)
        self.cog = cog
        self.code = code
        self.donor_id = str(donor_id)

    @discord.ui.button(label="👍 Legit", style=discord.ButtonStyle.success)
    async def legit_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.cog.add_vote(self.code, self.donor_id, True, interaction)

    @discord.ui.button(label="👎 Fake", style=discord.ButtonStyle.danger)
    async def fake_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.cog.add_vote(self.code, self.donor_id, False, interaction)


class NitroDonate(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.codes = load_json(DATA_FILE)
        self.votes = load_json(VOTES_FILE)

    async def add_vote(self, code, donor_id, is_legit, interaction):
        self.votes.setdefault(code, {"up": 0, "down": 0})
        self.votes.setdefault(donor_id, {"up": 0, "down": 0})

        if is_legit:
            self.votes[code]["up"] += 1
            self.votes[donor_id]["up"] += 1
        else:
            self.votes[code]["down"] += 1
            self.votes[donor_id]["down"] += 1

        save_json(VOTES_FILE, self.votes)
        await interaction.response.send_message("✅ Vote registered!", ephemeral=True)

    def get_percent(self, up, down):
        total = up + down
        return 100 if total == 0 else int((up / total) * 100)

    @app_commands.command(name="donatenitro", description="Donate a Nitro gift code to the server pool")
    async def donatenitro(self, interaction: discord.Interaction, code: str):
        await interaction.response.defer(ephemeral=True)
        code = code.strip()

        if not is_valid_code(code):
            await interaction.followup.send("❌ Invalid Nitro code format.", ephemeral=True)
            return

        if any(entry['code'] == code for entry in self.codes):
            await interaction.followup.send("❌ This code has already been donated.", ephemeral=True)
            return

        donated_at = datetime.utcnow().isoformat()
        self.codes.append({
            "code": code,
            "donor_id": interaction.user.id,
            "donated_at": donated_at
        })
        save_json(DATA_FILE, self.codes)
        await interaction.followup.send("🎉 Thank you for donating your Nitro code!", ephemeral=True)

    @app_commands.command(name="claimnitro", description="Claim a random donated Nitro gift code")
    async def claimnitro(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)

        now = datetime.utcnow()
        self.codes = [entry for entry in self.codes if (datetime.fromisoformat(entry['donated_at']) + timedelta(days=EXPIRATION_DAYS)) > now]

        if not self.codes:
            save_json(DATA_FILE, self.codes)
            await interaction.followup.send("❌ All Nitro codes are expired or unavailable.", ephemeral=True)
            return

        entry = random.choice(self.codes)
        self.codes.remove(entry)
        save_json(DATA_FILE, self.codes)

        code = entry['code']
        donor_id = str(entry['donor_id'])
        donor_mention = f"<@{donor_id}>"
        expires_text = format_expiration(entry['donated_at'])

        code_votes = self.votes.get(code, {"up": 0, "down": 0})
        code_legitness = self.get_percent(code_votes['up'], code_votes['down'])

        donor_votes = self.votes.get(donor_id, {"up": 0, "down": 0})
        donor_reputation = self.get_percent(donor_votes['up'], donor_votes['down'])

        embed = discord.Embed(
            title="🎁 Nitro Code Claimed!",
            description=(
                f"`{code}`\n[Redeem Here](https://discord.com/gifts/{code})\n\n"
                f"⏳ {expires_text}\n"
                f"🤖 Legitness: **{code_legitness}%**\n"
                f"👤 Donor Reputation: **{donor_reputation}%**\n"
                f"🙏 Thanks to {donor_mention}!"
            ),
            color=discord.Color.purple()
        )

        await interaction.followup.send(embed=embed, ephemeral=True, view=NitroVoteView(self, code, donor_id))


async def setup(bot):
    await bot.add_cog(NitroDonate(bot))
