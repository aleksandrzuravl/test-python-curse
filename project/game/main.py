from cards import *
from game import *
from players import *

if __name__ == "__main__":
    # Создание стола с разными настройками
    table = Table(
        human_players=0,
        bot_players=4,
        max_rounds=5,
        bot_strategies=[PlayerStrategy.CONSERVATIVE, PlayerStrategy.AGGRESSIVE],
        initial_chips=100
    )

    # Запуск игры
    table.play_game()