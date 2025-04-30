import discord
import mysql.connector
import logging
import asyncio
import random

from discord import app_commands

import db
import models

from models import Question
from models import User


class QuestionSetupView(discord.ui.View):
    def __init__(self):
        super().__init__()
        self.difficulty = None
        self.category = None

    @discord.ui.select(
        placeholder="Select difficulty...",
        options=[
            discord.SelectOption(label="easy"),
            discord.SelectOption(label="medium"),
            discord.SelectOption(label="hard")
        ]
    )
    async def select_difficulty(self, interaction: discord.Interaction, select: discord.ui.Select):
        self.difficulty = select.values[0]
        await interaction.response.send_message(f"Difficulty set to: {self.difficulty}", ephemeral=True)

    @discord.ui.select(
        placeholder="Select category...",
        options=[
            discord.SelectOption(label="General Knowledge"),
            discord.SelectOption(label="Entertainment: Books"),
            discord.SelectOption(label="Entertainment: Film"),
            discord.SelectOption(label="Entertainment: Music"),
            discord.SelectOption(label="Entertainment: Musicals & Theatres"),
            discord.SelectOption(label="Entertainment: Television"),
            discord.SelectOption(label="Entertainment: Video Games"),
            discord.SelectOption(label="Entertainment: Board Games"),
            discord.SelectOption(label="Entertainment: Comics"),
            discord.SelectOption(label="Entertainment: Japanese Anime & Manga"),
            discord.SelectOption(label="Entertainment: Cartoon & Animations"),
            discord.SelectOption(label="Science & Nature"),
            discord.SelectOption(label="Science: Computers"),
            discord.SelectOption(label="Science: Mathematics"),
            discord.SelectOption(label="Science: Gadgets"),
            discord.SelectOption(label="Mythology"),
            discord.SelectOption(label="Sports"),
            discord.SelectOption(label="Geography"),
            discord.SelectOption(label="History"),
            discord.SelectOption(label="Politics"),
            discord.SelectOption(label="Art"),
            discord.SelectOption(label="Celebrities"),
            discord.SelectOption(label="Animals"),
            discord.SelectOption(label="Vehicles")
        ]
    )
    async def select_category(self, interaction: discord.Interaction, select: discord.ui.Select):
        self.category = select.values[0]
        await interaction.response.send_message(f"Category set to: {self.category}", ephemeral=True)

    @discord.ui.button(label="Next", style=discord.ButtonStyle.primary)
    async def submit_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        if self.difficulty and self.category:
            await interaction.response.send_modal(SubmitQuestionModal(self.difficulty, self.category))
        else:
            await interaction.response.send_message("Please select both a difficulty and a category.", ephemeral=True)






class SubmitQuestionModal(discord.ui.Modal, title="Submit Your Question"):
    def __init__(self, difficulty: str, category: str):
        super().__init__()
        self.difficulty = difficulty
        self.category = category

        self.prompt_input = discord.ui.TextInput(label="Question Prompt", style=discord.TextStyle.paragraph, required=True)
        self.answers_input = discord.ui.TextInput(
            label="Answers (one per line for A-D)",
            style=discord.TextStyle.paragraph,
            placeholder="Answer A\nAnswer B\nAnswer C\nAnswer D",
            required=True
        )
        self.correct_letter_input = discord.ui.TextInput(label="Correct Answer Letter (A-D)", required=True, max_length=1)

        self.add_item(self.prompt_input)
        self.add_item(self.answers_input)
        self.add_item(self.correct_letter_input)

    async def on_submit(self, interaction: discord.Interaction):
        prompt = self.prompt_input.value.strip()
        answers_raw = self.answers_input.value.strip()
        correct_letter = self.correct_letter_input.value.strip().upper()

        # Validate prompt
        if len(prompt) < 10:
            await interaction.response.send_message("❌ Prompt is too short. Must be at least 10 characters.", ephemeral=True)
            return

        # Validate answers
        answers = [a.strip() for a in answers_raw.splitlines() if a.strip()]
        if len(answers) != 4:
            await interaction.response.send_message("❌ You must enter exactly 4 non-empty answers (A–D).", ephemeral=True)
            return

        # Validate correct answer letter
        if correct_letter not in ['A', 'B', 'C', 'D']:
            await interaction.response.send_message("❌ Correct answer must be one of: A, B, C, or D.", ephemeral=True)
            return

        correct_index = ord(correct_letter) - ord('A')
        
        
        
        
        
        
        question = Question(0, prompt, answers, correct_index, self.difficulty, self.category, interaction.user.name)
        db.add_question(question)

        await interaction.response.send_message("✅ Your question was submitted!", ephemeral=True)




