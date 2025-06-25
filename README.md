1. download files from github

	git clone https://github.com/Carterz5/TriviaBot.git

2. install python venv

	a. install pyenv
		follow instructions here https://github.com/pyenv/pyenv
		pyenv install 3.12.3
		pyenv local 3.12.3

	python3 -m venv venv
	source venv/bin/activate

3. install python3 packages

    use requirements.txt or pip install

        discord.py
        mysql-connector-python
        python-dotenv
        requests


4. setup mysql database

	sudo apt update
	sudo apt install mysql-server
	sudo systemctl start mysql
	sudo systemctl enable mysql
	sudo mysql_secure_installation
	
	sudo mysql

	CREATE DATABASE Discord_Bot;
	CREATE USER 'your_username'@'localhost' IDENTIFIED BY 'your_password';
	GRANT PROCESS ON *.* TO 'your_username'@'localhost';
	GRANT ALL PRIVILEGES ON Discord_Bot.* TO 'your_username'@'localhost';
	FLUSH PRIVILEGES;
	EXIT;

	mysql -u your_username -p Discord_Bot < schema.sql


5. create .env

    example
    ``` DISCORD_TOKEN = your_token_here

        DB_HOST = "localhost"
        DB_USER = "your_username"
        DB_PASSWORD = "your_password"
        DB_DATABASE = "Discord_Bot"
	```

6. Add questions to database

	python3 question_grabber.py


7. Run the bot

	python3 main.py