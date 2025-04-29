import discord
import mysql.connector
import logging
import json


import db
import models

from models import Question
from models import User






class AnswerButtons(discord.ui.View):
    def __init__(self, question: Question, timeout=30):
        super().__init__(timeout=timeout)
        self.question = question
        self.response = None

        # Create buttons based on the number of answers
        option_letters = ['A', 'B', 'C', 'D', 'E', 'F', 'G']
        for i, _ in enumerate(self.question.answers):
            if i >= len(option_letters):
                break
            label = option_letters[i]
            self.add_item(AnswerButton(label=label, index=i))
    
    async def on_timeout(self):
        logging.info("Trivia timed out!")

class AnswerButton(discord.ui.Button):
    def __init__(self, label: str, index: int):
        super().__init__(style=discord.ButtonStyle.primary, label=label)
        self.index = index

    async def callback(self, interaction: discord.Interaction):
        question: Question = self.view.question
        is_correct = (self.index == question.correct_index)

        # Disable all buttons after answer
        for item in self.view.children:
            item.disabled = True

        if is_correct:
            await interaction.response.edit_message(content="✅ Correct!", view=self.view)
        else:
            correct_letter = ['A', 'B', 'C', 'D', 'E', 'F', 'G'][question.correct_index]
            await interaction.response.edit_message(
                content=f"❌ Wrong! Correct answer was **{correct_letter}**.",
                view=self.view
            )



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


        try:
            result = db.fetch_random_question()

        except mysql.connector.Error as e:
            await interaction.response.send_message("❌ Error finding question. Try again later.", ephemeral=True)
       
        
        question = models.row_to_question(result)
        embed = question.to_embed()


        view = AnswerButtons(question)


        await interaction.response.send_message(embed=embed, view=view)
