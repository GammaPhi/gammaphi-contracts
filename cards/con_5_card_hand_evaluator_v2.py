MAX_STRAIGHT_FLUSH  = 10
MAX_FOUR_OF_A_KIND  = 166
MAX_FULL_HOUSE      = 322 
MAX_FLUSH           = 1599
MAX_STRAIGHT        = 1609
MAX_THREE_OF_A_KIND = 2467
MAX_TWO_PAIR        = 3325
MAX_PAIR            = 6185
MAX_HIGH_CARD       = 7462

MAX_TO_RANK_CLASS = {
    MAX_STRAIGHT_FLUSH: 1,
    MAX_FOUR_OF_A_KIND: 2,
    MAX_FULL_HOUSE: 3,
    MAX_FLUSH: 4,
    MAX_STRAIGHT: 5,
    MAX_THREE_OF_A_KIND: 6,
    MAX_TWO_PAIR: 7,
    MAX_PAIR: 8,
    MAX_HIGH_CARD: 9
}

RANK_CLASS_TO_STRING = {
    1: "Straight Flush",
    2: "Four of a Kind",
    3: "Full House",
    4: "Flush",
    5: "Straight",
    6: "Three of a Kind",
    7: "Two Pair",
    8: "Pair",
    9: "High Card"
}


# create dictionaries
flush_lookup = {}
unsuited_lookup = {}


def combinations(iterable, r):
    # combinations('ABCD', 2) --> AB AC AD BC BD CD
    # combinations(range(4), 3) --> 012 013 023 123
    pool = tuple(iterable)
    n = len(pool)
    if r > n:
        return
    ret = []
    indices = range(r)
    t = []
    for i in indices:
        t.append(pool[i])
    ret.append(tuple(t))
    while True:
        for i in reversed(range(r)):
            if indices[i] != i + n - r:
                break
        else:
            return ret
        indices[i] += 1
        for j in range(i+1, r):
            indices[j] = indices[j-1] + 1
        t = []
        for i in indices:
            t.append(pool[i])
        ret.append(tuple(t))            

