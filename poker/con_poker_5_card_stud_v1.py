import con_rsa_encryption as rsa
import con_5_card_hand_evaluator as he
import con_phi_lst001 as phi

phi_balances = ForeignHash(foreign_contract='con_phi_lst001', foreign_name='balances')
player_metadata = ForeignHash(foreign_contract='con_gamma_phi_profile_v1', foreign_name='metadata')

games = Hash(default_value=None)
hands = Hash(default_value=None)
players_games = Hash(default_value=[])
owner = Variable()

MAX_PLAYERS = 8
CARDS_PER_HAND = 5
MAX_RANDOM_NUMBER = 99999999
DECK = [
    '2c', '2d', '2h', '2s',
    '3c', '3d', '3h', '3s',
    '4c', '4d', '4h', '4s',
    '5c', '5d', '5h', '5s',
    '6c', '6d', '6h', '6s',
    '7c', '7d', '7h', '7s',
    '8c', '8d', '8h', '8s',
    '9c', '9d', '9h', '9s',
    'Tc', 'Td', 'Th', 'Ts',
    'Jc', 'Jd', 'Jh', 'Js',
    'Qc', 'Qd', 'Qh', 'Qs',
    'Kc', 'Kd', 'Kh', 'Ks',
    'Ac', 'Ad', 'Ah', 'As',
]


random.seed()


@construct
def seed():
    owner.set(ctx.caller)


def get_players_and_assert_exists(game_id: str) -> dict:
    players = games[game_id, 'players']
    assert players is not None, f'Game {game_id} does not exist.'
    return players


def create_game_id(creator: str) -> str:
    return hashlib.sha3(":".join([creator, str(now)]))


def create_hand_id(game_id: str) -> str:
    return hashlib.sha3(":".join([game_id, str(now)]))


@export
def add_chips_to_game(game_id: str, amount: float):
    player = ctx.caller
    assert amount > 0, 'Amount must be a positive number'
    
    players = get_players_and_assert_exists(game_id)
    assert player in players, 'You do not belong to this game.'

    games[game_id, player] = (games[game_id, player] or 0.0) + amount
    assert phi_balances[player, ctx.this] >= amount, 'You have not approved enough for this amount of chips'
    phi.transfer_from(amount, ctx.this, player)


@export
def withdraw_chips_from_game(game_id: str, amount: float):
    player = ctx.caller
    assert amount > 0, 'Amount must be a positive number'

    players = get_players_and_assert_exists(game_id)
    assert player in players, 'You do not belong to this game.'
    
    current_chip_count = games[game_id, player]
    
    assert current_chip_count >= amount, 'You cannot withdraw more than you have.'

    games[game_id, player] = current_chip_count - amount
    phi.transfer(
        amount=amount,
        to=player
    )


@export
def start_game(other_players: list, ante: float) -> str:
    creator = ctx.caller
    
    assert ante >= 0, 'Ante must be non-negative.'
    assert creator not in other_players, f'Caller can\'t be in other_players input.'
    assert other_players is not None and len(other_players) > 0, 'You cannot play by yourself!'
    assert len(other_players) < MAX_PLAYERS, f'Only {MAX_PLAYERS} are allowed to play at the same time.'

    game_id = create_game_id(creator=creator)

    assert games[game_id, 'creator'] is None, f'Game {game_id} has already been created.'

    games[game_id, 'players'] = [creator, *other_players]
    games[game_id, 'ante'] = ante
    games[game_id, 'creator'] = creator
    
    players_games[creator] = players_games[creator] + [game_id]

    for player in other_players:
        players_games[player] = players_games[player] + [game_id]

    return game_id


