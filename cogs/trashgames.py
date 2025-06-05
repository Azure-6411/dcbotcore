import discord
from discord.ext import commands
from discord import app_commands
from discord.ui import Button, View, Select
import random

GUILD_ID = 1375977504703119430  # Your guild ID

# === TrashAvoidGame ===
class TrashAvoidGame(View):
    """3x3 button grid; avoid the trash tile and safely click max_safe times."""
    def __init__(self, player: discord.User, max_safe_clicks=5):
        super().__init__(timeout=60)
        self.player = player
        self.max_safe = max_safe_clicks
        self.safe_clicks = 0
        self.trash_index = random.randint(0, 8)

        for i in range(9):
            btn = Button(style=discord.ButtonStyle.secondary, emoji="🟩", custom_id=str(i))
            btn.callback = self.button_click
            self.add_item(btn)

        self.message = None

    async def button_click(self, interaction: discord.Interaction):
        if interaction.user != self.player:
            await interaction.response.send_message("This isn't your game, chill!", ephemeral=True)
            return

        button_index = int(interaction.data['custom_id'])
        if button_index == self.trash_index:
            for item in self.children:
                item.disabled = True
                if int(item.custom_id) == self.trash_index:
                    item.style = discord.ButtonStyle.danger
                    item.emoji = "💩"
                else:
                    item.style = discord.ButtonStyle.secondary
                    item.emoji = "⬜"
            await interaction.response.edit_message(content=f"💥 Oh no, {self.player.mention} fell in the trash! Game Over!", view=self)
            self.stop()
        else:
            self.safe_clicks += 1
            if self.safe_clicks >= self.max_safe:
                for item in self.children:
                    item.disabled = True
                    if int(item.custom_id) == self.trash_index:
                        item.style = discord.ButtonStyle.secondary
                        item.emoji = "💩"
                    else:
                        item.style = discord.ButtonStyle.success
                        item.emoji = "✅"
                await interaction.response.edit_message(content=f"🎉 Congrats {self.player.mention}, you dodged the trash and won!", view=self)
                self.stop()
            else:
                for item in self.children:
                    if int(item.custom_id) == button_index:
                        item.disabled = True
                        item.style = discord.ButtonStyle.success
                        item.emoji = "✅"
                await interaction.response.edit_message(content=f"🟢 Safe! {self.safe_clicks}/{self.max_safe} safe clicks. Keep avoiding trash!", view=self)

    async def on_timeout(self):
        for item in self.children:
            item.disabled = True
        try:
            await self.message.edit(content="⏰ Time's up! Game ended.", view=self)
        except Exception:
            pass
        self.stop()

# === TrashStoryGame ===
class TrashStoryGame(View):
    """Branching story game with choices leading to different endings."""
    def __init__(self, player: discord.User):
        super().__init__(timeout=120)
        self.player = player

        self.stages = {
            0: {
                "Sacrifice your soul": 1,
                "Embrace love": 2,
                "Betray a friend": 3,
                "Stay cold-hearted": 4
            },
            1: {
                "Fight the darkness": 5,
                "Run away": 6,
                "Accept fate": "ending1",
                "Call for help": "ending2"
            },
            2: {
                "Confess feelings": 7,
                "Hide emotions": 8,
                "Protect loved ones": "ending3",
                "Lose yourself": "ending4"
            },
            3: {
                "Backstab carefully": 9,
                "Go loud": "ending5",
                "Double-cross again": "ending6",
                "Repent": "ending7"
            },
            4: {
                "Freeze your heart": "ending8",
                "Build walls": "ending9",
                "Break down": "ending10",
                "Stay numb": "ending8"
            },
            5: {}, 6: {}, 7: {}, 8: {}, 9: {},
        }

        self.endings = {
            "ending1": "You accepted your dark fate. The shadows consume you forever.",
            "ending2": "Help arrived too late. Darkness claimed the night.",
            "ending3": "Your love protected many, shining like a beacon.",
            "ending4": "Lost in love, you forgot who you were.",
            "ending5": "Your loud betrayal destroyed trust beyond repair.",
            "ending6": "Double-crossing again, you sealed your doom.",
            "ending7": "Repentance gave you a chance to start anew.",
            "ending8": "Your cold heart kept you alive, but lonely.",
            "ending9": "Building walls kept others out, and you in solitude.",
            "ending10": "Breaking down led to unexpected peace."
        }

        self.current_stage = 0
        self.update_buttons_for_stage(self.current_stage)
        self.message = None

    def update_buttons_for_stage(self, stage_key):
        self.clear_items()
        options = self.stages.get(stage_key, {})
        for label, next_key in options.items():
            btn = Button(label=label, style=discord.ButtonStyle.primary)
            btn.callback = self.make_choice_callback(next_key)
            self.add_item(btn)

    def make_choice_callback(self, next_key):
        async def callback(interaction: discord.Interaction):
            if interaction.user != self.player:
                await interaction.response.send_message("This isn't your story to play!", ephemeral=True)
                return

            if isinstance(next_key, int):
                self.current_stage = next_key
                self.update_buttons_for_stage(next_key)
                await interaction.response.edit_message(content=f"📖 Stage {next_key}: What do you choose?", view=self)
            else:
                ending_text = self.endings.get(next_key, "The story ends here.")
                for item in self.children:
                    item.disabled = True
                await interaction.response.edit_message(content=f"🏁 {ending_text}", view=self)
                self.stop()
        return callback

    async def on_timeout(self):
        for item in self.children:
            item.disabled = True
        try:
            await self.message.edit(content="⏰ Time's up! Story ended.", view=self)
        except Exception:
            pass
        self.stop()