class AnswerButtons(discord.ui.View):
    def __init__(self, question: Question, timeout=30, timeoutflag=False, buttonflag=False):
        super().__init__(timeout=timeout)
        self.question = question
        self.response = None
        self.timeoutflag = timeoutflag
        self.buttonflag = buttonflag

        # Create buttons based on the number of answers
        option_letters = ['A', 'B', 'C', 'D', 'E', 'F', 'G']
        for i, _ in enumerate(self.question.answers):
            if i >= len(option_letters):
                break
            label = option_letters[i]
            self.add_item(AnswerButton(label=label, index=i))
    
    async def on_timeout(self):
        logging.info("Trivia timed out!")
        self.timeoutflag=True
        for item in self.children:
            if isinstance(item, discord.ui.Button):
                item.disabled = True

        if self.message:
            try:
                current_message = await self.message.channel.fetch_message(self.message.id)
                if current_message.embeds == self.message.embeds:  # crude check
                    await self.message.edit(content="Trivai Timed Out!", view=self)
            except discord.NotFound:
                pass  

class AnswerButton(discord.ui.Button):
    def __init__(self, label: str, index: int):
        super().__init__(style=discord.ButtonStyle.primary, label=label)
        self.index = index

    async def callback(self, interaction: discord.Interaction):
        question: Question = self.view.question
        is_correct = (self.index == question.correct_index)
        user = models.row_to_user(db.fetch_user(interaction.user.id, interaction.guild.id))

        # Disable all buttons after answer
        for item in self.view.children:
            item.disabled = True

        if is_correct:
            await interaction.response.edit_message(content="✅ Correct!", view=self.view)
            user.streak += 1
            user.answers_total += 1
            user.answers_correct += 1
            match question.difficulty:
                case "easy":
                    user.points += 1
                case "medium":
                    user.points += 2
                case "hard":
                    user.points += 3
            
                
        else:
            correct_letter = ['A', 'B', 'C', 'D', 'E', 'F', 'G'][question.correct_index]
            await interaction.response.edit_message(
                content=f"❌ Wrong! Correct answer was **{correct_letter}**.",
                view=self.view
            )
            user.answers_total += 1
            user.streak = 0

        db.update_user(user)
        self.view.buttonflag = True
        await asyncio.sleep(2)
        try:
            row = db.fetch_random_question()
            next_question = models.row_to_question(row)
            new_embed = next_question.to_embed()
            new_view = AnswerButtons(next_question)

            message = await interaction.edit_original_response(content=None, embed=new_embed, view=new_view)
            new_view.message = message

        except Exception as e:
            await interaction.followup.send("Error loading next question.", ephemeral=True)





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
        view.message = await interaction.original_response()

    @tree.command(name="coinflip", description="Bet your points on a coin flip!")
    @app_commands.describe(bet= "How many points you want to bet", guess="Your guess: heads or tails")
    @app_commands.choices(guess=[app_commands.Choice(name="Heads", value="heads"), app_commands.Choice(name="Tails", value="tails")])

    async def coinflip(interaction: discord.Interaction, bet: int, guess: app_commands.Choice[str]):
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


    @tree.command(name="submit_question", description="Submit your own trivia question!")
    async def submit_question(interaction: discord.Interaction):
        view = QuestionSetupView()
        await interaction.response.send_message("Choose difficulty and category:", view=view, ephemeral=True)