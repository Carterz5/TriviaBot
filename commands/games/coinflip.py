import discord
import logging
import random


from core import db
from core import models


async def coin_flip(interaction: discord.Interaction, bet: int):
    players = dict()
    starter = interaction.user.id

    view=cf_buttons(bet, players, starter)

    embed = discord.Embed(
        title="Flip a coin!🪙",
        description=f"<@{starter}> has set the betting at {bet} points!",
        color=discord.Color.blurple()
    )

    await interaction.response.send_message(embed=embed, view=view)
    message = await interaction.original_response()
    view.message = await interaction.original_response()


class cf_buttons(discord.ui.View):
    def __init__(self, bet, players, starter, timeout=60):
        super().__init__(timeout=timeout)
        self.bet = bet
        self.starter = starter
        self.players = players
        # Create join button
        self.add_item(cf_button("Heads"))
        self.add_item(cf_button("Tails"))

    async def update_embed(self):
        embed = discord.Embed(
            title="Flip a coin!🪙",
            description=f"<@{self.starter}> has set the betting at {self.bet} points!",
            color=discord.Color.blurple()
        )
        for user, data in self.players.items():
            if data["Flips"] == 0:
                embed.add_field(
                name=f"Player:",
                value=f"<@{user}> was too poor to flip a coin! 😬 📉",
                inline=False
                )
            else:
                embed.add_field(
                name=f"Player:",
                value=f"<@{user}> Score: {data["Score"]} Flips: {data["Flips"]}",
                inline=False
                )


        await self.message.edit(embed=embed, view=self)       
       
    
    async def on_timeout(self):
        logging.info("Coin flip timed out")
        for item in self.children:
            item.disabled = True

        if self.message:
            await self.message.edit(view=None)


class cf_button(discord.ui.Button):
    def __init__(self, choice):
        super().__init__(style=discord.ButtonStyle.primary, label=f"{choice}")
        self.choice = choice

    async def callback(self, interaction: discord.Interaction):
        if not db.user_exists(interaction.user.id, interaction.guild_id):
            await interaction.response.send_message(content="You aren't registered, please use the /register command!", ephemeral=True)
            return
        
        
        correct_side = random.choice(["Heads", "Tails"])
        user = models.row_to_user(db.fetch_user(interaction.user.id, interaction.guild_id))
        player = self.view.players.setdefault(interaction.user.id, {"Score": 0, "Flips": 0})
        if user.points < self.view.bet:
            await interaction.response.send_message(content="You don't have enough points!", ephemeral=True)
            return
        
        if correct_side == self.choice:
            user.points += self.view.bet
            await interaction.response.send_message(content=f"You guessed right! You have won {self.view.bet} points! Your new balance is {user.points}.", ephemeral=True)
            player["Score"] += self.view.bet
            player["Flips"] += 1
            user.gambling_winnings += self.view.bet
            
        else:
            user.points -= self.view.bet
            await interaction.response.send_message(content=f"You guessed wrong! You have lost {self.view.bet} points! Your new balance is {user.points}.", ephemeral=True)
            player["Score"] -= self.view.bet
            player["Flips"] += 1
            user.gambling_losses += self.view.bet
            
            
        await self.view.update_embed()

        db.update_user(user)