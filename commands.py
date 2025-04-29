import discord
import mysql.connector
import logging
import json


import db

from dataclasses import dataclass
from typing import List
from db import DB_CONFIG

@dataclass
class Question:
    id: int
    prompt: str
    answers: List[str]
    correct_index: int
    difficulty: str
    category: str
    created_by: str

    def is_correct(self, user_choice: str) -> bool:
        user_choice = user_choice.strip().upper()
        choice_to_index = {'A': 0, 'B': 1, 'C': 2, 'D': 3, 'E': 4, 'F': 5, 'G': 6, }
        return choice_to_index.get(user_choice) == self.correct_index
    
    def to_embed(self) -> discord.Embed:
        embed = discord.Embed(
            title="🧠 Trivia Time!",
            description=self.prompt,
            color=discord.Color.blurple()
        )

        # Add the answer options
        option_letters = ['A', 'B', 'C', 'D', 'E', 'F', 'G']
        for i, answer in enumerate(self.answers):
            if i < len(option_letters):  # Prevent index error
                embed.add_field(name=f"{option_letters[i]}.", value=answer, inline=False)

        embed.set_footer(text=f"Difficulty: {self.difficulty} | Category: {self.category}")
        return embed


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





def row_to_question(row) -> Question:
    id, prompt, answers_json, correct_index, difficulty, category, created_by = row
    return Question(
        id=id,
        prompt=prompt,
        answers=json.loads(answers_json),
        correct_index=correct_index,
        difficulty=difficulty,
        category=category,
        created_by=created_by
    )




def register_commands(tree: discord.app_commands.CommandTree):

    @tree.command(name="hello", description="Say hello!")
    async def hello_command(interaction: discord.Interaction):
        await interaction.response.send_message("Hello!")

    # Slash command: /register
    @tree.command(name="register", description="Register yourself in the trivia leaderboard")
    async def register(interaction: discord.Interaction):
        user_id = interaction.user.id
        guild_id = interaction.guild.id

        try:
            conn = mysql.connector.connect(**DB_CONFIG)
            cursor = conn.cursor()

            cursor.execute("""
                INSERT INTO user_data (guild_id, user_id)
                VALUES (%s, %s)
                ON DUPLICATE KEY UPDATE user_id = user_id
            """, (guild_id, user_id))
            conn.commit()

            await interaction.response.send_message(f"{interaction.user.mention}, you are now registered!", ephemeral=True)

        except mysql.connector.Error as err:
            logging.error(f"MySQL error: {err}")
            await interaction.response.send_message("❌ Error registering. Try again later.", ephemeral=True)

        finally:
            if cursor:
                cursor.close()
            if conn:
                conn.close()

    @tree.command(name="askme", description="Get asked a trivia question!")
    async def askme(interaction: discord.Interaction):


        try:
            conn = mysql.connector.connect(**DB_CONFIG)
            cursor = conn.cursor()
            cursor.execute("SELECT id, prompt, answers, correct_index, difficulty, category, created_by FROM trivia_questions ORDER BY RAND() LIMIT 1")
            result = cursor.fetchone()

        except mysql.connector.Error as err:
            logging.error(f"MySQL error: {err}")
            await interaction.response.send_message("❌ Error finding question. Try again later.", ephemeral=True)

        finally:
            if cursor:
                cursor.close()
            if conn:
                conn.close()
        
        
        question = row_to_question(result)
        embed = question.to_embed()


        view = AnswerButtons(question)


        await interaction.response.send_message(embed=embed, view=view)
