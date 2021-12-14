# con_poker_card_games_v2
import con_rsa_encryption as rsa
import con_phi_lst001 as phi
I = importlib

phi_balances = ForeignHash(foreign_contract='con_phi_lst001', foreign_name='balances')

games = Hash(default_value=None)
hands = Hash(default_value=None)
game_names = Hash(default_value=None)
players_games = Hash(default_value=[])
players_invites = Hash(default_value=[])
messages_hash = Hash(default_value=[])
player_metadata_contract = Variable()
poker_hand_evaluator_contract = Variable()
owner = Variable()

MAX_RANDOM_NUMBER = 99999999
ONE_CARD_POKER = 0
BLIND_POKER = 1
STUD_POKER = 2
ALL_GAME_TYPES = [
    ONE_CARD_POKER,
    BLIND_POKER,
    STUD_POKER
]
NO_LIMIT = 0
POT_LIMIT = 1
ALL_BETTING_TYPES = [
    NO_LIMIT,
    POT_LIMIT
]

random.seed()

@construct
def seed():
    owner.set(ctx.caller)
    player_metadata_contract.set('con_gamma_phi_profile_v4')
    poker_hand_evaluator_contract.set('con_poker_hand_evaluator_v1')

@export
def update_player_metadata_contract(contract: str):
    assert ctx.caller == owner.get(), 'Only the owner can call update_player_metadata_contract()'
    player_metadata_contract.set(contract)

@export
def update_poker_hand_evaluator_contract(contract: str):
    assert ctx.caller == owner.get(), 'Only the owner can call update_player_metadata_contract()'
    poker_hand_evaluator_contract.set(contract)

def get_players_and_assert_exists(game_id: str) -> dict:
    players = games[game_id, 'players']
    assert players is not None, f'Game {game_id} does not exist.'
    return players

def create_game_id(name: str) -> str:
    return hashlib.sha3(":".join([name, str(now)]))

def create_hand_id(game_id: str) -> str:
    return hashlib.sha3(":".join([game_id, str(now)]))

def evaluate_hand(hand: list) -> int:
    phe = I.import_module(poker_hand_evaluator_contract.get())
    return phe.evaluate(hand)

@export
def game_message(game_id: str, message: str):
    player = ctx.caller
    players = get_players_and_assert_exists(game_id)
    assert player in players, 'You do not belong to this game.'
    messages = messages_hash[game_id, player] or []
    messages.append(message)
    messages_hash[game_id, player] = messages

@export
def hand_message(hand_id: str, message: str):
    player = ctx.caller
    active_players = hands[hand_id, 'active_players']
    assert player in active_players, 'You do not belong to this hand.'
    messages = messages_hash[hand_id, player] or []
    messages.append(message)
    messages_hash[hand_id, player] = messages

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
def respond_to_invite(game_id: str, accept: bool):
    player = ctx.caller
    player_invites = players_invites[player] or []
    players = get_players_and_assert_exists(game_id)
    assert player not in players, 'You are already a part of this game.'
    declined = players_invites[player, 'declined'] or []
    assert game_id in player_invites or game_id in declined or games[game_id, 'public'], 'You have not been invited to this game.'
    if game_id in player_invites:
        player_invites.remove(game_id)
        players_invites[player] = player_invites
    players_invites[player, game_id] = accept
    if accept:
        if game_id in declined:
            declined.remove(game_id)
            players_invites[player, 'declined'] = declined
        players.append(player)
        games[game_id, 'players'] = players
        players_games[player] = (players_games[player] or []) + [game_id]
    else:
        if game_id not in declined:
            declined.append(game_id)
            players_invites[player, 'declined'] = declined

@export
def decline_all_invites():
    # Nuclear option
    player = ctx.caller
    invites = players_invites[player] or []
    for invite in invites:
        players_invites[player, invite] = False
    players_invites[player] = []
    
def send_invite_requests(game_id: str, others: list):
    for other in others:
        player_invites = players_invites[other] or []
        player_invites.append(game_id)
        players_invites[other] = player_invites

def validate_game_name(name: str):
    assert name is not None and len(name) > 0, 'Game name cannot be null or empty'
    assert isinstance(name, str), 'Game name must be a string.'
    assert len(name) <= 36, 'Game name cannot be longer than 36 characters.'
    assert all([c.isalnum() or c in ('_', '-') for c in name]), 'Game name has invalid characters. Each character must be alphanumeric, a hyphen, or an underscore.'
    assert name[0] not in ('-', '_') and name[-1] not in ('-', '_'), 'Game name cannot start or end with a hyphen or underscore.'
    
