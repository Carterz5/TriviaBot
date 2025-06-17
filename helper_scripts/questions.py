import requests
import html
import random
import json
from core import db
from core import models

url = "https://opentdb.com/api.php?amount=10"
data = requests.get(url)

if not data:
    print("request failed, exiting")
    exit

json_data = json.loads(data.text)


print(f"number of results: {len(json_data['results'])}")

for question in json_data['results']:
    print(f"working on: {question['question']}\n====================================")
    print(question)
    if len(question['incorrect_answers']) > 3:
        raise ValueError("expected ≤ 3 answers") 
    
    prompt = html.unescape(question['question'])
    difficulty = html.unescape(question['difficulty'])
    category = html.unescape(question['category'])
    correct = html.unescape(question['correct_answer'])
    answers = [html.unescape(a) for a in question['incorrect_answers']]
    answers.append(correct)
    
    random.shuffle(answers)
    correct_index = answers.index(correct)


    input_q = models.Question(               
        id = 0,
        prompt = prompt,
        answers = answers,
        correct_index = correct_index,
        category = category,
        difficulty = difficulty,
        created_by = "Database"
    )

    print("Data gathered:")
    print(f"{input_q.prompt} - {input_q.answers} - {input_q.correct_index}\n\n")
    db.add_question(input_q)