from card import Card
from typing import List, Optional, Tuple

class Hand:
    """Represents a blackjack hand (player or dealer)."""
    def __init__(self, cards: Optional[List[Card]] = None):
        self.cards = cards if cards else []
        self.doubled = False  # Track if this hand was doubled
        self.split_from = None  # Track if this hand was created from a split

    def add_card(self, card: Card):
        self.cards.append(card)

    def value(self) -> Tuple[int, bool]:
        total = 0
        aces = 0
        for card in self.cards:
            if card.rank == 'A':
                aces += 1
            total += card.value()
        # Try to count one ace as 11 if it doesn't bust
        is_soft = False
        if aces > 0 and total + 10 <= 21:
            total += 10
            is_soft = True
        return total, is_soft

    def is_blackjack(self) -> bool:
        return len(self.cards) == 2 and self.value()[0] == 21

    def is_bust(self) -> bool:
        return self.value()[0] > 21

    def can_split(self) -> bool:
        return self.is_pair() and len(self.cards) == 2

    def is_pair(self) -> bool:
        return len(self.cards) == 2 and self.cards[0].rank == self.cards[1].rank

    def __str__(self):
        cards_str = ', '.join(str(card) for card in self.cards)
        val, is_soft = self.value()
        soft_str = " (soft)" if is_soft else ""
        return f"[{cards_str}] = {val}{soft_str}" 