@export
def start_game(name: str, 
               other_players: list, 
               ante: float,
               game_type: int,
               bet_type: int,
               n_cards_total: int = None,
               n_hole_cards: int = None,
               public: bool = False) -> str:

    creator = ctx.caller
    
    assert game_type in ALL_GAME_TYPES, f'Invalid game type: {game_type}.'
    assert bet_type in ALL_BETTING_TYPES, f'Invalid betting type: {bet_type}.'
    if game_type == STUD_POKER:
        assert n_cards_total is not None, 'Must specify n_cards_total for stud poker.'
        assert n_hole_cards is not None, 'Must specify n_hole_cards for stud poker.'
        assert n_cards_total == 5 or n_cards_total == 7, 'n_cards_total must equal 5 or 7.'
        assert n_hole_cards > 0, 'n_hole_cards must be positive.'
        assert n_hole_cards <= n_cards_total, 'n_hole_cards must be less than or equal to n_cards_total.'        

    assert ante >= 0, 'Ante must be non-negative.'
    assert creator not in other_players, f'Caller can\'t be in other_players input.'

    game_id = create_game_id(name=name)

    assert games[game_id, 'creator'] is None, f'Game {game_id} has already been created.'

    validate_game_name(name)
    assert game_names[name] is None, f'Game {name} has already been created.'
    game_names[name] = game_id

    games[game_id, 'players'] = [creator]
    games[game_id, 'ante'] = ante
    games[game_id, 'creator'] = creator
    games[game_id, 'invitees'] = other_players
    games[game_id, 'public'] = public
    games[game_id, 'game_type'] = game_type
    games[game_id, 'bet_type'] = bet_type
    if game_type == STUD_POKER:
        games[game_id, 'n_cards_total'] = n_cards_total
        games[game_id, 'n_hole_cards'] = n_hole_cards

    players_games[creator] = (players_games[creator] or []) + [game_id]
    send_invite_requests(game_id, other_players)

    return game_id

@export
def add_player_to_game(game_id: str, player_to_add: str):
    player = ctx.caller
    assert player != player_to_add, 'You cannot add yourself to a game.'
    creator = games[game_id, 'creator']
    assert player == creator, 'Only the game creator can add players.'
    players = get_players_and_assert_exists(game_id)
    assert player_to_add not in players, 'Player is already in the game.'
    invitees = games[game_id, 'invitees']
    assert player_to_add not in invitees, 'Player has already been invited.'
    invitees.append(player_to_add)
    games[game_id, 'invitees'] = invitees
    send_invite_requests(game_id, [player_to_add])

@export
def leave_game(game_id: str):
    player = ctx.caller
    players = get_players_and_assert_exists(game_id)
    assert player in players, 'You are not in this game.'

    chips = games[game_id, player]
    assert chips is None or chips == 0, 'You still have chips in this game. Please withdraw them before leaving.'

    player_games = players_games[player]
    player_games.remove(game_id)
    players_games[player] = player_games
    players.remove(player)
    games[game_id, 'players'] = players

    hand_id = games[game_id, 'current_hand']

    if hand_id is not None:
        active_players = hands[hand_id, 'active_players'] or []
        if player in active_players:
            folded = hands[hand_id, 'folded']
            all_in = hands[hand_id, 'all_in']
            next_better = hands[hand_id, 'next_better']
            if next_better == player:
                next_better = get_next_better(active_players, folded, all_in, player)
                hands[hand_id, 'next_better'] = next_better
            active_players.remove(player)
            hands[hand_id, 'active_players'] = active_players
            if player in folded:
                folded.remove(player)
                hands[hand_id, 'folded'] = folded
            if player in all_in:
                all_in.remove(player)
                hands[hand_id, 'all_in'] = all_in

@export
def start_hand(game_id: str) -> str:
    dealer = ctx.caller
    
    players = get_players_and_assert_exists(game_id)    
    assert dealer in players, 'You are not a part of this game.'
    assert len(players) > 1, 'You cannot start a hand by yourself.'

    previous_hand_id = games[game_id, 'current_hand']
    if previous_hand_id is not None:
        assert hands[previous_hand_id, 'payed_out'], 'The previous hand has not been payed out yet.'

    hand_id = create_game_id(name=game_id)
    # Update game state
    games[game_id, 'current_hand'] = hand_id
    # Update hand state
    hands[hand_id, 'game_id'] = game_id
    hands[hand_id, 'dealer'] = dealer
    hands[hand_id, 'folded'] = []
    hands[hand_id, 'completed'] = False
    hands[hand_id, 'payed_out'] = False
    hands[hand_id, 'reached_dealer'] = False
    hands[hand_id, 'active_players'] = []
    hands[hand_id, 'current_bet'] = 0
    hands[hand_id, 'pot'] = 0
    hands[hand_id, 'all_in'] = []
    return hand_id

