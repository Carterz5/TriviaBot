import discord
import logging
import random

from core import db
from core import models


async def slot_machine(interaction: discord.Interaction, bet: int):
    user_id = interaction.user.id
    guild_id = interaction.guild_id

    if not db.user_exists(user_id, guild_id):
        await interaction.response.send_message(content="You aren't registered. Use `/register` first!", ephemeral=True)
        return

    user = models.row_to_user(db.fetch_user(user_id, guild_id))

    if user.points < bet:
        await interaction.response.send_message(content="You don't have enough points to play!", ephemeral=True)
        return

    view = SlotMachineView(bet, user)
    embed = discord.Embed(
        title="🎰 Slot Machine 🎰",
        description=f"<@{user_id}> is betting **{bet}** points!",
        color=discord.Color.gold()
    )
    embed.add_field(name="Result", value="Press **Pull Lever** to spin!", inline=False)

    await interaction.response.send_message(embed=embed, view=view)
    view.message = await interaction.original_response()


class SlotMachineView(discord.ui.View):
    def __init__(self, bet, user, timeout=60):
        super().__init__(timeout=timeout)
        self.bet = bet
        self.user = user
        self.message = None

        self.add_item(PullLeverButton("Pull Lever"))

    async def on_timeout(self):
        for item in self.children:
            item.disabled = True
        if self.message:
            await self.message.edit(view=None)


class PullLeverButton(discord.ui.Button):
    def __init__(self, label):
        super().__init__(style=discord.ButtonStyle.success, label=label)

    async def callback(self, interaction: discord.Interaction):
        if interaction.user.id != self.view.user.user_id:
            await interaction.response.send_message("This isn't your slot machine!", ephemeral=True)
            return

        user = self.view.user
        bet = self.view.bet

        if user.points < bet:
            await interaction.response.send_message("You don't have enough points to spin!", ephemeral=True)
            return


        emojis = ["🍒", "🍋", "🍉", "⭐", "💎", "🔔"]
        grid = [[random.choice(emojis) for _ in range(3)] for _ in range(3)]

        # Format grid into a string for display
        result_lines = [" | ".join(row) for row in grid]
        grid_display = "\n".join(result_lines)

        # Define paylines to check
        paylines = [
            # Horizontal rows
            [grid[0][0], grid[0][1], grid[0][2]],
            [grid[1][0], grid[1][1], grid[1][2]],
            [grid[2][0], grid[2][1], grid[2][2]],
            # Vertical columns
            [grid[0][0], grid[1][0], grid[2][0]],
            [grid[0][1], grid[1][1], grid[2][1]],
            [grid[0][2], grid[1][2], grid[2][2]],
            # Diagonals
            [grid[0][0], grid[1][1], grid[2][2]],
            [grid[2][0], grid[1][1], grid[0][2]],
        ]

        winnings = 0
        winning_lines = 0

        for line in paylines:
            if line.count(line[0]) == 3:
                winnings += bet * 3
                winning_lines += 1

        if winning_lines == 0:
            winnings = -bet
            outcome = f"😢 No winning lines! You lost {bet} points."
        else:
            outcome = f"🎉 {winning_lines} winning line(s)! You won {bet * 3 * winning_lines} points!"

        # Update user data
        user.points += winnings
        if winnings > 0:
            user.gambling_winnings += winnings
        else:
            user.gambling_losses += bet

        db.update_user(user)

        embed = discord.Embed(
            title="🎰 Slot Machine 🎰",
            description=f"<@{user.user_id}> spun the slots for **{bet}** points!",
            color=discord.Color.gold()
        )
        embed.add_field(name="Result", value=f"```\n{grid_display}\n```", inline=False)
        embed.add_field(name="Outcome", value=outcome, inline=False)
        embed.set_footer(text=f"Your new balance: {user.points} points")

        await interaction.response.edit_message(embed=embed, view=self.view)
