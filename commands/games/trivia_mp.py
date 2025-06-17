import discord
import logging
import asyncio
import time



from core import db
from core import models

from core.models import Question










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