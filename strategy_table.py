# Blackjack strategy table: columns = dealer upcards 2-10, Ace
# Rows: sums 8-16, A/2-A/8, pairs 2/2-A/A (no J/J, Q/Q, K/K, just 10/10)
# Actions: H = Hit, S = Stand, D = Double, P = Split, D/H = Double if possible else Hit, D/S = Double if possible else Stand, R = Surrender

import random
from abc import ABC, abstractmethod

class Strategy(ABC):
    """
    Abstract base class for all blackjack strategies.
    All strategy implementations must inherit from this class and implement get_action.
    """
    
    @abstractmethod
    def get_action(self, player_hand, dealer_upcard, rules=None):
        """
        Determine the optimal action for a given player hand and dealer upcard.
        
        Args:
            player_hand: The player's current hand
            dealer_upcard: The dealer's visible card
            rules: Optional game rules that might affect strategy
            
        Returns:
            str: Action code ('H', 'S', 'P', 'D/H', 'D/S', 'R')
        """
        pass

class NaiveStrategy(Strategy):
    """Simple strategy: hit on anything below 17, stand otherwise."""
    
    def get_action(self, player_hand, dealer_upcard, rules=None):
        val, _ = player_hand.value()
        if val < 17:
            return 'H'
        else:
            return 'S'

class RandomStrategy(Strategy):
    """Random strategy: randomly choose between hit and stand."""
    
    def get_action(self, player_hand, dealer_upcard, rules=None):
        # Only return valid actions
        return random.choice(['H', 'S'])

