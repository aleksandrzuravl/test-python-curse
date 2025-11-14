import pytest
from project.game.cards import Card, Suit, ACE, KING, TEN, SIX
from project.game.players import Player, Dealer, PlayerStrategy
from project.game.cards import Card, Suit, ACE, KING, TEN


class TestPlayer:
    def test_player_initial_state(self):
        player = Player("Test", 100)
        assert player.name == "Test"
        assert player.chips == 100
        assert player.hand == []
        assert player.bet == 0

    def test_player_bet_success(self):
        player = Player("Test", 100)
        assert player.place_bet(50) == True
        assert player.chips == 50
        assert player.bet == 50

    def test_player_bet_insufficient_funds(self):
        player = Player("Test", 100)
        assert player.place_bet(150) == False
        assert player.chips == 100

    def test_player_score_calculation(self):
        player = Player("Test", 100)
        player.receive_card(Card(Suit.HEARTS, TEN))
        player.receive_card(Card(Suit.DIAMONDS, TEN))
        assert player.calculate_score() == 20

    def test_player_blackjack_detection(self):
        player = Player("Test", 100)
        player.receive_card(Card(Suit.HEARTS, ACE))
        player.receive_card(Card(Suit.DIAMONDS, KING))
        assert player.has_blackjack() == True
        assert player.is_busted() == False

    def test_player_bust_detection(self):
        player = Player("Test", 100)
        player.receive_card(Card(Suit.HEARTS, TEN))
        player.receive_card(Card(Suit.DIAMONDS, TEN))
        player.receive_card(Card(Suit.CLUBS, TEN))
        assert player.is_busted() == True


class TestDealer:
    def test_dealer_hit_decisions(self):
        dealer = Dealer(PlayerStrategy.CONSERVATIVE)
        dealer.receive_card(Card(Suit.HEARTS, TEN))
        dealer.receive_card(Card(Suit.DIAMONDS, SIX))
        assert dealer.should_hit() == True  # 16 < 17

        dealer.receive_card(Card(Suit.CLUBS, ACE))
        assert dealer.should_hit() == False  # 17 >= 17