@export
def start_hand(game_id: str) -> str:
    dealer = ctx.caller

    players = games[game_id, 'players']

    assert players is not None, 'This game does not exist.'
    
    # Check which players still have money
    ante = games[game_id, 'ante']
    active_players = [player for player in players if (games[game_id, player] or -1) >= ante]

    assert dealer in players, 'You are not a part of this game.'
    assert dealer in active_players, 'You do not have enough chips to be in this hand.'

    previous_hand_id = games[game_id, 'current_hand']
    if previous_hand_id is not None:
        assert hands[previous_hand_id, 'payed_out'], 'The previous hand has not been payed out yet.'

    hand_id = create_game_id(game_id)

    # Set current hand
    games[game_id, 'current_hand'] = hand_id

    total_cards_to_draw = len(players) * CARDS_PER_HAND

    cards = random.choices(DECK, total_cards_to_draw)

    for i in range(len(active_players)):
        player = active_players[i]
        player_key = player_metadata[player, 'public_rsa_key']
        assert player_key is not None, f'Player {player} has not setup their encryption keys.'
        player_hand = cards[i*CARDS_PER_HAND: i*CARDS_PER_HAND+CARDS_PER_HAND]
        
        player_hand_str = ",".join(player_hand)
        salt = str(random.randint(0, MAX_RANDOM_NUMBER))

        player_hand_str_with_salt = f'{player_hand_str}:{salt}'
        
        # Encrypt players hand with their personal keys
        player_encrypted_hand = rsa.encrypt(
            message_str=player_hand_str_with_salt,
            n=player_key[0],
            e=player_key[1]    
        )
        
        # For verification purposes
        house_encrypted_hand = hashlib.sha3(player_hand_str_with_salt)

        hands[hand_id, player, 'player_encrypted_hand'] = player_encrypted_hand
        hands[hand_id, player, 'house_encrypted_hand'] = house_encrypted_hand

        # Pay ante
        hands[hand_id, player, 'bet'] = ante
        games[game_id, player] -= ante

    hands[hand_id, 'game_id'] = game_id
    hands[hand_id, 'active_players'] = active_players
    hands[hand_id, 'dealer'] = dealer
    hands[hand_id, 'folded'] = []
    hands[hand_id, 'next_better'] = get_next_better(players, [], dealer)
    hands[hand_id, 'completed'] = False
    hands[hand_id, 'payed_out'] = False
    hands[hand_id, 'reached_dealer'] = False
    hands[hand_id, 'current_bet'] = ante
    hands[hand_id, 'pot'] = ante * len(active_players)

    return hand_id


def get_next_better(players: list, folded: list, current_better: str) -> str:
    if len(folded) >= len(players) - 1:
        return None # No one needs to bet
    
    non_folded_players = [p for p in players if p not in folded]
    current_index = non_folded_players.index(current_better)    
    assert current_index >= 0, 'Current better has folded, which does not make sense.'
    return non_folded_players[(current_index + 1) % len(non_folded_players)]


@export
def bet_check_or_fold(hand_id: str, bet: float):
    player = ctx.caller
    
    assert hands[hand_id, player, 'player_encrypted_hand'] is not None, 'Hand does not exist'
    assert not hands[hand_id, 'completed'], 'This hand has already completed.'
    assert hands[hand_id, 'next_better'] == player, 'It is not your turn to bet.'

    players = hands[hand_id, 'active_players']
    folded = hands[hand_id, 'folded']

    call_bet = hands[hand_id, 'current_bet'] or 0.0
    player_previous_bet  = hands[hand_id, player, 'bet'] or 0.0
    dealer = hands[hand_id, 'dealer']
    if dealer == player:
        # Been around the circle once
        hands[hand_id, 'reached_dealer'] = True

    next_better = get_next_better(players, folded, player)
    if next_better is None:
        # No need to bet, this is the end of the hand
        hands[hand_id, 'completed'] = True

    else:
        if bet < 0:
            # Folding
            folded.append(player)
            hands[hand_id, 'folded'] = folded
            if len(folded) == len(players) - 1:
                hands[hand_id, 'completed'] = True
        elif bet == 0:
            # Checking
            assert player_previous_bet >= call_bet, 'Cannot check in this scenario. Current bet is above your bet.'
            next_players_bet = hands[hand_id, next_better, 'bet']
            if next_players_bet is not None and next_players_bet == call_bet and hands[hand_id, 'reached_dealer']:
                # Betting is over (TODO allow reraise)
                hands[hand_id, 'completed'] = True
        else:
            # Betting
            game_id = hands[hand_id, 'game_id']
            assert games[game_id, player] >= bet, 'You do not have enough chips to make this bet'
            current_bet = player_previous_bet + bet
            assert current_bet >= call_bet, 'Current bet is above your bet.'            
            hands[hand_id, player, 'bet'] = current_bet
            hands[hand_id, 'current_bet'] = current_bet
            hands[hand_id, 'pot'] += bet
            games[game_id, player] -= bet
            #next_players_bet = hands[hand_id, next_better, 'bet']
            #if next_players_bet is not None and next_players_bet == current_bet:
            #    # Betting is over (TODO allow reraise)
            #    hands[hand_id, 'completed'] = True
        
    hands[hand_id, 'next_better'] = next_better


