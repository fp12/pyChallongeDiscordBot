import asyncio
import re
from challonge import Account, ChallongeException
from const import *


def author_is_winner(csv_score):
    total_author = 0
    total_opponent = 0
    for s in re.findall(r'\d+-\d+', csv_score):
        split = s.split('-')
        if split[0] > split[1]:
            total_author += 1
        else:
            total_opponent += 1
    return total_author > total_opponent


def reverse_score(csv_score):
    newScore = []
    for s in re.findall(r'\d+-\d+', csv_score):
        split = s.split('-')
        newScore.append('{0}-{1}'.format(split[1], split[0]))
    return ','.join(newScore)


def verify_score_format(csv_score):
	result = re.compile('(\d+-\d+)(,\d+-\d+)*')
	return result.match(csv_score)


async def get_player(account, t_id, name):
    try:
        participants = await account.participants.index(t_id)
    except ChallongeException as e:
        return None, T_OnChallongeException.format(e)
    else:
        for x in participants:
            if x['name'] == name:
                return x['id']
        return None, None


async def get_players(account, t_id, p1_name, p2_name):
    try:
        participants = await account.participants.index(t_id)
    except ChallongeException as e:
        return None, None, T_OnChallongeException.format(e)
    else:
        for x in participants:
            if x['name'] == p1_name:
                p1_id = x['id']
            elif x['name'] == p2_name:
                p2_id = x['id']
            if p1_id and p2_id:
                break
        return p1_id, p2_id, None


async def get_match(t_id, p1_id, p2_id):
    try:
        openMatches = await account.matches.index(t_id, state='open', participant_id=p1_id)
    except ChallongeException as e:
        return None, None, T_OnChallongeException.format(e)
    else:
        for m in openMatches:
            if m['player1-id'] == p1_id and m['player2-id'] == p2_id or m['player2-id'] == p1_id and m['player1-id'] == p2_id:
                is_reversed = m['player1-id'] == p2_id
                return m, is_reversed, None
    return None, None, None


async def update_score(account, t_id, m_id, score, winner_id):
    try:
        await account.matches.update(t_id, m_id, scores_csv=score, winner_id=winner_id)
    except ChallongeException as e:
        return '', T_OnChallongeException.format(e)
    else:
        return '✅ These results have been uploaded to Challonge', None