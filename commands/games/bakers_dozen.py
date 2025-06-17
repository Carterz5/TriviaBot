import discord
import logging
import asyncio
import time
import random



from core import db
from core import models




async def bakers_dozen(interaction: discord.Interaction, bet: int):
    players = dict()
    game_start = int(time.time())
    starter = interaction.user.id
    view=bd_buttons(players, bet, starter)
    embed = discord.Embed(
        title=" Click join to get in on the fun!",
        description=f"<@{starter}> has set the buy in at {bet} points!",
        color=discord.Color.blurple()
    )
    for user, data in players.items():
        bet = data["Bet"]
        embed.add_field(
            name=f"Player",
            value=f"<@{user}>",
            inline=False
        )

    await interaction.response.send_message(content=f"🍞 Baker's Dozen! game starts <t:{game_start + 15}:R>", embed=embed, view=view)
    message = await interaction.original_response()
    view.message = await interaction.original_response()
    
    await asyncio.sleep(16)
    game_start = int(time.time())

    # Disable buttons
    for item in view.children:
        if isinstance(item, discord.ui.Button):
            item.disabled = True

    if not players:
        await view.message.edit(content="Nobody Joined! Baker's Dozen has expired.", view=view)
        return
    
    view.start()
    await view.message.edit(content=f"🍞 Baker's Dozen! game ends <t:{game_start + 30}:R>")
    await view.update_embed()
    view.message = message

    await asyncio.sleep(31)


    # Step 1: Filter out busted players
    valid_players = {
        user: data
        for user, data in players.items()
        if data["Score"] <= 13
    }

    # Step 2: Find highest valid score
    winner_ids = []
    winning_score = None
    if valid_players:
        # Get the highest valid score
        winning_score = max(data["Score"] for data in valid_players.values())
        # Get all users with that score
        winner_ids = [
            user for user, data in valid_players.items()
            if data["Score"] == winning_score
        ]

    # Step 3: Build embed showing all players
    embed = discord.Embed(
        title="🍞 Baker's Dozen - Results!",
        description="Final scores below:",
        color=discord.Color.gold()
    )

    for user, data in players.items():
        true_score = data["Score"]
        
        if true_score > 13:
            score_display = "BUST"
        else:
            score_display = str(true_score)

        embed.add_field(
            name="Player",
            value=f"<@{user}> Final Score: {score_display}",
            inline=False
        )

    # Step 4: Add winners section
    if winner_ids:
        winnings = (len(players) * bet) / len(winner_ids)
        mentions = ", ".join(f"<@{user}>" for user in winner_ids)
        embed.add_field(
            name=f"🏆 Winner(s) each recieve {winnings} points!",
            value=f"{mentions} with a score of **{winning_score}**!",
            inline=False
        )
    else:
        embed.add_field(
            name="No Winner 😢",
            value="Everyone busted!",
            inline=False
        )

    # Step 5: Update the message
    await interaction.edit_original_response(content="Baker's Dozen is over!", embed=embed, view=None)

    if winner_ids:
        
        for id in winner_ids:
            user = models.row_to_user(db.fetch_user(id, interaction.guild.id))
            user.points += int(winnings)
            user.gambling_winnings += (int(winnings) - bet)
            db.update_user(user)

    loser_ids = [player_id for player_id in players if player_id not in winner_ids]
    if loser_ids:
        for id in loser_ids:
            user = models.row_to_user(db.fetch_user(id, interaction.guild.id))
            user.gambling_losses += bet
            db.update_user(user)


class bd_buttons(discord.ui.View):
    def __init__(self, players, entry, starter, timeout=60):
        super().__init__(timeout=timeout)
        self.players = players
        self.entry = entry
        self.starter = starter
        # Create join button
        self.add_item(bd_join())
        self.add_item(bd_howto())
       
    async def update_embed(self):
        embed = discord.Embed(
            title="Game Has Started!",
            description=f"Try to roll a total of 13 without going over! Closest Wins!",
            color=discord.Color.blurple()
        )
        for user, data in self.players.items():
            
            score = data["Score"] - data["Hidden"]
            if data["Score"] > 13:
                embed.add_field(
                name=f"Player:",
                value=f"<@{user}> Score: BUST",
                inline=False
                )
            elif data.get("Stay") == 1:
                embed.add_field(
                    name=f"Player:",
                    value=f"<@{user}> Score: {score}, STAYING",
                    inline=False
                )
            else:
                embed.add_field(
                    name=f"Player:",
                    value=f"<@{user}> Score: {score}",
                    inline=False
                )


        await self.message.edit(embed=embed, view=self)

    def start(self):
        self.clear_items()
        self.add_item(bd_roll())
        self.add_item(bd_stay())
        
    async def on_timeout(self):
        logging.info("Bakers Dozen timed out")
        for item in self.children:
            item.disabled = True

        if self.message:
            await self.message.edit(view=None)

