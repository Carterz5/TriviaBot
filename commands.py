import discord
import mysql.connector
import logging
import asyncio
import random

from discord import app_commands

import db
import models
import ui



def register_commands(tree: discord.app_commands.CommandTree):

    @tree.command(name="hello", description="Say hello!")
    async def hello_command(interaction: discord.Interaction):
        await interaction.response.send_message("Hello!")

    @tree.command(name="mystats", description="Displays users stats!")
    async def my_stats(interaction: discord.Interaction):
        user_id = interaction.user.id
        guild_id = interaction.guild.id
        logging.info(f"Fetching stats for user {user_id}, guild {guild_id}")
        try:
            result = db.fetch_user(user_id, guild_id)

        
        except mysql.connector.Error as e:
            await interaction.response.send_message("❌ Could not fetch user's stats.", ephemeral=True)

        user = models.row_to_user(result)
        embed = user.to_embed()

        await interaction.response.send_message(embed=embed)


    # Slash command: /register
    @tree.command(name="register", description="Register yourself in the trivia leaderboard")
    async def register(interaction: discord.Interaction):
        user_id = interaction.user.id
        guild_id = interaction.guild.id
        logging.info(f"Registering user {user_id}, guild {guild_id}")

        try:
            db.add_user(user_id, guild_id)
            await interaction.response.send_message(f"{interaction.user.mention}, you are now registered!", ephemeral=True)

        except mysql.connector.Error as e:
            await interaction.response.send_message("❌ Could not add user to database.", ephemeral=True)

    @tree.command(name="askme", description="Get asked a trivia question!")
    async def askme(interaction: discord.Interaction):
        if not db.user_exists(interaction.user.id, interaction.guild_id):
            await interaction.response.send_message("You aren't registered, please use the /register command!")
            return
        
        try:
            result = db.fetch_random_question()
        except mysql.connector.Error as e:
            await interaction.response.send_message("❌ Error finding question. Try again later.", ephemeral=True)
       
        question = models.row_to_question(result)
        embed = question.to_embed()
        view = ui.AnswerButtons(question)
        await interaction.response.send_message(embed=embed, view=view)
        view.message = await interaction.original_response()



    @tree.command(name="askus", description="Get asked a trivia question!")
    @app_commands.describe(rounds= "How many rounds you want to play!")
    async def askus(interaction: discord.Interaction, rounds: int):

        if not db.user_exists(interaction.user.id, interaction.guild_id):
            await interaction.response.send_message("You aren't registered, please use the /register command!")
            return


        asyncio.create_task(ui.mp_game_loop(interaction, rounds))


        # try:
        #     result = db.fetch_random_question()
        # except mysql.connector.Error as e:
        #     await interaction.response.send_message("❌ Error finding question. Try again later.", ephemeral=True)
       
        # question = models.row_to_question(result)
        # embed = question.to_embed()
        # view = ui.AnswerButtonsMP(question)
        # await interaction.response.send_message(embed=embed, view=view)
        # view.message = await interaction.original_response()

    @tree.command(name="coinflip", description="Bet your points on a coin flip!")
    @app_commands.describe(bet= "How many points you want to bet", guess="Your guess: heads or tails")
    @app_commands.choices(guess=[app_commands.Choice(name="Heads", value="heads"), app_commands.Choice(name="Tails", value="tails")])

    async def coinflip(interaction: discord.Interaction, bet: int, guess: app_commands.Choice[str]):
        if not db.user_exists(interaction.user.id, interaction.guild_id):
            await interaction.response.send_message("You aren't registered, please use the /register command!")
            return
        
        
        
        user = models.row_to_user(db.fetch_user(interaction.user.id, interaction.guild.id))

        if bet < 0:
            await interaction.response.send_message("You can't bet negative points!")
            return

        if user.points < bet:
            await interaction.response.send_message("You don't have that many points!")
            return

        result = random.choice(["heads", "tails"])

        if guess.value == result:
            await interaction.response.send_message(f"🎉 It's {result}! You win {bet} points!")
            user.points += bet
            user.gambling_winnings += bet
        else:
            await interaction.response.send_message(f"😢 It's {result}. You lose {bet} points.")
            user.points -= bet
            user.gambling_losses += bet

        db.update_user(user)


    @tree.command(name="bakersdozen", description="Play Baker's Dozen! (similar to blackjack)")
    @app_commands.describe(bet= "How many points you want to bet")
    async def bakersdozen(interaction: discord.Interaction, bet: int):
        if not db.user_exists(interaction.user.id, interaction.guild_id):
            await interaction.response.send_message("You aren't registered, please use the /register command!")
            return
        user = models.row_to_user(db.fetch_user(interaction.user.id, interaction.guild.id))
        if bet < 0:
            await interaction.response.send_message("You can't bet negative points!")
            return

        if user.points < bet:
            await interaction.response.send_message("You don't have that many points!")
            return
        
        asyncio.create_task(ui.bakers_dozen(interaction, bet=bet))

    @tree.command(name="submit_question", description="Submit your own trivia question!")
    async def submit_question(interaction: discord.Interaction):
        if not db.user_exists(interaction.user.id, interaction.guild_id):
            await interaction.response.send_message("You aren't registered, please use the /register command!")
            return
        
        view = ui.QuestionSetupView()
        await interaction.response.send_message("Choose difficulty and category:", view=view, ephemeral=True)