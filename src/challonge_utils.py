import re


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