# === Difficulty Select for TicTacToe ===
class DifficultySelect(View):
    """Dropdown menu to select TicTacToe AI difficulty."""
    def __init__(self, player: discord.User):
        super().__init__(timeout=30)
        self.player = player
        self.selected = None

        options = [
            discord.SelectOption(label="Easy", description="Random moves", value="easy"),
            discord.SelectOption(label="Medium", description="Basic strategy", value="medium"),
            discord.SelectOption(label="Hard", description="Unbeatable AI", value="hard"),
        ]

        self.select = Select(placeholder="Select AI Difficulty", options=options)
        self.select.callback = self.select_callback
        self.add_item(self.select)
        self.message = None

    async def select_callback(self, interaction: discord.Interaction):
        if interaction.user != self.player:
            await interaction.response.send_message("This isn't your menu!", ephemeral=True)
            return
        self.selected = self.select.values[0]
        self.stop()
        await interaction.response.edit_message(content=f"Difficulty selected: **{self.selected.capitalize()}**. Starting game...", view=None)

    async def on_timeout(self):
        try:
            await self.message.edit(content="⏰ Time's up! Difficulty selection ended.", view=None)
        except Exception:
            pass
        self.stop()

# === TicTacToeGame ===
class TicTacToeGame(View):
    """Classic TicTacToe vs AI with selectable difficulty and buttons as board."""
    def __init__(self, player: discord.User, difficulty='easy'):
        super().__init__(timeout=120)
        self.player = player
        self.current_turn = 'X'  # Player always 'X'
        self.board = [' '] * 9
        self.difficulty = difficulty
        self.game_over = False
        self.message = None

        for i in range(9):
            btn = Button(label=' ', style=discord.ButtonStyle.secondary, row=i // 3, custom_id=str(i))
            btn.callback = self.make_move
            self.add_item(btn)

    async def make_move(self, interaction: discord.Interaction):
        if interaction.user != self.player:
            await interaction.response.send_message("This isn't your game!", ephemeral=True)
            return

        if self.game_over:
            await interaction.response.send_message("The game is over!", ephemeral=True)
            return

        idx = int(interaction.data['custom_id'])
        if self.board[idx] != ' ':
            await interaction.response.send_message("That spot is taken!", ephemeral=True)
            return

        # Player move
        self.board[idx] = 'X'
        self.update_buttons()

        if self.check_winner(self.board, 'X'):
            self.game_over = True
            self.disable_all()
            await interaction.response.edit_message(content=f"🎉 {self.player.mention} wins!", view=self)
            return
        elif self.is_draw():
            self.game_over = True
            self.disable_all()
            await interaction.response.edit_message(content="It's a draw!", view=self)
            return

        # AI move
        ai_move = self.get_ai_move()
        self.board[ai_move] = 'O'
        self.update_buttons()

        if self.check_winner(self.board, 'O'):
            self.game_over = True
            self.disable_all()
            await interaction.response.edit_message(content=f"🤖 AI wins! Better luck next time, {self.player.mention}.", view=self)
            return
        elif self.is_draw():
            self.game_over = True
            self.disable_all()
            await interaction.response.edit_message(content="It's a draw!", view=self)
            return

        await interaction.response.edit_message(content=f"{self.player.mention}'s turn (X). Choose your move:", view=self)

    def update_buttons(self):
        for i, btn in enumerate(self.children):
            btn.label = self.board[i]
            btn.style = discord.ButtonStyle.success if self.board[i] == 'X' else \
                        discord.ButtonStyle.danger if self.board[i] == 'O' else discord.ButtonStyle.secondary
            btn.disabled = (self.board[i] != ' ') or self.game_over

    def disable_all(self):
        for btn in self.children:
            btn.disabled = True

    def check_winner(self, board, player_symbol):
        wins = [(0,1,2), (3,4,5), (6,7,8), (0,3,6), (1,4,7), (2,5,8), (0,4,8), (2,4,6)]
        return any(all(board[pos] == player_symbol for pos in line) for line in wins)

    def is_draw(self):
        return all(cell != ' ' for cell in self.board)

    def get_ai_move(self):
        if self.difficulty == 'easy':
            return self.get_random_move()
        elif self.difficulty == 'medium':
            return self.get_medium_move()
        else:
            return self.get_hard_move()

    def get_random_move(self):
        return random.choice([i for i, spot in enumerate(self.board) if spot == ' '])

    def get_medium_move(self):
        # Basic: block player or pick random
        for move in self.get_empty_indices():
            board_copy = self.board[:]
            board_copy[move] = 'O'
            if self.check_winner(board_copy, 'O'):
                return move
        for move in self.get_empty_indices():
            board_copy = self.board[:]
            board_copy[move] = 'X'
            if self.check_winner(board_copy, 'X'):
                return move
        return self.get_random_move()

    def get_hard_move(self):
        _, move = self.minimax(self.board, True)
        return move

    def minimax(self, board, is_maximizing):
        if self.check_winner(board, 'O'):
            return (1, None)
        if self.check_winner(board, 'X'):
            return (-1, None)
        if self.is_draw_board(board):
            return (0, None)

        if is_maximizing:
            best_score = -float('inf')
            best_move = None
            for i in self.get_empty_indices_board(board):
                board[i] = 'O'
                score, _ = self.minimax(board, False)
                board[i] = ' '
                if score > best_score:
                    best_score = score
                    best_move = i
            return best_score, best_move
        else:
            best_score = float('inf')
            best_move = None
            for i in self.get_empty_indices_board(board):
                board[i] = 'X'
                score, _ = self.minimax(board, True)
                board[i] = ' '
                if score < best_score:
                    best_score = score
                    best_move = i
            return best_score, best_move

    def get_empty_indices(self):
        return [i for i, v in enumerate(self.board) if v == ' ']

    def get_empty_indices_board(self, board):
        return [i for i, v in enumerate(board) if v == ' ']

    def is_draw_board(self, board):
        return all(cell != ' ' for cell in board)

# === Main Cog ===
class MinigamesCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="trashavoid", description="Play Trash Avoid game")
    async def trashavoid(self, interaction: discord.Interaction):
        """Start Trash Avoid mini-game."""
        view = TrashAvoidGame(interaction.user)
        message = await interaction.response.send_message(f"{interaction.user.mention}, avoid the trash! Click safely {view.max_safe} times without hitting the trash tile.", view=view)
        view.message = await interaction.original_response()

    @app_commands.command(name="trashstory", description="Play Trash Story game")
    async def trashstory(self, interaction: discord.Interaction):
        """Start Trash Story mini-game."""
        view = TrashStoryGame(interaction.user)
        message = await interaction.response.send_message(f"{interaction.user.mention}, begin your trashy story. Choose wisely.", view=view)
        view.message = await interaction.original_response()

    @app_commands.command(name="tictactoe", description="Play TicTacToe against AI")
    async def tictactoe(self, interaction: discord.Interaction):
        """Select AI difficulty, then start TicTacToe mini-game."""
        difficulty_view = DifficultySelect(interaction.user)
        message = await interaction.response.send_message(f"{interaction.user.mention}, select AI difficulty:", view=difficulty_view)
        difficulty_view.message = await interaction.original_response()

        await difficulty_view.wait()
        if difficulty_view.selected is None:
            await interaction.edit_original_response(content="❌ You didn't select a difficulty in time!", view=None)
            return

        game_view = TicTacToeGame(interaction.user, difficulty=difficulty_view.selected)
        await interaction.edit_original_response(content=f"{interaction.user.mention}, starting TicTacToe on **{difficulty_view.selected.capitalize()}** mode. Your move (X).", view=game_view)
        game_view.message = await interaction.original_response()

async def setup(bot):
    await bot.add_cog(MinigamesCog(bot))
