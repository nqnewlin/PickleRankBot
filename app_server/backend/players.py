import sqlite3
from app_server.backend import rating as Rating

DATABASE = 'pickle_rank.db'
PLAYER_TABLE = 'players'
MATCHES_TABLE = 'matches'

DEFAULT_RANK = 1500

class Player:


    def __init__(self):
        self.conn = sqlite3.connect(DATABASE)
        self._create_tables()

    def _create_tables(self):
        cursor = self.conn.cursor()

        cursor.execute('''
            CREATE TABLE IF NOT EXISTS players (
                    player_id INTEGER PRIMARY KEY,
                    first_name TEXT,
                    last_name TEXT,
                    discord_id INTEGER,
                    rating INTEGER
            )
            ''')


        cursor.execute('''
            CREATE TABLE IF NOT EXISTS matches(
                match_id INTEGER PRIMARY KEY,
                team_1_player_1_id INTEGER,
                team_1_player_2_id INTEGER,
                team_2_player_1_id INTEGER,
                team_2_player_2_id INTEGER,
                team_1_score INTEGER,
                team_2_score INTEGER,
                game_ts DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        self.conn.commit()
        cursor.close()


    def get_all_current_ranking(self) -> list[dict]:
        players = []
        conn = sqlite3.connect(DATABASE)
        cursor = conn.cursor()


        cursor.execute("SELECT * FROM players")
        player_rows = cursor.fetchall()

        for row in player_rows:
            player_history = self._get_player_match_history(row[0])
            player_history['rating'] = row[4]
            name = row[1] + ' ' + row[2][0].upper() + '.'
            player_history['name'] = name
            players.append(player_history)


        return players

    def _get_player_match_history(self, player_id: int) -> dict[str, int]:

        cursor = self.conn.cursor()

        cursor.execute("SELECT * FROM matches where team_1_player_1_id = ? or team_1_player_2_id = ?",
                       (player_id, player_id))
        # cursor.execute("SELECT * FROM matches where player_1_id = ?", (player_id,))
        match_rows_1 = cursor.fetchall()

        cursor.execute(
            "SELECT * FROM matches where team_2_player_1_id = ? or team_2_player_2_id = ?",
            (player_id, player_id))
        # cursor.execute("SELECT * FROM matches where player_2_id = ?", (player_id,))
        match_rows_2 = cursor.fetchall()

        # games = len(match_rows_1)
        games = len(match_rows_1) + len(match_rows_2)
        wins = 0
        losses = 0

        for match in match_rows_1:
            wins, losses = update_wins_losses(match[5], match[6], wins, losses)

        for match in match_rows_2:
            wins, losses = update_wins_losses(match[6], match[5], wins, losses)

        return { 'wins': wins, 'losses': losses, 'games': games, 'percent' : wins/games * 100 if games > 0 else 0}


    def create_new_player(self, first_name: str, last_name: str, discord_id: int = None) -> bool:
        try:
            cursor = self.conn.cursor()
            cursor.execute("INSERT INTO players (first_name, last_name, rating, discord_id) VALUES (?, ?, ?, ?)",
                           (first_name, last_name, DEFAULT_RANK, discord_id))
            self.conn.commit()
            cursor.close()
        except Exception as e:
            print(f'Error occurred: {e}')
            return False

        return True

    def update_discord_id(self, player_id:int, discord_id: int):
        cursor = self.conn.cursor()
        cursor.execute("UPDATE players SET discord_id = ? where player_id = ?", (discord_id, player_id))
        self.conn.commit()
        cursor.close()
    def add_match(self, team_1: list[int], team_2: list[int], team_1_score:int, team_2_score:int):
        cursor = self.conn.cursor()
        if len(team_1) == 1 and len(team_2) == 1:
            cursor.execute(
                "INSERT INTO matches (team_1_player_1_id, team_2_player_1_id, team_1_score, team_2_score) VALUES (?, ?, ?, ?)",
                (team_1[0], team_2[0], team_1_score, team_2_score))
        elif len(team_1) == 2 and len(team_2) == 2:
            cursor.execute(
                "INSERT INTO matches (team_1_player_1_id, team_1_player_2_id, team_2_player_1_id, team_2_player_2_id, team_1_score, team_2_score) VALUES (?, ?, ?, ?, ?, ?)",
                (team_1[0], team_1[1], team_2[0], team_2[1], team_1_score, team_2_score))
        else:
            raise Exception("Team 1 and Team 2 not same size")
        self.conn.commit()

        self.__update_player_ratings(team_1, team_2, team_1_score, team_2_score)

        cursor.close()
        return True

    def __update_player_ratings(self, team_1: list[int], team_2: list[int], team_1_score: int, team_2_score: int):
        team_1_player_1 = self.__get_player_stats(team_1[0])
        team_1_player_2 = self.__get_player_stats(team_1[1]) if len(team_1) > 1  else (None, None)
        team_2_player_1 = self.__get_player_stats(team_2[0])
        team_2_player_2 = self.__get_player_stats(team_2[1]) if len(team_2) > 1 else (None, None)

        team_1_rating = Rating.calculate_team_rating(team_1_player_1[0], team_1_player_2[0])
        team_2_rating = Rating.calculate_team_rating(team_2_player_1[0], team_2_player_2[0])

        team_1_score_calc, team_2_score_calc = Rating.calculate_score(team_1_score, team_2_score)

        team_1_player_1_update = Rating.calculate_player_ranking_update(team_1_rating, team_2_rating, team_1_score_calc, team_1_player_1[1])
        self.__update_rating(team_1[0], int(team_1_player_1[0] + team_1_player_1_update))
        if len(team_1) > 1:
            team_1_player_2_update = Rating.calculate_player_ranking_update(team_1_rating, team_2_rating, team_1_score_calc, team_1_player_2[1])
            self.__update_rating(team_1[1], int(team_1_player_2[0] + team_1_player_2_update))
        team_2_player_1_update = Rating.calculate_player_ranking_update(team_2_rating, team_1_rating, team_2_score_calc, team_2_player_1[1])
        self.__update_rating(team_2[0], int(team_2_player_1[0] + team_2_player_1_update))
        if len(team_2) > 1:
            team_2_player_2_update = Rating.calculate_player_ranking_update(team_2_rating, team_1_rating, team_2_score_calc, team_2_player_2[1])
            self.__update_rating(team_2[1], int(team_2_player_2[0] + team_2_player_2_update))



    def __update_rating(self, player_id: int, rating: int):
        cursor = self.conn.cursor()
        cursor.execute("UPDATE players set rating = ? where player_id = ?", (rating, player_id))
        self.conn.commit()

    def __get_player_stats(self, player_id:int) -> tuple[int, int]:
        cursor = self.conn.cursor()
        cursor.execute("SELECT rating from players where player_id = ?", (player_id,))
        rating = cursor.fetchone()[0]
        cursor.execute("SELECT match_id FROM matches where team_1_player_1_id = ? or team_1_player_2_id = ? or team_2_player_1_id = ? or team_2_player_2_id = ?",
                       (player_id, player_id, player_id, player_id))
        games_played = len(cursor.fetchall())
        return rating, games_played







    def retrieve_player_list(self) -> list:
        cursor = self.conn.cursor()
        cursor.execute("SELECT player_id, first_name, last_name from players")
        player_rows = cursor.fetchall()
        players = [
            {'player_id': p[0], 'first_name':p[1], 'last_name':p[2]} for p in player_rows
        ]
        return players





def update_wins_losses(player_score, opp_score, wins, losses) -> tuple[int, int]:
    if player_score > opp_score:
        wins += 1
    else:
        losses += 1
    return wins, losses


if __name__ == "__main__":
    player = Player()
    # player.add_match(1, 2, 13, 11)
    # player.add_match(1, 2, 11, 1)
    # player.create_new_player('Nicholas', 'Newlin')
    # player.create_new_player('Anallely', 'Newlin')
    # player.get_all_current_ranking()
    player.retrieve_player_list()


