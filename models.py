import discord
import json




from dataclasses import dataclass
from typing import List



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

        embed.set_footer(text=f"Difficulty: {self.difficulty} | Category: {self.category} | Author: {self.created_by}")
        return embed
    


@dataclass
class User:
    user_id: int
    guild_id: int
    points: int
    streak: int
    answers_total: int
    answers_correct: int
    gambling_winnings: int
    gambling_losses: int

    def to_embed(self) -> discord.Embed:
        embed = discord.Embed(
            title="Your Stats",
            color=discord.Color.blurple()
        )        
        embed.add_field(name="Total Points:", value=f"{self.points:,}", inline=False)
        embed.add_field(name="Streak:", value=f"{self.streak:,}", inline=False)
        embed.add_field(name="Total Questions Answered:", value=f"{self.answers_total:,}", inline=False)
        embed.add_field(name="Total Correct Answers:", value=f"{self.answers_correct:,}", inline=False)
        embed.add_field(name="Total Gambling Winnings:", value=f"{self.gambling_winnings:,}", inline=False)
        embed.add_field(name="Total Gambling Losses:", value=f"{self.gambling_losses:,}", inline=False)

        return embed
    
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

def row_to_user(row) -> User:
    guild_id, user_id, points, streak, answers_total, answers_correct, gambling_winnings, gambling_losses = row
    return User(
        user_id=user_id,
        guild_id=guild_id,
        points=points,
        streak=streak,
        answers_total=answers_total,
        answers_correct=answers_correct,
        gambling_winnings=gambling_winnings,
        gambling_losses=gambling_losses
    )