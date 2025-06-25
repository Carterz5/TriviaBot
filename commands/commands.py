import discord
import mysql.connector
import logging
import asyncio


from discord import app_commands

from core import db
from core import models
from commands.submit_question import QuestionSetupView
from commands.games.coinflip import coin_flip
from commands.games.bakers_dozen import bakers_dozen
from commands.games.trivia_mp import mp_game_loop
from commands.games.trivia_sp import AnswerButtons
from commands.games.slots import slot_machine



def register_commands(tree: discord.app_commands.CommandTree):

    @tree.command(name="hello", description="Say hello!")
    async def hello_command(interaction: discord.Interaction):
        await interaction.response.send_message("Hello!")

    @tree.command(name="mystats", description="Displays users stats!")
    async def my_stats(interaction: discord.Interaction):
        if not db.user_exists(interaction.user.id, interaction.guild_id):
            await interaction.response.send_message("You aren't registered, please use the /register command!")
            return
        
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

    @tree.command(name="askme", description="Play a game of trivia by yourself!")
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
        view = AnswerButtons(question, interaction.user.id)
        await interaction.response.send_message(embed=embed, view=view)
        view.message = await interaction.original_response()



    @tree.command(name="askus", description="Play a game of trivia with friends!")
    @app_commands.describe(rounds= "How many rounds you want to play!")
    async def askus(interaction: discord.Interaction, rounds: int):

        if not db.user_exists(interaction.user.id, interaction.guild_id):
            await interaction.response.send_message("You aren't registered, please use the /register command!")
            return


        asyncio.create_task(mp_game_loop(interaction, rounds))


    @tree.command(name="coinflip", description="Bet your points on a coin flip!")
    @app_commands.describe(bet= "How many points you want to bet")
    
    async def coinflip(interaction: discord.Interaction, bet: int):
        if not db.user_exists(interaction.user.id, interaction.guild_id):
            await interaction.response.send_message("You aren't registered, please use the /register command!")
            return
        user = models.row_to_user(db.fetch_user(interaction.user.id, interaction.guild.id))
        if bet < 1:
            await interaction.response.send_message("You must bet more than 0 points!")
            return

        if user.points < bet:
            await interaction.response.send_message("You don't have that many points!")
            return
        
        
        asyncio.create_task(coin_flip(interaction, bet))

    @tree.command(name="slots", description="Bet your points on a coin flip!")
    @app_commands.describe(bet= "How many points you want to bet")
    
    async def slots(interaction: discord.Interaction, bet: int):
        if not db.user_exists(interaction.user.id, interaction.guild_id):
            await interaction.response.send_message("You aren't registered, please use the /register command!")
            return
        user = models.row_to_user(db.fetch_user(interaction.user.id, interaction.guild.id))
        if bet < 1:
            await interaction.response.send_message("You must bet more than 0 points!")
            return

        if user.points < bet:
            await interaction.response.send_message("You don't have that many points!")
            return
        
        
        asyncio.create_task(slot_machine(interaction, bet))



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
        
        asyncio.create_task(bakers_dozen(interaction, bet=bet))

    @tree.command(name="submit_question", description="Submit your own trivia question!")
    async def submit_question(interaction: discord.Interaction):
        if not db.user_exists(interaction.user.id, interaction.guild_id):
            await interaction.response.send_message("You aren't registered, please use the /register command!")
            return
        
        view = QuestionSetupView()
        await interaction.response.send_message("Choose difficulty and category:", view=view, ephemeral=True)

    @tree.command(name="help", description="Get a list of all commands and what they do.")
    async def help(interaction: discord.Interaction):
        embed = discord.Embed(
            title="Help",
            description=None,
            color=discord.Color.blurple()
        )
        embed.add_field(name="/askme",value="Play a game of trivia by yourself.",inline=False)
        embed.add_field(name="/askus",value="Play a game of trivia with friends.",inline=False)
        embed.add_field(name="/bakersdozen",value="Play a game of bakersdozen.",inline=False)
        embed.add_field(name="/coinflip",value="Gamble your points on the outcome of a coinflip.",inline=False)
        embed.add_field(name="/hello",value="Say hello.",inline=False)
        embed.add_field(name="/help",value="Shows this info.",inline=False)
        embed.add_field(name="/mystats",value="Display a message with all your stats.",inline=False)
        embed.add_field(name="/register",value="Register yourself as a player. This allows tracking of stats.",inline=False)
        embed.add_field(name="/slots",value="Gamble your points on the outcome of a slot machine.",inline=False)
        embed.add_field(name="/submit_question",value="Submit your own question into the trivia database.",inline=False)

        await interaction.response.send_message(embed=embed)