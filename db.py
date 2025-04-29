DB_CONFIG = {
    'host': 'localhost',
    'user': 'Trivia_Bot',
    'password': 'Trivia123',
    'database': 'Discord_Bot'
}

# CREATE TABLE trivia_stats (
#     guild_id BIGINT UNSIGNED NOT NULL,
#     user_id BIGINT UNSIGNED NOT NULL,
#     points BIGINT UNSIGNED DEFAULT 0,
#     streak INT DEFAULT 0,
#     answers_total INT DEFAULT 0,
#     answers_correct INT DEFAULT 0,
#     gambling_winnings BIGINT UNSIGNED DEFAULT 0,
#     gambling_losses BIGINT UNSIGNED DEFAULT 0,
#     PRIMARY KEY (guild_id, user_id)
# );