class ExplicitTableStrategy(Strategy):
    """
    Strategy based on an explicit lookup table for optimal blackjack play.
    Uses a comprehensive strategy table for all possible hand combinations.
    """
    
    # Dealer upcard order for columns
    upcard_labels = ['2', '3', '4', '5', '6', '7', '8', '9', '10', 'A']
    # Row labels for printing and lookup
    row_labels = (
        [str(i) for i in range(8, 17)] +
        [f'A/{i}' for i in range(2, 9)] +
        [f'{i}/{i}' for i in range(2, 11)] + ['A/A']
    )
    # Explicit 2D strategy table: columns = dealer upcards 2-10, Ace
    # Rows: sums 8-16, A/2-A/8, pairs 2/2-A/A (no J/J, Q/Q, K/K, just 10/10)
    # Actions: H (hit), S (stand), P (split), D/H (double if possible else hit), D/S (double if possible else stand), R/H (surrender if possible else hit)
    strategy_table = [
        
        # Sums 8 to 16
        ['H','H','H','H','H','H','H','H','H','H'],  # 8
        ['H','D/H','D/H','D/H','D/H','H','H','H','H','H'],  # 9
        ['D/H','D/H','D/H','D/H','D/H','D/H','D/H','D/H','H','H'],  # 10
        ['D/H','D/H','D/H','D/H','D/H','D/H','D/H','D/H','D/H','D/H'],  # 11
        ['H','H','S','S','S','H','H','H','H','H'],  # 12
        ['S','S','S','S','S','H','H','H','H','H'],  # 13
        ['S','S','S','S','S','H','H','H','H','H'],  # 14
        ['S','S','S','S','S','H','H','H','H','H'],  # 15
        ['S','S','S','S','S','H','H','H','H','H'],  # 16

        # Soft hands A/2 to A/8
        ['H','H','H','D/H','D/H','H','H','H','H','H'],  # A/2
        ['H','H','H','D/H','D/H','H','H','H','H','H'],  # A/3
        ['H','H','D/H','D/H','D/H','H','H','H','H','H'],  # A/4
        ['H','H','D/H','D/H','D/H','H','H','H','H','H'],  # A/5
        ['H','D/H','D/H','D/H','D/H','H','H','H','H','H'],  # A/6
        ['S','D/S','D/S','D/S','D/S','S','S','H','H','H'],  # A/7
        ['S','S','S','S','S','S','S','S','S','S'],  # A/8

        # Pairs 2/2 to 10/10, A/A
        ['P','P','P','P','P','P','H','H','H','H'],  # 2/2
        ['P','P','P','P','P','P','H','H','H','H'],  # 3/3
        ['H','H','H','P','P','H','H','H','H','H'],  # 4/4
        ['D/H','D/H','D/H','D/H','D/H','D/H','D/H','D/H','H','H'],  # 5/5
        ['P','P','P','P','P','H','H','H','H','H'],  # 6/6
        ['P','P','P','P','P','P','H','H','H','H'],  # 7/7
        ['P','P','P','P','P','P','P','P','P','P'],  # 8/8
        ['P','P','P','P','P','S','P','P','S','S'],  # 9/9
        ['S','S','S','S','S','S','S','S','S','S'],  # 10/10
        ['P','P','P','P','P','P','P','P','P','P'],  # A/A
    ]

    def get_table_position(self, player_hand, dealer_upcard):
        """Get the row and column position in the strategy table for a given hand."""
        upcard = dealer_upcard.rank if dealer_upcard.rank != 'A' else 'A'
        try:
            col = self.upcard_labels.index(upcard)
        except ValueError:
            col = 8  # default to 10
        
        # Determine row
        if player_hand.is_pair():
            rank = player_hand.cards[0].rank
            if rank in ['J', 'Q', 'K']:
                row = self.row_labels.index('10/10')
            elif rank == 'A':
                row = self.row_labels.index('A/A')
            else:
                row = self.row_labels.index(f'{rank}/{rank}')
        else:
            val, is_soft = player_hand.value()
            if is_soft and 2 <= (val-11) <= 8:
                row = self.row_labels.index(f'A/{val-11}')
            elif 8 <= val <= 16:
                row = self.row_labels.index(str(val))
            else:
                # For hands with value 17+, return None (not in table)
                return None
        
        return row, col

    def get_action(self, player_hand, dealer_upcard, rules=None):
        upcard = dealer_upcard.rank if dealer_upcard.rank != 'A' else 'A'
        try:
            col = self.upcard_labels.index(upcard)
        except ValueError:
            col = 8  # default to 10
        # Determine row
        if player_hand.is_pair():
            rank = player_hand.cards[0].rank
            if rank in ['J', 'Q', 'K']:
                row = self.row_labels.index('10/10')
            elif rank == 'A':
                row = self.row_labels.index('A/A')
            else:
                row = self.row_labels.index(f'{rank}/{rank}')
        else:
            val, is_soft = player_hand.value()
            if is_soft and 2 <= (val-11) <= 8:
                row = self.row_labels.index(f'A/{val-11}')
            elif 8 <= val <= 16:
                row = self.row_labels.index(str(val))
            else:
                # For hands with value 17+, always stand
                return 'S'
        return self.strategy_table[row][col]

    def print_to_file(self, filename='strategy_table.txt'):
        with open(filename, 'w', encoding='utf-8') as f:
            f.write('BLACKJACK STRATEGY TABLE\n\n')
            f.write('      ' + ' '.join([f'{col:>3}' for col in self.upcard_labels]) + '\n')
            for i, row in enumerate(self.strategy_table):
                f.write(f'{self.row_labels[i]:>5} ')
                for action in row:
                    f.write(f'   {action}')
                f.write('\n')

