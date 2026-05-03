from deck import Deck
from strategy_table import Strategy
from hand import Hand
from card import Card
from typing import Dict

class BlackjackGame:
    """Handles a single round of blackjack, including splits and doubles."""
    def __init__(self, deck: Deck, strategy: Strategy, rules: Dict):
        self.deck = deck
        self.strategy = strategy
        self.rules = rules

    def play_hand(self) -> Dict:
        # Initial deal
        player_hand = Hand([self.deck.deal(), self.deck.deal()])
        dealer_hand = Hand([self.deck.deal(), self.deck.deal()])
        dealer_upcard = dealer_hand.cards[0]
        initial_bet = 1
        total_bet = 1
        money_change = 0
        hand_results = []
        result_list = []
        strategy_positions = []  # Track strategy table positions

        # Check for player natural blackjack only (dealer's hidden card is unknown)
        player_blackjack = player_hand.is_blackjack()
        if player_blackjack:
            # Player has blackjack, now check dealer's hidden card
            dealer_blackjack = dealer_hand.is_blackjack()
            if dealer_blackjack:
                result = 'push'
            else:
                result = 'win_blackjack'
                money_change += 1.5  # 3:2 payout
            return {
                'result': [result],
                'money_change': money_change,
                'player_hands': [str(player_hand)],
                'dealer_hand': str(dealer_hand),
                'total_bet': total_bet,
                'strategy_positions': strategy_positions
            }

        # Record the strategy table position for the initial hand only
        if hasattr(self.strategy, 'get_table_position'):
            pos = self.strategy.get_table_position(player_hand, dealer_upcard)
            if pos is not None:
                strategy_positions.append(pos)

        # Check for split (only once, only on first two cards)
        hands_to_play = []
        if player_hand.can_split() and self.strategy.get_action(player_hand, dealer_upcard, self.rules) == 'P' and self.rules.get('allow_splits', True):
            card1 = player_hand.cards[0]
            card2 = player_hand.cards[1]
            new_hand1 = Hand([card1, self.deck.deal()])
            new_hand2 = Hand([card2, self.deck.deal()])
            hands_to_play = [(new_hand1, initial_bet)] + [(new_hand2, initial_bet)]
            total_bet += initial_bet
        else:
            hands_to_play = [(player_hand, initial_bet)]

        # Play each hand (no further splits allowed)
        for hand, bet in hands_to_play:
            # Do NOT record strategy table position for split hands
            doubled = False
            surrendered = False
            max_actions = 20
            action_count = 0
            while True:
                action_count += 1
                if action_count > max_actions:
                    break  # Prevent infinite loop, treat as stand
                action = self.strategy.get_action(hand, dealer_upcard, self.rules)
                if action == 'D/H':
                    if len(hand.cards) == 2 and self.rules.get('double_after_split', True):
                        hand.add_card(self.deck.deal())
                        bet *= 2
                        doubled = True
                        break
                    else:
                        action = 'H'
                        # fall through to hit
                elif action == 'D/S':
                    if len(hand.cards) == 2 and self.rules.get('double_after_split', True):
                        hand.add_card(self.deck.deal())
                        bet *= 2
                        doubled = True
                        break
                    else:
                        action = 'S'
                        # fall through to stand
                elif action == 'H' or action not in ['H', 'S', 'P', 'D/H', 'D/S', 'R/H']:
                    # Treat any unknown action (including 'D') as 'H' for safety
                    hand.add_card(self.deck.deal())
                    if hand.is_bust():
                        break
                    if len(hand.cards) >= 21:
                        break
                elif action == 'S':
                    break
                elif action == 'R/H':
                    # Surrender: only allowed as first action with 2 cards
                    if len(hand.cards) == 2:
                        money_change -= 0.5 * bet
                        surrendered = True
                        break
                    else:
                        action = 'H'
                        # fall through to hit
                else:
                    break
            if not surrendered:
                hand_results.append((hand, bet))
            else:
                result_list.append('surrender')

        # Dealer plays (if any player hand not bust or surrendered)
        if any(not h.is_bust() for h, _ in hand_results):
            while True:
                val, is_soft = dealer_hand.value()
                if val < 17 or (val == 17 and is_soft and self.rules.get('dealer_hits_soft_17', False)):
                    dealer_hand.add_card(self.deck.deal())
                else:
                    break

        # Settle bets for each hand
        dealer_val, _ = dealer_hand.value()
        for hand, bet in hand_results:
            player_val, _ = hand.value()
            if hand.is_blackjack() and len(hand.cards) == 2:
                # This can only happen for a split Ace + 10, which is NOT a blackjack, so treat as normal 21
                # (already handled above for natural blackjack)
                pass
            if hand.is_bust():
                money_change -= bet
                result = 'lose'
            elif dealer_hand.is_bust():
                money_change += bet
                result = 'win'
            elif player_val > dealer_val:
                money_change += bet
                result = 'win'
            elif player_val < dealer_val:
                money_change -= bet
                result = 'lose'
            else:
                result = 'push'
            result_list.append(result)

        return {
            'result': result_list,
            'money_change': money_change,
            'player_hands': [str(h) for h, _ in hand_results],
            'dealer_hand': str(dealer_hand),
            'total_bet': total_bet,
            'strategy_positions': strategy_positions
        } 