import discord



from core import db
from core.models import Question






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


