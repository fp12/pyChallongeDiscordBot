from enum import Enum


class Events(Enum):
    on_join = 0
    on_checkin_start = 1
    on_update_score = 2
    on_tournament_start = 3
    on_tournament_finalize = 4
    on_tournament_destroy = 5
