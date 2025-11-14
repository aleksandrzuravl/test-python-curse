from enum import Enum
from project.game.cards import *


class PlayerStrategy(Enum):
    CONSERVATIVE = 1  # Останавливается на 17+
    MODERATE = 2  # Останавливается на 16+
    AGGRESSIVE = 3  # Останавливается на 15+
    RANDOM = 4  # Случайный выбор


class Player:
    def __init__(self, name, initial_chips=100, strategy=None, is_human=False):
        self.name = name
        self.chips = initial_chips
        self.hand = []
        self.bet = 0
        self.stand = False
        self.strategy = strategy
        self.is_human = is_human

    def place_bet(self, amount):
        """Ставка игрока"""
        if amount <= self.chips:
            self.bet = amount
            self.chips -= amount
            return True
        return False

    def receive_card(self, card):
        """Получение карты"""
        self.hand.append(card)

    def calculate_score(self):
        """Подсчет очков с учетом тузов"""
        score = sum(card.rank.value for card in self.hand)
        aces = sum(1 for card in self.hand if card.rank == ACE)

        # Уменьшаем значение тузов с 11 до 1, если нужно
        while score > 21 and aces > 0:
            score -= 10
            aces -= 1

        return score

    def has_blackjack(self):
        """Проверка на блэкджек (21 очко с двумя картами)"""
        return len(self.hand) == 2 and self.calculate_score() == 21

    def is_busted(self):
        """Проверка на перебор"""
        return self.calculate_score() > 21

    def should_hit(self):
        """Определяет, нужно ли брать карту в зависимости от стратегии"""
        if self.strategy is None:
            return False

        score = self.calculate_score()

        if self.strategy == PlayerStrategy.CONSERVATIVE:
            return score < 17
        elif self.strategy == PlayerStrategy.MODERATE:
            return score < 16
        elif self.strategy == PlayerStrategy.AGGRESSIVE:
            return score < 15
        elif self.strategy == PlayerStrategy.RANDOM:
            import random
            return random.choice([True, False]) and score < 20

        return score < 17

    def make_decision(self):
        """Принимает решение о ходе (для ботов)"""
        if self.is_busted() or self.stand:
            return "stand"

        if self.should_hit():
            return "hit"
        else:
            return "stand"

    def clear_hand(self):
        """Очистка руки"""
        self.hand = []
        self.stand = False
        self.bet = 0

    def win_bet(self):
        """Выигрыш ставки"""
        self.chips += self.bet * 2

    def push(self):
        """Возврат ставки при ничьей"""
        self.chips += self.bet

    def __str__(self):
        hand_str = ", ".join(str(card) for card in self.hand)
        player_type = "Человек" if self.is_human else "Бот"
        strategy_str = f" ({self.strategy.name})" if self.strategy else ""
        return f"{self.name}: {hand_str} ({self.calculate_score()}) | Фишки: {self.chips} [{player_type}{strategy_str}]"

    def __repr__(self):
        return f"Player(name='{self.name}', chips={self.chips}, human={self.is_human})"


class Dealer(Player):
    def __init__(self, strategy=PlayerStrategy.MODERATE):
        super().__init__("Диллер", strategy=strategy)

    def should_hit(self):
        """Определяет, нужно ли диллеру брать карту в зависимости от стратегии"""
        score = self.calculate_score()

        if self.strategy == PlayerStrategy.CONSERVATIVE:
            return score < 17
        elif self.strategy == PlayerStrategy.MODERATE:
            return score < 16
        elif self.strategy == PlayerStrategy.AGGRESSIVE:
            return score < 15

        return score < 17

    def show_hand(self, hide_first_card=False):
        """Показывает руку диллера"""
        if hide_first_card and len(self.hand) > 0:
            hidden_hand = ["XX"] + [str(card) for card in self.hand[1:]]
            return f"{self.name}: {', '.join(hidden_hand)}"
        else:
            return str(self)