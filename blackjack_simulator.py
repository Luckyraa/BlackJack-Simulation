from deck import Deck
from blackjack_game import BlackjackGame
from strategy_table import Strategy
import matplotlib.pyplot as plt
from collections import defaultdict

class BlackjackSimulator:
    """Runs multiple rounds, collects statistics, outputs results."""
    def __init__(self, num_hands: int, strategy: Strategy, rules: dict):
        self.num_hands = num_hands
        self.strategy = strategy
        self.rules = rules
        self.stats = {
            'win': 0,
            'lose': 0,
            'push': 0,
            'win_blackjack': 0,
            'lose_blackjack': 0,
            'surrender': 0,
            'money': 0.0,
            'money_curve': [],
            'hand_frequencies': defaultdict(int),
            'strategy_table_frequencies': defaultdict(int),  # Track frequencies by strategy table position
            'strategy_table_wins': defaultdict(int),  # Track wins by strategy table position
            'total_bet': 0
        }

    def run(self):
        deck = Deck(num_decks=6)
        for i in range(self.num_hands):
            # Reshuffle if deck is empty
            if deck.cards_left() < 52:  # reshuffle with less than 1 deck left
                deck = Deck(num_decks=6)
            game = BlackjackGame(deck, self.strategy, self.rules)
            result = game.play_hand()
            # Update stats
            res = result['result']
            if isinstance(res, list):
                for r in res:
                    if r in self.stats:
                        self.stats[r] += 1
            else:
                if res in self.stats:
                    self.stats[res] += 1
            self.stats['money'] += result['money_change']
            self.stats['money_curve'].append(self.stats['money'])
            self.stats['total_bet'] += result['total_bet']
            # Track hand frequencies
            for hand_str in result['player_hands']:
                self.stats['hand_frequencies'][hand_str] += 1
            # Track strategy table frequencies and wins
            positions = result.get('strategy_positions', [])
            win_types = {'win', 'win_blackjack'}
            is_win = False
            if isinstance(res, list):
                is_win = any(r in win_types for r in res)
            else:
                is_win = res in win_types
            for pos in positions:
                self.stats['strategy_table_frequencies'][pos] += 1
                if is_win:
                    self.stats['strategy_table_wins'][pos] += 1

    def write_results(self, filename: str):
        with open(filename, 'w', encoding='utf-8') as f:
            f.write("Blackjack Simulation Results\n")
            f.write(f"Total hands played: {self.num_hands}\n")
            f.write(f"Wins: {self.stats['win']}\n")
            f.write(f"Losses: {self.stats['lose']}\n")
            f.write(f"Pushes: {self.stats['push']}\n")
            f.write(f"Blackjack Wins: {self.stats['win_blackjack']}\n")
            f.write(f"Blackjack Losses: {self.stats['lose_blackjack']}\n")
            f.write(f"Total money won/lost: {self.stats['money']:.2f}\n")
            f.write(f"Total bet: {self.stats['total_bet']}\n")
            f.write(f"Average return per hand: {self.stats['money']/self.num_hands:.4f}\n")
            f.write("\nHand Frequency Table (top 20):\n")
            sorted_freq = sorted(self.stats['hand_frequencies'].items(), key=lambda x: -x[1])
            for hand, freq in sorted_freq[:20]:
                f.write(f"{hand}: {freq}\n")

    def plot_money_curve(self, filename: str):
        plt.figure(figsize=(10, 6))
        plt.plot(self.stats['money_curve'], label='Money over hands', color='blue')
        plt.xlabel('Number of Hands Played')
        plt.ylabel('Money ($)')
        plt.title('Money as a Function of Number of Hands Played')
        plt.grid(True, linestyle='--', alpha=0.6)
        plt.legend()
        plt.tight_layout()
        plt.savefig(filename)
        plt.close() 