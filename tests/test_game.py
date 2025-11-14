import pytest
from unittest.mock import patch, MagicMock
from project.game.game import Table
from project.game.players import PlayerStrategy
from project.game.cards import Card, Suit, ACE, KING, TEN


class TestTable:
    def test_table_initialization(self):
        table = Table(human_players=1, bot_players=2)
        assert len(table.players) == 3
        assert table.human_players_count == 1
        assert table.bot_players_count == 2

    def test_deal_initial_cards(self):
        table = Table(human_players=1, bot_players=1)
        table.deal_initial_cards()

        assert len(table.dealer.hand) == 2
        for player in table.players:
            assert len(player.hand) == 2

    def test_determine_winners_dealer_bust(self):
        table = Table(human_players=1, bot_players=0)
        player = table.players[0]
        dealer = table.dealer

        # Мокаем результаты
        player.calculate_score = MagicMock(return_value=20)
        player.is_busted = MagicMock(return_value=False)
        dealer.calculate_score = MagicMock(return_value=22)
        dealer.is_busted = MagicMock(return_value=True)

        player.place_bet(10)
        winners = table.determine_winners()

        assert player in winners
        assert player.chips == 110  # 100 - 10 + 20

    def test_determine_winners_player_bust(self):
        table = Table(human_players=1, bot_players=0)
        player = table.players[0]

        player.calculate_score = MagicMock(return_value=25)
        player.is_busted = MagicMock(return_value=True)

        player.place_bet(10)
        winners = table.determine_winners()

        assert player not in winners
        assert player.chips == 90  # Ставка проиграна

    @patch('builtins.input', return_value='25')
    def test_human_betting(self, mock_input):
        table = Table(human_players=1, bot_players=0)
        player = table.players[0]

        with patch('builtins.print'):
            result = table.human_player_bet(player)

        assert result == True
        assert player.bet == 25
        assert player.chips == 75