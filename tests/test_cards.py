import pytest
from project.game.cards import *


class TestCard:
    def test_card_creation_and_string(self):
        card = Card(Suit.HEARTS, ACE)
        assert card.suit == Suit.HEARTS
        assert card.rank == ACE
        assert str(card) == "A♥"


class TestDeck:
    def test_deck_has_52_cards(self):
        deck = Deck()
        assert len(deck) == 52

    def test_deck_deal_reduces_count(self):
        deck = Deck()
        card = deck.deal()
        assert isinstance(card, Card)
        assert len(deck) == 51

    def test_deck_reset_after_empty(self):
        deck = Deck()
        for _ in range(52):
            deck.deal()
        assert len(deck) == 0

        card = deck.deal()
        assert isinstance(card, Card)
        assert len(deck) == 51