@export
def verify_hand(hand_id: str, player_hand_str: str):
    # TODO allow user to not verify onchain to hide bluffs

    player = ctx.caller
    assert hands[hand_id, 'completed'], 'This hand has not completed yet.'
    folded = hands[hand_id, 'folded']
    assert player not in folded, 'No need to verify your hand because you folded.'
    players = hands[hand_id, 'active_players']
    assert player in players, 'You are not an active player in this hand.'

    # Check if player has bet enough
    bet_should_equal = hands[hand_id, 'current_bet']
    assert bet_should_equal is not None, 'There is no current bet.'

    player_bet = hands[hand_id, player, 'bet']
    assert player_bet is not None, 'You have not bet yet.'

    assert bet_should_equal == player_bet, 'Bets have not stabilized.'

    # For verification purposes
    house_encrypted_hand = hashlib.sha3(player_hand_str)

    previous_house_encrypted_hand = hands[hand_id, player, 'house_encrypted_hand']

    verified = previous_house_encrypted_hand is not None and \
        previous_house_encrypted_hand == house_encrypted_hand

    if not verified:
        # BAD ACTOR NEEDS TO BE PUNISHED
        folded.append(player)
        hands[hand_id, 'folded'] = folded

    assert verified, 'You cheated. Your hand has been forfeited.'

    cards = player_hand_str.split(':')[0].split(',')
    rank = he.evaluate_cards(cards=cards)

    hands[hand_id, player, 'rank'] = rank
    hands[hand_id, player, 'hand'] = cards
    

@export
def payout_hand(hand_id: str):
    pot = hands[hand_id, 'pot']
    assert pot > 0, 'There is no pot to claim!'
    assert not hands[hand_id, 'payed_out'], 'This hand has already been payed out.'
    
    folded = hands[hand_id, 'folded']
    players = hands[hand_id, 'active_players']
    game_id = hands[hand_id, 'game_id']

    remaining = [p for p in players if p not in folded]
    assert len(remaining) > 0, 'There are no remaining players.'

    if len(remaining) == 1:
        # Just pay out, everyone else folded
        winners = remaining

    else:
        ranks = {}
        best_rank = None
        for p in remaining:
            rank = hands[hand_id, p, 'rank']
            assert rank is not None, f'Player {p} has not verified their hand yet.'
            if rank not in ranks:
                ranks[rank] = []
            ranks[rank] = [p]
            if best_rank is None:
                best_rank = rank
            else:
                best_rank = min(best_rank, rank)

        # Handle pot splitting
        winners = ranks[best_rank]
    payout = pot / len(winners)

    for p in winners:
        games[game_id, p] += payout

    hands[hand_id, 'winners'] = winners
    hands[hand_id, 'payed_out'] = True


@export
def emergency_withdraw(amount: float):
    assert ctx.caller == owner.get(), 'Only the owner can call emergency_withdraw()'
    phi.transfer(
        amount=amount,
        to=ctx.caller
    )