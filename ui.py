import discord
import logging
import asyncio
import mysql.connector
import time
import random


import db
import models

from models import Question
from models import User





class QuestionSetupView(discord.ui.View):
    def __init__(self):
        super().__init__()
        self.difficulty = None
        self.category = None
        self.prompt = None
        self.answer1 = None
        self.answer2 = None
        self.answer3 = None
        self.answer4 = None
        self.correct_answer = None

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
        await interaction.response.defer(ephemeral=True, thinking=False)
        # await interaction.response.send_message(f"Difficulty set to: {self.difficulty}", ephemeral=True)

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
        await interaction.response.defer(ephemeral=True, thinking=False)
        # await interaction.response.send_message(f"Category set to: {self.category}", ephemeral=True)




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


#single player

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

    def repopulate_buttons(self):
        self.clear_items()
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

        await self.message.edit(content="Trivia Timed Out!", view=self)


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


            self.embed = next_question.to_embed()
            self.view.question = next_question
            self.view.repopulate_buttons()

            message = await interaction.edit_original_response(content=None, embed=self.embed, view=self.view)
            self.view.message = message

        except Exception as e:
            await interaction.followup.send("Error loading next question.", ephemeral=True)
            logging.error(f"Error loading next question error: {e}")



#multiplayer

class AnswerButtonsMP(discord.ui.View):
    def __init__(self, question: Question, timeout=30, timeoutflag=False):
        super().__init__(timeout=timeout)
        self.question = question
        self.response = None
        self.timeoutflag = timeoutflag
        self.answered_users = dict()

        # Create buttons based on the number of answers
        option_letters = ['A', 'B', 'C', 'D', 'E', 'F', 'G']
        for i, _ in enumerate(self.question.answers):
            if i >= len(option_letters):
                break
            label = option_letters[i]
            self.add_item(AnswerButtonMP(label=label, index=i))

    def repopulate_buttons(self):
        self.clear_items()
        option_letters = ['A', 'B', 'C', 'D', 'E', 'F', 'G']
        for i, _ in enumerate(self.question.answers):
            if i >= len(option_letters):
                break
            label = option_letters[i]
            self.add_item(AnswerButtonMP(label=label, index=i))
    
    async def on_timeout(self):
        logging.info("Trivia timed out!")
        self.timeoutflag=True
        for item in self.children:
            if isinstance(item, discord.ui.Button):
                item.disabled = True
        

class AnswerButtonMP(discord.ui.Button):
    def __init__(self, label: str, index: int):
        super().__init__(style=discord.ButtonStyle.primary, label=label)
        self.index = index

    async def callback(self, interaction: discord.Interaction):
        if interaction.user.name in self.view.answered_users:
            await interaction.response.send_message("You already answered!", ephemeral=True)
            return
        self.view.answered_users[interaction.user.name] = {"answer": self.index, "timestamp": time.time()}
        
        question=self.view.question
        is_correct = (self.index == question.correct_index)
        user = models.row_to_user(db.fetch_user(interaction.user.id, interaction.guild.id))

        if is_correct:

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
            user.answers_total += 1
            user.streak = 0
        await interaction.response.defer(ephemeral=True, thinking=False)
        db.update_user(user)

#baker's dozen

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



# features to add:
# command user determines size of bet for everyone.
# 
# <@{interaction.user.id}>
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

    



async def mp_game_loop(interaction: discord.Interaction, rounds: int):
    scoreboard = dict()

    for i in range(rounds):
        # Fetch a new question
        row = db.fetch_random_question()
        question = models.row_to_question(row)
        embed = question.to_embed()
        view = AnswerButtonsMP(question)
        difficulty_to_index = {'easy': 1, 'medium': 2, 'hard': 3, }
        points = difficulty_to_index.get(view.question.difficulty)
        question_start = int(time.time())

        if i == 0:
            await interaction.response.send_message(content=f"Answer <t:{question_start + 15}:R>.", embed=embed, view=view)
            message = await interaction.original_response()
        else:
            message = await message.edit(content=f"Answer <t:{question_start + 15}:R>.", embed=embed, view=view)
        
        view.message = message

        await asyncio.sleep(15)

        # Disable buttons
        for item in view.children:
            if isinstance(item, discord.ui.Button):
                item.disabled = True

        if not view.answered_users:
            await view.message.edit(content="Nobody answered! Trivia session has expired.", view=view)
            return

        correct_letter = ['A', 'B', 'C', 'D', 'E', 'F', 'G'][question.correct_index]
        result_embed = discord.Embed(
            title="Results",
            description=f"⏰ Time's up! Correct answer was **{correct_letter}**, {view.question.answers[view.question.correct_index]}.",
            color=discord.Color.blurple()
        )

        for user_name, data in view.answered_users.items():
            is_correct = data['answer'] == question.correct_index
            speed = time_difference_seconds(question_start, data['timestamp'])

            if is_correct:
                scoreboard[user_name] = scoreboard.get(user_name, 0) + 1
                result_embed.add_field(
                    name=f"✅{user_name} | +{points} points!",
                    value=f"- Answered in {speed:.2f} seconds!",
                    inline=False
                )
            else:
                scoreboard[user_name] = scoreboard.get(user_name, 0)
                result_embed.add_field(
                    name=f"❌{user_name} ",
                    value=f"- Got it wrong in {speed:.2f} seconds!",
                    inline=False
                )
        result_embed.set_footer(text=f"Difficulty: {view.question.difficulty} | Category: {view.question.category} | Author: {view.question.created_by}")


        question_start = int(time.time())
        await view.message.edit(content=f"Next Question <t:{question_start + 10}:R>.", embed=result_embed, view=view)
        await asyncio.sleep(10)
    
    await view.message.edit(content=None, embed=result_embed, view=view)

    final_score_embed = discord.Embed(
        title="🏁 Trivia Game Over!",
        description="Here are the final scores:",
        color=discord.Color.gold()
    )

    # Sort by highest score
    sorted_scores = sorted(scoreboard.items(), key=lambda item: item[1], reverse=True)

    for user_name, score in sorted_scores:
        final_score_embed.add_field(name=f"{user_name}", value=f"- {score} correct", inline=False)

    await view.message.channel.send(embed=final_score_embed)

    

def time_difference_seconds(t1, t2):
    return abs(t2 - t1)