class bd_roll(discord.ui.Button):
    def __init__(self):
        super().__init__(style=discord.ButtonStyle.primary, label="Roll!")

    async def callback(self, interaction: discord.Interaction):
        if interaction.user.id not in self.view.players:
            await interaction.response.send_message("You are not playing!", ephemeral=True)
            return
        if self.view.players[interaction.user.id]["Score"] > 13:
            await interaction.response.send_message("You already busted!, you cannot roll anymore", ephemeral=True)
            return
        if self.view.players[interaction.user.id].get("Stay") == 1:
            await interaction.response.send_message("You have chosen to stay, and can no longer roll", ephemeral=True)
            return

        roll = random.randint(1, 6)
        self.view.players[interaction.user.id]["Score"] += roll
        emoji_map = {1: "1️⃣", 2: "2️⃣", 3: "3️⃣", 4: "4️⃣", 5: "5️⃣", 6: "6️⃣"}
        roll_emoji = emoji_map[roll]
        if self.view.players[interaction.user.id]["Score"] > 13:
            await interaction.response.send_message(f"You rolled a {roll_emoji}! You're new total is {self.view.players[interaction.user.id]["Score"]}! You have busted!", ephemeral=True)
        else:
            await interaction.response.send_message(f"You rolled a {roll_emoji}! You're new total is {self.view.players[interaction.user.id]["Score"]}", ephemeral=True)

        await self.view.update_embed()

class bd_stay(discord.ui.Button):
    def __init__(self):
        super().__init__(style=discord.ButtonStyle.primary, label="Stay!")

    async def callback(self, interaction: discord.Interaction):
        if interaction.user.id not in self.view.players:
            await interaction.response.send_message("You are not playing!", ephemeral=True)
            return
        else:
            self.view.players[interaction.user.id]["Stay"] = 1
            await interaction.response.defer()

        await self.view.update_embed()

class bd_join(discord.ui.Button):
    def __init__(self):
        super().__init__(style=discord.ButtonStyle.primary, label="Join")
    

    async def callback(self, interaction: discord.Interaction):
        if not db.user_exists(interaction.user.id, interaction.guild_id):
            await interaction.response.send_message("You aren't registered, please use the /register command!")
            return
        user = models.row_to_user(db.fetch_user(interaction.user.id, interaction.guild.id))
        if user.points < self.view.entry:
            await interaction.response.send_message("You don't have enough points!")
            return
        
        if interaction.user.id in self.view.players:
            await interaction.response.send_message("You're already playing!", ephemeral=True)
            return
        else:
            hidden_roll = random.randint(1, 6)
            roll = random.randint(1, 6)
            emoji_map = {1: "1️⃣", 2: "2️⃣", 3: "3️⃣", 4: "4️⃣", 5: "5️⃣", 6: "6️⃣"}
            roll_emoji = emoji_map[roll]
            hidden_roll_emoji = emoji_map[hidden_roll]
            self.view.players[interaction.user.id] = {"Score": roll+hidden_roll, "Hidden": hidden_roll}
            await interaction.response.send_message(f"Your hidden roll is: {hidden_roll_emoji}, public roll of {roll_emoji}, with a total of: {self.view.players[interaction.user.id]["Score"]}.\nDo not share this info with the other players!", ephemeral=True)


        embed = discord.Embed(
            title="Click join to get in on the fun!",
            description=f"<@{self.view.starter}> has set the buy in at {self.view.entry} points!\n The pot is now {len(self.view.players) * self.view.entry} points!",
            color=discord.Color.blurple()
        )
        for id, data in self.view.players.items():
            embed.add_field(
                name=f"Player",
                value=f"<@{id}>",
                inline=False
            )
        
        await self.view.message.edit(embed=embed)

        user.points -= int(self.view.entry)
        db.update_user(user)



class bd_howto(discord.ui.Button):
    def __init__(self):
        super().__init__(style=discord.ButtonStyle.primary, label="How to play")
    

    async def callback(self, interaction: discord.Interaction):
        await interaction.response.send_message(
            content="Bakers dozen is a dice game similar to blackjack." \
            " Each player rolls 2d6, keeping one d6 secret. Everyone is able to see the other players current total, minus their secret die." \
            "\nAfter rolling, players can either roll an additional d6, or stay." \
            " You can roll as many additional dice as you wish.\nThe goal is to get as close to, or exactly, 13 - a baker's dozen. Going over means you lose!\n" \
            "After everyone has finished rolling, the players true totals are revealed! The player with the closest score to 13, without going over, wins!",
            ephemeral=True
        )



