import discord
import logging
import asyncio


from core import db
from core import models

from core.models import Question








class AnswerButtons(discord.ui.View):
    def __init__(self, question: Question, starter, timeout=30, timeoutflag=False, buttonflag=False):
        super().__init__(timeout=timeout)
        self.question = question
        self.response = None
        self.timeoutflag = timeoutflag
        self.buttonflag = buttonflag
        self.starter = starter

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
        if interaction.user.id != self.view.starter:
            await interaction.response.send_message("This is a single player game, and you did not start it!", ephemeral=True)
            return
        
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
                content=f"❌ Wrong! Correct answer was **{correct_letter}**, {question.answers[question.correct_index]}",
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

