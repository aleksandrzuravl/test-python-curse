import random
from enum import Enum


class Suit(Enum):
    HEARTS = "♥"
    DIAMONDS = "♦"
    CLUBS = "♣"
    SPADES = "♠"


class Rank:
    def __init__(self, value, symbol):
        self.value = value
        self.symbol = symbol

    def __str__(self):
        return self.symbol

    def __repr__(self):
        return self.symbol


# Создаем ранги карт
TWO = Rank(2, "2")
THREE = Rank(3, "3")
FOUR = Rank(4, "4")
FIVE = Rank(5, "5")
SIX = Rank(6, "6")
SEVEN = Rank(7, "7")
EIGHT = Rank(8, "8")
NINE = Rank(9, "9")
TEN = Rank(10, "10")
JACK = Rank(10, "J")
QUEEN = Rank(10, "Q")
KING = Rank(10, "K")
ACE = Rank(11, "A")

# Список всех рангов для удобства
RANKS = [TWO, THREE, FOUR, FIVE, SIX, SEVEN, EIGHT, NINE, TEN, JACK, QUEEN, KING, ACE]


class Card:
    def __init__(self, suit, rank):
        self.suit = suit
        self.rank = rank

    def __str__(self):
        return f"{self.rank.symbol}{self.suit.value}"

    def __repr__(self):
        return self.__str__()

    def __eq__(self, other):
        if not isinstance(other, Card):
            return False
        return self.suit == other.suit and self.rank == other.rank


class Deck:
    def __init__(self):
        self.cards = []
        self.reset()

    def reset(self):
        """Создает новую колоду и перемешивает ее"""
        self.cards = [Card(suit, rank) for suit in Suit for rank in RANKS]
        self.shuffle()

    def shuffle(self):
        """Перемешивает колоду"""
        random.shuffle(self.cards)

    def deal(self):
        """Раздает одну карту из колоды"""
        if not self.cards:
            self.reset()
        return self.cards.pop()

    def __len__(self):
        return len(self.cards)
