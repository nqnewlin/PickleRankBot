from enum import Enum
from typing import Literal
import math

LOWER_PLAYER_RATIO = .7 # currently assuming lower rated player has greater ratio/impact on team rating

def calculate_score(team_1_score: int, team_2_score: int) -> tuple[float, float]:
    """
    Calculates adjusted scores for two teams based on their initial scores,
    applying an "extra point" penalty/bonus for games going beyond 11 points.

    Args:
        team_1_score: The initial score of team 1.
        team_2_score: The initial score of team 2.

    Returns:
        A tuple containing the adjusted scores for team 1 and team 2.
    """

    winner_score = max(team_1_score, team_2_score)
    loser_score = min(team_1_score, team_2_score)
    score_difference = winner_score - loser_score

    # Rule 1: Winner must score at least 11
    if winner_score < 11:
        raise ValueError("The winning team must score at least 11 points.")

    if winner_score > 11 and score_difference > 2:
        raise ValueError("The winning team and losing team must be within 2 points for any value greater than 11")

    # Rule 2: Winner must win by at least 2 points
    if score_difference < 2:
        raise ValueError("The winning team must win by at least 2 points.")

    extra_round = max(0, team_1_score - 11, team_2_score - 11)

    # 1 - e^(-kx) extra_point approaches 1 for each extra round played
    # Using math.exp for e^x
    extra_point = 1 - math.exp(-extra_round)

    # Determine the winner and calculate initial adjusted scores
    if team_1_score > team_2_score:
        margin = team_1_score - team_2_score
        adj_team_1_score = 11 + margin
        adj_team_2_score = 11 - margin

        # Apply extra_point adjustment
        final_team_1_score = (adj_team_1_score - extra_point)/ 22
        final_team_2_score = (adj_team_2_score + extra_point)/ 22
    else:
        margin = team_2_score - team_1_score
        adj_team_1_score = 11 - margin
        adj_team_2_score = 11 + margin

        # Apply extra_point adjustment
        final_team_1_score = (adj_team_1_score + extra_point)/ 22
        final_team_2_score = (adj_team_2_score - extra_point)/ 22

    return final_team_1_score, final_team_2_score








def calculate_expected_score(rating_a: int, rating_b: int) -> float:
    """
    Formula: Ea = 1 / (1 + 10^((Rb - Ra) / 400))
    Ea - expected score
    Rb - player b rating
    Ra - player a rating
    """
    return 1 / (1 + 10 ** ((rating_b - rating_a) / 400))

def calculate_k(games: int, rating: int) -> int:
    if games < 10:
        return 150
    elif games < 20 :
        return 75
    elif 1700 > rating > 1300:
        return 32
    else:
        return 16



def update_player_ranking(rank_player: int, rank_opponent: int, outcome_score: float, games: int) -> float:
    """
    :param rank_player: ELO rating of player
    :param rank_opponent: ELO rating of opponent
    :param outcome_score: the calculated outcome score will be value from 0.0 - 1.0
    :param games: number of games player 1 has completed, used to determine k factor
    :return: updated rating for player
    """
    expected = calculate_expected_score(rank_player, rank_opponent)
    k = calculate_k(games, rank_player)
    update_qty = k * (outcome_score - expected)
    return rank_player + update_qty



def update_player_rankings(rank_1: int, rank_2: int, player_1_outcome: float) -> tuple[float, float]:
    """
    Formula: R'a = Ra + K * (Sa - Ea)
    :param rank_1:
    :param rank_2:
    :param player_1_outcome:
    :return:
    """

    expected_1 = calculate_expected_score(rank_1, rank_2)
    K = 32
    update_qty = K * (player_1_outcome - expected_1)
    print(update_qty)


    return rank_1 + update_qty, rank_2 - update_qty

def calculate_team_rating(player_1_rating: float, player_2_rating: float) -> float:
    if player_1_rating < player_2_rating:
        return (player_1_rating * LOWER_PLAYER_RATIO) + (player_2_rating * (1.0 - LOWER_PLAYER_RATIO))
    else:
        return (player_2_rating * LOWER_PLAYER_RATIO) + (player_1_rating * (1.0 - LOWER_PLAYER_RATIO))




if __name__ == '__main__':


    print(calculate_team_rating(1500, 1100))
    team_1, team_2 = calculate_score(1, 11)
    print(f'Team 1 score: {team_1}')
    print(f'Team 2 score: {team_2}')
    #
    # player_1_updated, player_2_updated = update_player_rankings(player_1, player_2, team_1)
    player_1_updated = update_player_ranking(1500, 1500, team_1, 1)
    player_2_updated = update_player_ranking(1500, 1500, team_2, 1)
    print(f'Player 1 updated: {player_1_updated}')
    print(f'Player 2 updated: {player_2_updated}')

    # for i in range(50):
    #     team_1, team_2 = calculate_score(0, 11)
    #     temp = player_1
    #     player_1 = update_player_ranking(player_1, player_2, team_1, i + 1)
    #     player_2 = update_player_ranking(player_2, temp, team_2, i + 1)
    #
    # print(f'Player 1 final: {player_1}')
    # print(f'Player 2 final: {player_2}')




