import random
# from cards import *
from project.game.players import *


class Table:
    def __init__(self, human_players=1, bot_players=2, max_rounds=None,
                 bot_strategies=None, initial_chips=100):
        """
        Инициализация стола

        Args:
            human_players: количество человеческих игроков
            bot_players: количество ботов
            max_rounds: максимальное количество раундов
            bot_strategies: список стратегий для ботов (если None - случайные)
            initial_chips: начальное количество фишек
        """
        self.human_players_count = human_players
        self.bot_players_count = bot_players
        self.max_rounds = max_rounds
        self.initial_chips = initial_chips

        # Создаем игроков
        self.players = self._create_players(bot_strategies)
        self.dealer = Dealer()
        self.deck = Deck()
        self.current_round = 0
        self.active_players = self.players.copy()
        self.game_history = []

    def _create_players(self, bot_strategies):
        """Создает список игроков"""
        players = []

        # Создаем человеческих игроков
        for i in range(self.human_players_count):
            player = Player(f"Игрок_{i + 1}", self.initial_chips, is_human=True)
            players.append(player)

        # Создаем боты
        all_strategies = list(PlayerStrategy)
        for i in range(self.bot_players_count):
            if bot_strategies and i < len(bot_strategies):
                strategy = bot_strategies[i]
            else:
                strategy = random.choice(all_strategies)

            bot = Player(f"Бот_{i + 1}", self.initial_chips, strategy=strategy, is_human=False)
            players.append(bot)

        return players

    def deal_initial_cards(self):
        """Раздача начальных карт"""
        for _ in range(2):
            for player in self.active_players + [self.dealer]:
                player.receive_card(self.deck.deal())

    def human_player_turn(self, player):
        """Ход человеческого игрока"""
        print(f"\n--- Ход {player.name} ---")
        print(f"Ваши карты: {player}")

        while not player.stand and not player.is_busted():
            action = input("Выберите действие (hit/stand): ").lower().strip()

            if action == 'hit':
                player.receive_card(self.deck.deal())
                print(f"Вы получили: {player.hand[-1]}")
                print(f"Текущая рука: {player}")

                if player.is_busted():
                    print("Перебор! Вы проиграли.")
                    break
            elif action == 'stand':
                player.stand = True
                print(f"{player.name} остановился.")
            else:
                print("Неверная команда. Используйте 'hit' или 'stand'.")

    def bot_player_turn(self, player):
        """Ход бота"""
        print(f"\n--- Ход {player.name} ({player.strategy.name}) ---")
        print(f"Карты: {player}")

        while not player.stand and not player.is_busted():
            decision = player.make_decision()

            if decision == "hit":
                player.receive_card(self.deck.deal())
                print(f"{player.name} берет карту: {player.hand[-1]}")
                print(f"Теперь: {player}")

                if player.is_busted():
                    print(f"{player.name} перебрал!")
                    break
            else:
                player.stand = True
                print(f"{player.name} останавливается.")
                break

    def player_turn(self, player):
        """Общий метод хода игрока"""
        state_before = self._capture_game_state()

        if player.is_human:
            self.human_player_turn(player)
        else:
            self.bot_player_turn(player)

        state_after = self._capture_game_state()
        self.game_history.append({
            'action': f'{player.name}_turn',
            'player_type': 'human' if player.is_human else 'bot',
            'strategy': player.strategy.name if player.strategy else None,
            'state_before': state_before,
            'state_after': state_after
        })

    def dealer_turn(self):
        """Ход диллера"""
        state_before = self._capture_game_state()

        print(f"\n--- Ход диллера ({self.dealer.strategy.name}) ---")
        print(self.dealer.show_hand())

        while self.dealer.should_hit() and not self.dealer.is_busted():
            self.dealer.receive_card(self.deck.deal())
            print(f"Диллер получил: {self.dealer.hand[-1]}")
            print(f"Рука диллера: {self.dealer}")

            if self.dealer.is_busted():
                print("Диллер перебрал!")
                break

        state_after = self._capture_game_state()
        self.game_history.append({
            'action': 'dealer_turn',
            'strategy': self.dealer.strategy.name,
            'state_before': state_before,
            'state_after': state_after
        })

    def determine_winners(self):
        """Определение победителей"""
        dealer_score = self.dealer.calculate_score()
        dealer_busted = self.dealer.is_busted()

        winners = []

        for player in self.active_players:
            player_score = player.calculate_score()
            player_busted = player.is_busted()

            if player_busted:
                # Игрок проиграл, ставка не возвращается
                pass
            elif dealer_busted:
                player.win_bet()
                winners.append(player)
            elif player_score > dealer_score:
                player.win_bet()
                winners.append(player)
            elif player_score == dealer_score:
                player.push()

        return winners

    def cleanup_round(self):
        """Очистка после раунда"""
        for player in self.active_players + [self.dealer]:
            player.clear_hand()

        # Удаляем игроков без фишек
        self.active_players = [player for player in self.active_players if player.chips > 0]

    def _capture_game_state(self):
        """Захватывает текущее состояние игры для истории"""
        return {
            'round': self.current_round,
            'dealer_score': self.dealer.calculate_score(),
            'dealer_hand_size': len(self.dealer.hand),
            'dealer_strategy': self.dealer.strategy.name,
            'active_players': len(self.active_players),
            'players_state': [
                {
                    'name': player.name,
                    'type': 'human' if player.is_human else 'bot',
                    'strategy': player.strategy.name if player.strategy else None,
                    'chips': player.chips,
                    'score': player.calculate_score(),
                    'hand_size': len(player.hand),
                    'busted': player.is_busted(),
                    'stand': player.stand,
                    'bet': player.bet
                }
                for player in self.active_players
            ]
        }

    def show_game_state(self):
        """Показывает текущее состояние игры"""
        state = self._capture_game_state()
        print(f"\n=== Раунд {state['round']} ===")
        print(
            f"Диллер: {len(self.dealer.hand)} карт, очки: {state['dealer_score']}, стратегия: {state['dealer_strategy']}")
        print("Игроки:")
        for player_state in state['players_state']:
            player_type = "Человек" if player_state['type'] == 'human' else "Бот"
            strategy_str = f", стратегия: {player_state['strategy']}" if player_state['strategy'] else ""
            status = "STAND" if player_state['stand'] else "PLAYING"
            busted = " BUSTED" if player_state['busted'] else ""
            bet_info = f", ставка: {player_state['bet']}" if player_state['bet'] > 0 else ""
            print(f"  {player_state['name']} [{player_type}{strategy_str}]: "
                  f"{player_state['score']} очков, {player_state['chips']} фишек{bet_info}, "
                  f"{player_state['hand_size']} карт [{status}{busted}]")

    def human_player_bet(self, player):
        """Ставка человеческого игрока"""
        print(f"\n--- Ставка {player.name} ---")
        print(f"Ваши фишки: {player.chips}")

        while True:
            try:
                bet_input = input(f"Сделайте ставку (1-{player.chips}): ").strip()

                # Проверяем специальные команды
                if bet_input.lower() == 'all':
                    bet_amount = player.chips
                elif bet_input.lower() == 'half':
                    bet_amount = player.chips // 2
                else:
                    bet_amount = int(bet_input)

                # Проверяем валидность ставки
                if bet_amount < 1:
                    print("Ставка должна быть не менее 1 фишки!")
                    continue
                elif bet_amount > player.chips:
                    print(f"Недостаточно фишек! У вас только {player.chips} фишек.")
                    continue

                # Размещаем ставку
                if player.place_bet(bet_amount):
                    print(f"{player.name} ставит {bet_amount} фишек")
                    break
                else:
                    print("Ошибка при размещении ставки!")

            except ValueError:
                print("Пожалуйста, введите число, 'all' или 'half'!")
            except KeyboardInterrupt:
                print("\nИгра прервана!")
                return False

        return True

    def auto_place_bets(self):
        """Автоматическая расстановка ставок для ботов"""
        for player in self.active_players:
            if player.is_human:
                # Пропускаем человеческих игроков - они делают ставки вручную
                continue
            else:
                # Для ботов - ставка зависит от стратегии
                if player.strategy == PlayerStrategy.CONSERVATIVE:
                    bet_amount = max(1, min(10, player.chips // 10))
                elif player.strategy == PlayerStrategy.AGGRESSIVE:
                    bet_amount = max(1, min(30, player.chips // 3))
                else:  # MODERATE, RANDOM
                    bet_amount = max(1, min(20, player.chips // 5))

                player.place_bet(bet_amount)
                print(f"{player.name} ставит {bet_amount} фишек")

    def place_bets_phase(self):
        """Фаза размещения ставок"""
        print("\n--- Фаза ставок ---")

        # Сначала человеческие игроки делают ставки
        human_players = [p for p in self.active_players if p.is_human]
        for player in human_players:
            if not self.human_player_bet(player):
                return False  # Игра прервана

        # Затем боты делают автоматические ставки
        self.auto_place_bets()

        return True

    def play_round(self):
        """Играет один раунд"""
        self.current_round += 1
        round_state = self._capture_game_state()
        self.game_history.append({
            'action': 'round_start',
            'state': round_state
        })

        print(f"\n{'=' * 60}")
        print(f"РАУНД {self.current_round}")
        print(f"{'=' * 60}")

        # Фаза ставок
        if not self.place_bets_phase():
            return []  # Игра прервана

        # Раздача карт
        self.deal_initial_cards()
        self.show_game_state()

        # Ходы игроков (сначала человеческие, потом боты)
        human_players = [p for p in self.active_players if p.is_human]
        bot_players = [p for p in self.active_players if not p.is_human]

        for player in human_players + bot_players:
            self.player_turn(player)

        # Ход диллера (только если есть игроки, которые не перебрали)
        if any(not player.is_busted() for player in self.active_players):
            self.dealer_turn()

        # Определение победителей
        winners = self.determine_winners()

        # Запись результатов раунда
        final_state = self._capture_game_state()
        self.game_history.append({
            'action': 'round_end',
            'winners': [w.name for w in winners],
            'state': final_state
        })

        # Очистка
        self.cleanup_round()

        return winners

    def play_game(self):
        """Основной игровой цикл"""
        print("Добро пожаловать в Blackjack!")
        print(f"Игроков: {self.human_players_count} человек, {self.bot_players_count} ботов")
        print(f"Максимум раундов: {self.max_rounds or 'без ограничения'}")
        print("\nКоманды для ставок:")
        print("  - Введите число для конкретной ставки")
        print("  - 'all' для ставки всех фишек")
        print("  - 'half' для ставки половины фишек")

        while (self.active_players and
               (self.max_rounds is None or self.current_round < self.max_rounds)):

            winners = self.play_round()

            if not winners and self.current_round == 0:
                # Игра была прервана во время ставок
                break

            print(f"\nПобедители раунда: {[w.name for w in winners]}")

            # Проверка условий окончания игры
            if not self.active_players:
                print("\nИгра окончена! Все игроки проиграли.")
                break

            if self.max_rounds and self.current_round >= self.max_rounds:
                print(f"\nДостигнуто максимальное количество раундов: {self.max_rounds}")
                break

            # Продолжение игры
            if any(p.is_human for p in self.active_players):
                print("\n" + "-" * 40)
                continue_game = input("Продолжить игру? (y/n): ").lower().strip()
                if continue_game != 'y':
                    break
            else:
                # Если остались только боты, продолжаем автоматически
                print("\nПродолжаем игру...")

        # Финальные результаты
        self.show_final_results()
        return self._capture_game_state()

    def show_final_results(self):
        """Показывает финальные результаты"""
        print(f"\n{'=' * 50}")
        print("ФИНАЛЬНЫЕ РЕЗУЛЬТАТЫ")
        print(f"{'=' * 50}")

        human_players = [p for p in self.players if p.is_human]
        bot_players = [p for p in self.players if not p.is_human]

        print("\nЧеловеческие игроки:")
        for player in human_players:
            status = "В игре" if player in self.active_players else "Выбыл"
            profit = player.chips - self.initial_chips
            profit_str = f" ({profit:+d})" if profit != 0 else ""
            print(f"  {player.name}: {player.chips} фишек{profit_str} ({status})")

        print("\nБоты:")
        for player in bot_players:
            status = "В игре" if player in self.active_players else "Выбыл"
            strategy = f" ({player.strategy.name})" if player.strategy else ""
            profit = player.chips - self.initial_chips
            profit_str = f" ({profit:+d})" if profit != 0 else ""
            print(f"  {player.name}{strategy}: {player.chips} фишек{profit_str} ({status})")

        if self.active_players:
            best_player = max(self.active_players, key=lambda p: p.chips)
            player_type = "Человек" if best_player.is_human else "Бот"
            total_profit = best_player.chips - self.initial_chips
            profit_str = f" (прибыль: {total_profit:+d})" if total_profit != 0 else ""
            print(f"\n🏆 Победитель: {best_player.name} ({player_type}) с {best_player.chips} фишками{profit_str}!")
        else:
            print("\nВсе игроки проиграли!")