def active_player_sort(players: list) -> int:
    def sort(player):
        return players.index(player)
    return sort

@export
def ante_up(hand_id: str):
    player = ctx.caller
    game_id = hands[hand_id, 'game_id']
    assert game_id is not None, 'This game does not exist.'
    players = get_players_and_assert_exists(game_id)    
    assert player in players, 'You are not a part of this game.'
    ante = games[game_id, 'ante']
    chips = games[game_id, player]
    assert chips is not None and chips >= ante, 'You do not have enough chips.'
    active_players = hands[hand_id, 'active_players'] or []
    assert player not in active_players, 'You have already paid the ante.'
    game_type = games[game_id, 'game_type']
    if game_type == STUD_POKER:
        max_players = 52 // games[game_id, 'n_cards_total']
    else:
        max_players = 50
    assert len(active_players) < max_players, f'A maximum of {max_players} is allowed for this game type.'
    # Pay ante
    hands[hand_id, player, 'bet'] = ante
    hands[hand_id, player, 'max_bet'] = chips
    games[game_id, player] -= ante
    # Update hand state
    active_players.append(player)
    active_players.sort(key=active_player_sort(players))
    hands[hand_id, 'active_players'] = active_players
    hands[hand_id, 'current_bet'] = ante
    hands[hand_id, 'pot'] += ante
    if chips == ante:
        # All in
        all_in = hands[hand_id, 'all_in']
        all_in.append(player)
        hands[hand_id, 'all_in'] = all_in

@export
def deal_cards(hand_id: str):
    dealer = ctx.caller

    active_players = hands[hand_id, 'active_players']

    assert dealer == hands[hand_id, 'dealer'], 'You are not the dealer.'
    assert len(active_players) > 1, f'Not enough active players: {len(active_players)} <= 1'
    assert dealer in active_players, 'You are not actively part of this hand.'

    game_id = hands[hand_id, 'game_id']
    game_type = games[game_id, 'game_type']

    player_metadata = ForeignHash(foreign_contract=player_metadata_contract.get(), foreign_name='metadata')

    cards = [
        '2c', '2d', '2h', '2s', '3c', '3d', '3h', '3s', '4c', '4d', '4h', '4s',
        '5c', '5d', '5h', '5s', '6c', '6d', '6h', '6s', '7c', '7d', '7h', '7s',
        '8c', '8d', '8h', '8s', '9c', '9d', '9h', '9s', 'Tc', 'Td', 'Th', 'Ts',
        'Jc', 'Jd', 'Jh', 'Js', 'Qc', 'Qd', 'Qh', 'Qs', 'Kc', 'Kd', 'Kh', 'Ks',
        'Ac', 'Ad', 'Ah', 'As',
    ]
    random.shuffle(cards)

    n_cards_total = games[game_id, 'n_cards_total']
    n_hole_cards = games[game_id, 'n_hole_cards']

    for i in range(len(active_players)):
        player = active_players[i]
        player_key = player_metadata[player, 'public_rsa_key']
        assert player_key is not None, f'Player {player} has not setup their encryption keys.'
        keys = player_key.split('|')
        assert len(keys) == 2, 'Invalid keys'

        if game_type == ONE_CARD_POKER:
            player_hand = cards[i: i+1]
        elif game_type == BLIND_POKER:
            # Player's hand is actually everyone elses hand
            player_hand = cards[0:i] + cards[i+1:len(active_players)]
            assert len(player_hand) == len(active_players)-1, f'Something went wrong. {len(player_hand)} != {len(active_players)-1}'
        elif game_type == STUD_POKER:
            player_hand = cards[n_cards_total*i:n_cards_total*i+n_cards_total]            
            assert len(player_hand) == n_cards_total, 'Something went wrong.'
        else:
            assert False, 'Invalid game type.'

        player_hand_str = ",".join(player_hand)

        if n_hole_cards is not None and n_hole_cards < n_cards_total:
            public_hand_str = ",".join(player_hand[n_hole_cards:])
        else:
            public_hand_str = None

        salt = str(random.randint(0, MAX_RANDOM_NUMBER))

        player_hand_str_with_salt = f'{player_hand_str}:{salt}'
        
        # Encrypt players hand with their personal keys
        player_encrypted_hand = rsa.encrypt(
            message_str=player_hand_str_with_salt,
            n=int(keys[0]),
            e=int(keys[1])    
        )
        
        # For verification purposes
        house_encrypted_hand = hashlib.sha3(player_hand_str_with_salt)

        if public_hand_str is not None:
            hands[hand_id, player, 'public_hand'] = public_hand_str
        hands[hand_id, player, 'player_encrypted_hand'] = player_encrypted_hand
        hands[hand_id, player, 'house_encrypted_hand'] = house_encrypted_hand

    # Update hand state
    all_in = hands[hand_id, 'all_in']
    hands[hand_id, 'next_better'] = get_next_better(active_players, [], all_in, dealer)