class CustomTableStrategy(Strategy):
    """
    Customizable strategy table for user experiments.
    Modify custom_strategy_table and custom_row_labels/upcard_labels as desired.
    """
    upcard_labels = ['2', '3', '4', '5', '6', '7', '8', '9', '10', 'A']
    row_labels = (
        [str(i) for i in range(8, 17)] +
        [f'A/{i}' for i in range(2, 9)] +
        [f'{i}/{i}' for i in range(2, 11)] + ['A/A']
    )
    custom_strategy_table = [
        # Copy of the default table, user can edit this
        ['H','H','H','H','H','H','H','H','H','H'],  # 8
        ['H','D/H','D/H','D/H','D/H','H','H','H','H','H'],  # 9
        ['D/H','D/H','D/H','D/H','D/H','D/H','D/H','D/H','H','H'],  # 10
        ['D/H','D/H','D/H','D/H','D/H','D/H','D/H','D/H','D/H','D/H'],  # 11
        ['H','H','S','S','S','H','H','H','H','R/H'],  # 12
        ['S','S','S','S','S','H','H','H','H','R/H'],  # 13
        ['S','S','S','S','S','H','H','H','H','R/H'],  # 14
        ['S','S','S','S','S','H','H','H','R/H','R/H'],  # 15
        ['S','S','S','S','S','H','H','H','R/H','R/H'],  # 16

        ['H','H','H','D/H','D/H','H','H','H','H','H'],  # A/2
        ['H','H','H','D/H','D/H','H','H','H','H','H'],  # A/3
        ['H','H','D/H','D/H','D/H','H','H','H','H','H'],  # A/4
        ['H','H','D/H','D/H','D/H','H','H','H','H','H'],  # A/5
        ['H','D/H','D/H','D/H','D/H','H','H','H','H','H'],  # A/6
        ['S','D/S','D/S','D/S','D/S','S','S','H','H','H'],  # A/7
        ['S','S','S','S','S','S','S','S','S','S'],  # A/8

        ['P','P','P','P','P','P','H','H','H','R/H'],  # 2/2
        ['P','P','P','P','P','P','H','H','H','R/H'],  # 3/3
        ['H','H','H','P','P','H','H','H','H','H'],  # 4/4
        ['D/H','D/H','D/H','D/H','D/H','D/H','D/H','D/H','H','H'],  # 5/5
        ['P','P','P','P','P','H','H','H','H','R/H'],  # 6/6
        ['P','P','P','P','P','P','H','H','H','R/H'],  # 7/7
        ['P','P','P','P','P','P','P','P','P','P'],  # 8/8
        ['P','P','P','P','P','S','P','P','S','S'],  # 9/9
        ['S','S','S','S','S','S','S','S','S','S'],  # 10/10
        ['P','P','P','P','P','P','P','P','P','P'],  # A/A
    ]
    def get_action(self, player_hand, dealer_upcard, rules=None):
        upcard = dealer_upcard.rank if dealer_upcard.rank != 'A' else 'A'
        try:
            col = self.upcard_labels.index(upcard)
        except ValueError:
            col = 8  # default to 10
        if player_hand.is_pair():
            rank = player_hand.cards[0].rank
            if rank in ['J', 'Q', 'K']:
                row = self.row_labels.index('10/10')
            elif rank == 'A':
                row = self.row_labels.index('A/A')
            else:
                row = self.row_labels.index(f'{rank}/{rank}')
        else:
            val, is_soft = player_hand.value()
            if is_soft and 2 <= (val-11) <= 8:
                row = self.row_labels.index(f'A/{val-11}')
            elif 8 <= val <= 16:
                row = self.row_labels.index(str(val))
            else:
                return 'S'
        return self.custom_strategy_table[row][col]
    def get_table_position(self, player_hand, dealer_upcard):
        upcard = dealer_upcard.rank if dealer_upcard.rank != 'A' else 'A'
        try:
            col = self.upcard_labels.index(upcard)
        except ValueError:
            col = 8
        if player_hand.is_pair():
            rank = player_hand.cards[0].rank
            if rank in ['J', 'Q', 'K']:
                row = self.row_labels.index('10/10')
            elif rank == 'A':
                row = self.row_labels.index('A/A')
            else:
                row = self.row_labels.index(f'{rank}/{rank}')
        else:
            val, is_soft = player_hand.value()
            if is_soft and 2 <= (val-11) <= 8:
                row = self.row_labels.index(f'A/{val-11}')
            elif 8 <= val <= 16:
                row = self.row_labels.index(str(val))
            else:
                return None
        return row, col
