from card import Card
import random

class Deck:
    """Represents a shoe of 6 decks, handles shuffling and dealing."""
    suits = ['♠', '♥', '♦', '♣']
    ranks = ['2', '3', '4', '5', '6', '7', '8', '9', '10', 'J', 'Q', 'K', 'A']

    def __init__(self, num_decks: int = 6):
        self.num_decks = num_decks
        self.cards = []
        self._build_deck()
        self.shuffle()

    def _build_deck(self):
        self.cards = [Card(rank, suit)
                      for _ in range(self.num_decks)
                      for suit in self.suits
                      for rank in self.ranks]

    def shuffle(self):
        random.shuffle(self.cards)

    def deal(self) -> Card:
        if not self.cards:
            self._build_deck()
            self.shuffle()
        return self.cards.pop()

    def cards_left(self) -> int:
        return len(self.cards) 