def get_next_better(players: list, folded: list, all_in: list, current_better: str) -> str:
    if len(folded) >= len(players) - 1:
        return None # No one needs to bet, only one player left in the hand
    if len(players) == len(all_in):
        return None # No one needs to bet, everyone is all in
    non_folded_players = [p for p in players if p not in folded and p not in all_in]
    current_index = non_folded_players.index(current_better)    
    assert current_index >= 0, 'Current better has folded, which does not make sense.'
    return non_folded_players[(current_index + 1) % len(non_folded_players)]

@export
def bet_check_or_fold(hand_id: str, bet: float):
    player = ctx.caller
    
    assert hands[hand_id, player, 'player_encrypted_hand'] is not None, 'Hand does not exist'
    assert not hands[hand_id, 'completed'], 'This hand has already completed.'
    assert hands[hand_id, 'next_better'] == player, 'It is not your turn to bet.'

    active_players = hands[hand_id, 'active_players']
    folded = hands[hand_id, 'folded']

    call_bet = hands[hand_id, 'current_bet'] or 0.0
    player_previous_bet  = hands[hand_id, player, 'bet'] or 0.0
    dealer = hands[hand_id, 'dealer']

    if dealer == player:
        # Been around the circle once
        hands[hand_id, 'reached_dealer'] = True
        reached_dealer = True
    else:
        reached_dealer = hands[hand_id, 'reached_dealer']

    all_in = hands[hand_id, 'all_in']
    next_better = get_next_better(active_players, folded, all_in, player)

    if next_better is None:
        # No need to bet, this is the end of the hand
        hands[hand_id, 'completed'] = True

    else:
        if bet < 0:
            # Folding
            folded.append(player)
            hands[hand_id, 'folded'] = folded
            if player in all_in:
                all_in.remove(player)
                hands[hand_id, 'all_in'] = all_in
            if len(folded) == len(active_players) - 1:
                hands[hand_id, 'completed'] = True
        elif bet == 0:
            # Checking
            max_bet = hands[hand_id, player, 'max_bet']
            if max_bet == player_previous_bet and player not in all_in:
                all_in.append(player)
                hands[hand_id, 'all_in'] = all_in
            assert max_bet == player_previous_bet or player_previous_bet >= call_bet, 'Cannot check in this scenario. Current bet is above your bet and you are not all in.'
            next_players_bet = hands[hand_id, next_better, 'bet']
            if next_players_bet is not None and next_players_bet == call_bet and reached_dealer:
                # Betting is over (TODO allow reraise)
                hands[hand_id, 'completed'] = True
        else:
            # Betting
            game_id = hands[hand_id, 'game_id']
            assert games[game_id, player] >= bet, 'You do not have enough chips to make this bet'
            bet_type = games[game_id, 'bet_type']
            if bet_type == POT_LIMIT:
                pot = hands[hand_id, 'pot']
                assert bet <= pot, f'Cannot overbet the pot in pot-limit mode.'
            current_bet = player_previous_bet + bet
            max_bet = hands[hand_id, player, 'max_bet']
            if max_bet == current_bet and player not in all_in:
                all_in.append(player)
                hands[hand_id, 'all_in'] = all_in
            assert max_bet == current_bet or current_bet >= call_bet, 'Current bet is above your bet and you did not go all in.'            
            hands[hand_id, player, 'bet'] = current_bet
            hands[hand_id, 'current_bet'] = current_bet
            hands[hand_id, 'pot'] += bet
            games[game_id, player] -= bet
        
    hands[hand_id, 'next_better'] = next_better