def flushes():
    """
    Straight flushes and flushes. 
    Lookup is done on 13 bit integer (2^13 > 7462):
    xxxbbbbb bbbbbbbb => integer hand index
    """

    # straight flushes in rank order
    straight_flushes = [
        7936,  # int('0b1111100000000', 2), # royal flush
        3968,  # int('0b111110000000', 2),
        1984,  # int('0b11111000000', 2),
        992,   # int('0b1111100000', 2),
        496,   # int('0b111110000', 2),
        248,   # int('0b11111000', 2),
        124,   # int('0b1111100', 2),
        62,    # int('0b111110', 2),
        31,    # int('0b11111', 2),
        4111   # int('0b1000000001111', 2) # 5 high
    ]

    # now we'll dynamically generate all the other
    # flushes (including straight flushes)
    flushes = []
    bits = int('0b11111', 2)
    # 1277 = number of high cards
    # 1277 + len(str_flushes) is number of hands with all cards unique rank
    t = int((bits | (bits - 1))) + 1
    next = t | ((int(((t & -t) / (bits & -bits))) >> 1) - 1)
    for i in range(1277 + len(straight_flushes) - 1):   # we also iterate over SFs
        # pull the next flush pattern from our generator
        f = next

        # if this flush matches perfectly any
        # straight flush, do not add it
        notSF = True
        for sf in straight_flushes:
            # if f XOR sf == 0, then bit pattern 
            # is same, and we should not add
            if not f ^ sf:
                notSF = False

        if notSF:
            flushes.append(f)

        t = (next | (next - 1)) + 1 
        next = t | ((((t & -t) // (next & -next)) >> 1) - 1)

    # we started from the lowest straight pattern, now we want to start ranking from
    # the most powerful hands, so we reverse
    flushes.reverse()

    # now add to the lookup map:
    # start with straight flushes and the rank of 1
    # since it is the best hand in poker
    # rank 1 = Royal Flush!
    rank = 1
    for sf in straight_flushes:
        prime_product = prime_product_from_rankbits(sf)
        flush_lookup[prime_product] = rank
        rank += 1

    # we start the counting for flushes on max full house, which
    # is the worst rank that a full house can have (2,2,2,3,3)
    rank = MAX_FULL_HOUSE + 1
    for f in flushes:
        prime_product = prime_product_from_rankbits(f)
        flush_lookup[prime_product] = rank
        rank += 1

    # we can reuse these bit sequences for straights
    # and high cards since they are inherently related
    # and differ only by context 
    straight_and_highcards(straight_flushes, flushes)

def straight_and_highcards(straights, highcards):
    """
    Unique five card sets. Straights and highcards. 
    Reuses bit sequences from flush calculations.
    """
    rank = MAX_FLUSH + 1

    for s in straights:
        prime_product = prime_product_from_rankbits(s)
        unsuited_lookup[prime_product] = rank
        rank += 1

    rank = MAX_PAIR + 1
    for h in highcards:
        prime_product = prime_product_from_rankbits(h)
        unsuited_lookup[prime_product] = rank
        rank += 1

def multiples():
    """
    Pair, Two Pair, Three of a Kind, Full House, and 4 of a Kind.
    """
    backwards_ranks = list(range(len(INT_RANKS) - 1, -1, -1))

    # 1) Four of a Kind
    rank = MAX_STRAIGHT_FLUSH + 1

    # for each choice of a set of four rank
    for i in backwards_ranks:

        # and for each possible kicker rank
        kickers = backwards_ranks[:]
        kickers.remove(i)
        for k in kickers:
            product = PRIMES[i]**4 * PRIMES[k]
            unsuited_lookup[product] = rank
            rank += 1
    
    # 2) Full House
    rank = MAX_FOUR_OF_A_KIND + 1

    # for each three of a kind
    for i in backwards_ranks:

        # and for each choice of pair rank
        pairranks = backwards_ranks[:]
        pairranks.remove(i)
        for pr in pairranks:
            product = PRIMES[i]**3 * PRIMES[pr]**2
            unsuited_lookup[product] = rank
            rank += 1

    # 3) Three of a Kind
    rank = MAX_STRAIGHT + 1

    # pick three of one rank
    for r in backwards_ranks:

        kickers = backwards_ranks[:]
        kickers.remove(r)
        gen = combinations(kickers, 2)

        for kickers in gen:
            c1, c2 = kickers
            product = PRIMES[r]**3 * PRIMES[c1] * PRIMES[c2]
            unsuited_lookup[product] = rank
            rank += 1

    # 4) Two Pair
    rank = MAX_THREE_OF_A_KIND + 1

    tpgen = combinations(backwards_ranks, 2)
    for tp in tpgen:

        pair1, pair2 = tp
        kickers = backwards_ranks[:]
        kickers.remove(pair1)
        kickers.remove(pair2)
        for kicker in kickers:

            product = PRIMES[pair1]**2 * PRIMES[pair2]**2 * PRIMES[kicker]
            unsuited_lookup[product] = rank
            rank += 1

    # 5) Pair
    rank = MAX_TWO_PAIR + 1

    # choose a pair
    for pairrank in backwards_ranks:

        kickers = backwards_ranks[:]
        kickers.remove(pairrank)
        kgen = combinations(kickers, 3)

        for kickers in kgen:

            k1, k2, k3 = kickers
            product = PRIMES[pairrank]**2 * PRIMES[k1] \
                * PRIMES[k2] * PRIMES[k3]
            unsuited_lookup[product] = rank
            rank += 1

def write_table_to_disk(table, filepath):
    """
    Writes lookup table to disk
    """
    with open(filepath, 'w') as f:
        for prime_prod, rank in table.iteritems():
            f.write(str(prime_prod) + "," + str(rank) + '\n')

# the basics
STR_RANKS = '23456789TJQKA'
INT_RANKS = range(13)
PRIMES = [2, 3, 5, 7, 11, 13, 17, 19, 23, 29, 31, 37, 41]

# conversion from string => int
CHAR_RANK_TO_INT_RANK = dict(zip(list(STR_RANKS), INT_RANKS))
CHAR_SUIT_TO_INT_SUIT = {
    's': 1,  # spades
    'h': 2,  # hearts
    'd': 4,  # diamonds
    'c': 8,  # clubs
}
INT_SUIT_TO_CHAR_SUIT = 'xshxdxxxc'

def new(string):
    """
    Converts Card string to binary integer representation of card, inspired by:
    
    http://www.suffecool.net/poker/evaluator.html
    """

    rank_char = string[0]
    suit_char = string[1]
    rank_int = CHAR_RANK_TO_INT_RANK[rank_char]
    suit_int = CHAR_SUIT_TO_INT_SUIT[suit_char]
    rank_prime = PRIMES[rank_int]

    bitrank = 1 << rank_int << 16
    suit = suit_int << 12
    rank = rank_int << 8

    return bitrank | suit | rank | rank_prime

def int_to_str(card_int):
    rank_int = get_rank_int(card_int)
    suit_int = get_suit_int(card_int)
    return STR_RANKS[rank_int] + INT_SUIT_TO_CHAR_SUIT[suit_int]

def get_rank_int(card_int):
    return (card_int >> 8) & 0xF

def get_suit_int(card_int):
    return (card_int >> 12) & 0xF

def get_bitrank_int(card_int):
    return (card_int >> 16) & 0x1FFF

def get_prime(card_int):
    return card_int & 0x3F

def hand_to_binary(card_strs):
    """
    Expects a list of cards as strings and returns a list
    of integers of same length corresponding to those strings. 
    """
    bhand = []
    for c in card_strs:
        bhand.append(new(c))
    return bhand

def prime_product_from_hand(card_ints):
    """
    Expects a list of cards in integer form. 
    """

    product = 1
    for c in card_ints:
        product *= (c & 0xFF)

    return product

def prime_product_from_rankbits(rankbits):
    """
    Returns the prime product using the bitrank (b)
    bits of the hand. Each 1 in the sequence is converted
    to the correct prime and multiplied in.
    Params:
        rankbits = a single 32-bit (only 13-bits set) integer representing 
                the ranks of 5 _different_ ranked cards 
                (5 of 13 bits are set)
    Primarily used for evaulating flushes and straights, 
    two occasions where we know the ranks are *ALL* different.
    Assumes that the input is in form (set bits):
                            rankbits     
                    +--------+--------+
                    |xxxbbbbb|bbbbbbbb|
                    +--------+--------+
    """
    product = 1
    for i in INT_RANKS:
        # if the ith bit is set
        if rankbits & (1 << i):
            product *= PRIMES[i]

    return product

def int_to_binary(card_int):
    """
    For debugging purposes. Displays the binary number as a 
    human readable string in groups of four digits. 
    """
    bstr = bin(card_int)[2:][::-1]  # chop off the 0b and THEN reverse string
    output = list("".join(["0000" + "\t"] * 7) + "0000")

    for i in range(len(bstr)):
        output[i + int(i/4)] = bstr[i]

    # output the string to console
    output.reverse()
    return "".join(output)


@export
def evaluate_cards(cards: list) -> int:
    """
    Performs an evalution given cards in integer form, mapping them to
    a rank in the range [1, 7462], with lower ranks being more powerful.
    Variant of Cactus Kev's 5 card evaluator, though I saved a lot of memory
    space using a hash table and condensing some of the calculations. 
    """
    flushes()
    multiples()

    # if flush
    if cards[0] & cards[1] & cards[2] & cards[3] & cards[4] & 0xF000:
        handOR = (cards[0] | cards[1] | cards[2] | cards[3] | cards[4]) >> 16
        prime = prime_product_from_rankbits(handOR)
        return flush_lookup[prime]

    # otherwise
    else:
        prime = prime_product_from_hand(cards)
        return unsuited_lookup[prime]