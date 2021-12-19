# con_hand_evaluator_v1
random.seed()
NUM_CARDS_IN_DECK = 52
NUM_VALUES_IN_DECK = 13
NUM_SUITS_IN_DECK = 4
NUM_CARDS_IN_HAND = 5
ACE_VALUE = 2 ** 13
STRAIGHT_LOW_ACE_INDICATOR = int("10000000011110", 2)
TEN_CARD_POSITION = 8
RANK_BASE_VALUE = 10 ** 9
RANK_ORDER = [
    'high_card',
    'pair',
    'two_pairs',
    'trips',
    'straight',
    'flush',
    'full_house',
    'quads',
    'straight_flush',
    'royal_flush',
]
DECK = [
    '2c', '3c', '4c', '5c', '6c', '7c', '8c', '9c', 'Tc', 'Jc', 'Qc', 'Kc', 'Ac',
    '2d', '3d', '4d', '5d', '6d', '7d', '8d', '9d', 'Td', 'Jd', 'Qd', 'Kd', 'Ad',
    '2h', '3h', '4h', '5h', '6h', '7h', '8h', '9h', 'Th', 'Jh', 'Qh', 'Kh', 'Ah',
    '2s', '3s', '4s', '5s', '6s', '7s', '8s', '9s', 'Ts', 'Js', 'Qs', 'Ks', 'As',
]
RANKS = {
    '2c': 13, '2d': 13, '2h': 13, '2s': 13,
    '3c': 12, '3d': 12, '3h': 12, '3s': 12,
    '4c': 11, '4d': 11, '4h': 11, '4s': 11,
    '5c': 10, '5d': 10, '5h': 10, '5s': 10,
    '6c': 9, '6d': 9, '6h': 9, '6s': 9,
    '7c': 8, '7d': 8, '7h': 8, '7s': 8,
    '8c': 7, '8d': 7, '8h': 7, '8s': 7,
    '9c': 6, '9d': 6, '9h': 6, '9s': 6,
    'Tc': 5, 'Td': 5, 'Th': 5, 'Ts': 5,
    'Jc': 4, 'Jd': 4, 'Jh': 4, 'Js': 4,
    'Qc': 3, 'Qd': 3, 'Qh': 3, 'Qs': 3,
    'Kc': 2, 'Kd': 2, 'Kh': 2, 'Ks': 2,
    'Ac': 1, 'Ad': 1, 'Ah': 1, 'As': 1,
}

# Python program to  illustrate sum of two numbers.
def reduce(function, iterable, initializer=None):
    value = initializer
    i = 0
    for element in iterable:
        value = function(value, element, i)
        i += 1
    return value


def rank_value_fn(total, val, index):
    return total + \
        ((val == 1 and (2**(index+1))) or 0) + \
        ((val > 1 and (2**(index+1) * ACE_VALUE * val)) or 0)


def evaluate_5_card_ints(hand: list) -> int:
    '''
    A: 8192
    K: 4096
    Q: 2048
    J: 1024
    T:  512
    9:  256
    8:  128
    7:   64
    6:   32
    5:   16
    4:    8
    3:    4
    2:    2
    A:    1

    10: Royal Flush
    9: Straight Flush
    8: Quads (4 of a kind)
    7: Full House
    6: Flush
    5: Straight
    4: Trips (3 of a kind)
    3: Two Pairs
    2: Pair
    1: High Card

    '''
    assert len(hand) == 5, 'Invalid number of cards.'
    suits = [0] * NUM_SUITS_IN_DECK
    values = [0] * NUM_VALUES_IN_DECK

    for card in hand:
        suits[card // NUM_VALUES_IN_DECK] += 1
        values[card % NUM_VALUES_IN_DECK] += 1

    rank_value = reduce(
        rank_value_fn,
        values,
        initializer=0
    )

    if 1 in values:
        first_card_index = values.index(1)
    else:
        first_card_index = -1

    is_straight = False
    if first_card_index >= 0:
        c = values[first_card_index:first_card_index+5]
        if rank_value == STRAIGHT_LOW_ACE_INDICATOR or \
            (len(c) == 5 and all([d == 1 for d in c])):
            is_straight = True

    n_pairs = values.count(2)
    is_trips = 3 in values
    ranks = {
        'royal_flush': False,
        'straight_flush': False,
        'quads': 4 in values,
        'full_house': is_trips and n_pairs == 1,
        'flush': NUM_CARDS_IN_HAND in suits,
        'straight': is_straight,
        'trips': is_trips,
        'two_pairs': n_pairs == 2,
        'pair': n_pairs == 1,
        'high_card': True,
    }
    ranks['straight_flush'] = ranks['flush'] and ranks['straight']
    ranks['royal_flush'] = ranks['straight_flush'] and first_card_index == TEN_CARD_POSITION
    
    rank_index = 0
    #rank_description = ""
    for r in range(len(RANK_ORDER)-1, -1, -1):
        rank = RANK_ORDER[r]
        if ranks[rank]:
            rank_index = r
            #rank_description = rank
            break
    
    rank_value += rank_index * RANK_BASE_VALUE - \
        ((rank_value == STRAIGHT_LOW_ACE_INDICATOR and ACE_VALUE - 1) or 0)

    return rank_value


def evaluate_7_card_ints(hand: list) -> int:
    best_rank = None
    assert len(hand) == 7, 'Invalid number of cards.'
    # 7 choose 5
    for i in range(7):
        for j in range(i+1, 7):
            new_hand = hand[0:i] + hand[i+1:j] + hand[j+1:]
            rank = evaluate_5_card_ints(new_hand)
            if best_rank is None or best_rank < rank:
                best_rank = rank
    return best_rank


def evaluate_omaha(hole_cards: list, board: list) -> int:
    best_rank = None
    assert len(hole_cards) == 4, 'Invalid number of hole cards'
    assert len(board) == 5, 'Invalid number of board cards'
    n = 0
    for b in range(0, 4):
        for r in range(b+1, 5):
            for x in range(0, 3):
                for y in range(x+1, 4):
                    new_hand = list(board)
                    new_hand[b] = hole_cards[x]
                    new_hand[r] = hole_cards[y]
                    rank = evaluate_5_card_ints(new_hand)
                    if best_rank is None or best_rank < rank:
                        best_rank = rank
                    n += 1
    return best_rank


@export
def evaluate(hand: list) -> int:
    if len(hand) == 1:
        # Simple lookup
        return 14 - RANKS[hand[0]]
    else:
        hand = [DECK.index(card) for card in hand]
        if len(hand) == 5:
            return evaluate_5_card_ints(hand)
        elif len(hand) == 7:
            return evaluate_7_card_ints(hand)
        elif len(hand) == 9:
            # Assume board is the last 5 cards
            return evaluate_omaha(hand[:4], hand[4:])            
        else:
            assert False, 'Invalid number of cards specified: {}'.format(len(hand))


@export
def get_deck(shuffled: bool = True) -> list:
    cards = DECK.copy()
    if shuffled:
        random.shuffle(cards)
    return cards