@export
def verify_hand(hand_id: str, player_hand_str: str) -> str:
    player = ctx.caller
    assert hands[hand_id, 'completed'], 'This hand has not completed yet.'
    folded = hands[hand_id, 'folded']
    assert player not in folded, 'No need to verify your hand because you folded.'
    active_players = hands[hand_id, 'active_players']
    assert player in active_players, 'You are not an active player in this hand.'

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

        return 'Verification failed. Your hand has been forfeited.'

    else:
        cards = player_hand_str.split(':')[0].split(',')

        game_id = hands[hand_id, 'game_id']
        game_type = games[game_id, 'game_type']

        if game_type == BLIND_POKER:
            j = 0
            for p in active_players:
                if p != player:
                    if p not in folded:
                        card = cards[j]
                        rank = evaluate_hand([card])
                        if hands[hand_id, p, 'rank'] is None:
                            hands[hand_id, p, 'rank'] = rank
                            hands[hand_id, p, 'hand'] = card
                    j += 1
        else:
            rank = evaluate_hand(cards)
            hands[hand_id, player, 'rank'] = rank
            hands[hand_id, player, 'hand'] = cards

        return 'Verification succeeded.'

def find_winners(ranks: dict, players: list) -> list:
    sorted_rank_values = sorted(ranks.keys(), reverse=True)
    player_set = set(players)
    for rank in sorted_rank_values:
        players_with_rank = ranks[rank]
        intersection = player_set.intersection(set(players_with_rank))
        if len(intersection) > 0:
            # Found players
            winners = list(intersection)
            break
    return winners

def calculate_ranks(hand_id: str, players: list) -> dict:
    ranks = {}
    for p in players:
        rank = hands[hand_id, p, 'rank']
        assert rank is not None, f'Player {p} has not verified their hand yet.'
        if rank not in ranks:
            ranks[rank] = []
        ranks[rank].append(p)
    return ranks

@export
def payout_hand(hand_id: str):
    pot = hands[hand_id, 'pot']
    assert pot > 0, 'There is no pot to claim!'
    assert not hands[hand_id, 'payed_out'], 'This hand has already been payed out.'
    
    folded = hands[hand_id, 'folded']
    all_in = hands[hand_id, 'all_in']
    active_players = hands[hand_id, 'active_players']

    remaining = [p for p in active_players if p not in folded]
    assert len(remaining) > 0, 'There are no remaining players.'

    payouts = {}

    if len(remaining) == 1:
        # Just pay out, everyone else folded
        payouts[remaining[0]] = pot
    else:
        ranks = calculate_ranks(hand_id, remaining)
        if len(all_in) > 0:
            # Need to calculate split pots
            all_in_map = {}
            for player in all_in:
                # Check all in amount
                amount = hands[hand_id, player, 'max_bet']
                all_in_map[player] = amount
            pots = sorted(set(all_in_map.values()))
            total_payed_out = 0
            for bet in pots:
                players_in_pot = []
                for player in remaining:
                    if player not in all_in_map or all_in_map[player] >= bet:
                        players_in_pot.append(player)
                        pot_winners = find_winners(ranks, players_in_pot)
                        pot_payout = bet * len(players_in_pot)
                        total_payed_out += pot_payout
                        payout = pot_payout / len(pot_winners)
                        for winner in pot_winners:
                            if winner not in payouts:
                                payouts[winner] = 0
                            payouts[winner] += payout                            
            remaining_to_payout = pot - total_payed_out
            not_all_in = set(remaining).difference(set(all_in))
            assert remaining_to_payout == 0 or len(not_all_in) > 0, 'Invalid state when calculating side pots.'
            if remaining_to_payout > 0:
                if len(not_all_in) == 1:
                    winners = not_all_in
                else:
                    winners = find_winners(ranks, not_all_in)
                payout = remaining_to_payout / len(winners)
                for winner in winners:
                    if winner not in payouts:
                        payouts[winner] = 0
                    payouts[winner] += payout
        else:
            winners = find_winners(ranks, remaining)
            payout = pot / len(winners)
            for winner in winners:
                payouts[winner] = payout

    game_id = hands[hand_id, 'game_id']
    for player, payout in payouts.items():
        games[game_id, player] += payout

    hands[hand_id, 'winners'] = list(payouts.keys())
    hands[hand_id, 'payed_out'] = True

@export
def emergency_withdraw(amount: float):
    assert ctx.caller == owner.get(), 'Only the owner can call emergency_withdraw()'
    phi.transfer(
        amount=amount,
        to=ctx.caller
    )

@export
def change_ownership(new_owner: str):
    assert ctx.caller == owner.get(), 'Only the owner can change ownership!'

    owner.set(new_owner)