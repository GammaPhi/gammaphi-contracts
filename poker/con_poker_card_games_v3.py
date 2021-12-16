# con_poker_card_games_v3
import con_rsa_encryption as rsa
import con_otp_v1 as otp
import con_phi_lst001 as phi
I = importlib

phi_balances = ForeignHash(foreign_contract='con_phi_lst001', foreign_name='balances')

games = Hash(default_value=None)
hands = Hash(default_value=None)
game_names = Hash(default_value=None)
players_games = Hash(default_value=[])
players_invites = Hash(default_value=[])
player_metadata_contract = Variable()
hand_evaluator_contract = Variable()
owner = Variable()

MAX_RANDOM_NUMBER = 99999999
ONE_CARD_POKER = 0
BLIND_POKER = 1
STUD_POKER = 2
HOLDEM_POKER = 3
OMAHA_POKER = 4
ALL_GAME_TYPES = [ONE_CARD_POKER, BLIND_POKER, STUD_POKER, HOLDEM_POKER, OMAHA_POKER]
NO_LIMIT = 0
POT_LIMIT = 1
ALL_BETTING_TYPES = [NO_LIMIT, POT_LIMIT]
FLOP = 1
TURN = 2
RIVER = 3

random.seed()

@construct
def seed():
    owner.set(ctx.caller)
    player_metadata_contract.set('con_gamma_phi_profile_v4')
    hand_evaluator_contract.set('con_hand_evaluator_v1')

@export
def update_player_metadata_contract(contract: str):
    assert ctx.caller == owner.get(), 'Only the owner can call update_player_metadata_contract()'
    player_metadata_contract.set(contract)

@export
def update_poker_hand_evaluator_contract(contract: str):
    assert ctx.caller == owner.get(), 'Only the owner can call update_player_metadata_contract()'
    hand_evaluator_contract.set(contract)

def get_players_and_assert_exists(game_id: str) -> dict:
    players = games[game_id, 'players']
    assert players is not None, f'Game {game_id} does not exist.'
    return players

def create_game_id(name: str) -> str:
    return hashlib.sha3(":".join([name, str(now)]))

def create_hand_id(game_id: str) -> str:
    return hashlib.sha3(":".join([game_id, str(now)]))

def get_hand_evaluator():
    return I.import_module(hand_evaluator_contract.get())

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
    games[game_id, 'name'] = name
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
                evaluator = get_hand_evaluator()
                next_better = evaluator.get_next_better(active_players, folded, all_in, player)
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
    elif game_type == HOLDEM_POKER:
        max_players = 10
    elif game_type == OMAHA_POKER:
        max_players = 10
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

    evaluator = get_hand_evaluator()
    cards = evaluator.get_deck()

    n_cards_total = games[game_id, 'n_cards_total']
    n_hole_cards = games[game_id, 'n_hole_cards']

    if game_type == HOLDEM_POKER or game_type == OMAHA_POKER:
        community_cards = [",".join(cards[0:3]), cards[3], cards[4]]
    else:
        community_cards = None

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
        elif game_type == HOLDEM_POKER:
            player_hand = cards[5+2*i:5+2*i+2]
        elif game_type == OMAHA_POKER:
            player_hand = cards[5+4*i:5+4*i+4]
        else:
            assert False, 'Invalid game type.'

        player_hand_str = ",".join(player_hand)

        if n_hole_cards is not None and n_hole_cards < n_cards_total:
            public_hand_str = ",".join(player_hand[n_hole_cards:])
        else:
            public_hand_str = None

        salt = str(random.randint(0, MAX_RANDOM_NUMBER))

        if community_cards is not None:
            pad1 = otp.generate_otp(80)
            pad2 = otp.generate_otp(20)
            pad3 = otp.generate_otp(20)
            salt1 = str(random.randint(0, MAX_RANDOM_NUMBER))
            salt2 = str(random.randint(0, MAX_RANDOM_NUMBER))
            salt3 = str(random.randint(0, MAX_RANDOM_NUMBER))
            if i == 0:
                community_cards[0] = otp.encrypt(community_cards[0], pad1, safe=False)
                community_cards[1] = otp.encrypt(community_cards[1], pad2, safe=False)
                community_cards[2] = otp.encrypt(community_cards[2], pad3, safe=False)
            else:
                community_cards[0] = otp.encrypt_hex(community_cards[0], pad1, safe=False)
                community_cards[1] = otp.encrypt_hex(community_cards[1], pad2, safe=False)
                community_cards[2] = otp.encrypt_hex(community_cards[2], pad3, safe=False)
            pad1_with_salt = f'{pad1}:{salt1}'
            pad2_with_salt = f'{pad2}:{salt2}'
            pad3_with_salt = f'{pad3}:{salt3}'
            encrypted_pad1 = rsa.encrypt(
                message_str=pad1_with_salt,
                n=int(keys[0]),
                e=int(keys[1])    
            )
            encrypted_pad2 = rsa.encrypt(
                message_str=pad2_with_salt,
                n=int(keys[0]),
                e=int(keys[1])    
            )
            encrypted_pad3 = rsa.encrypt(
                message_str=pad3_with_salt,
                n=int(keys[0]),
                e=int(keys[1])    
            )
            hands[hand_id, player, 'player_encrypted_pad1'] = encrypted_pad1
            hands[hand_id, player, 'player_encrypted_pad2'] = encrypted_pad2
            hands[hand_id, player, 'player_encrypted_pad3'] = encrypted_pad3
            hands[hand_id, player, 'house_encrypted_pad1'] = hashlib.sha3(pad1_with_salt)
            hands[hand_id, player, 'house_encrypted_pad2'] = hashlib.sha3(pad2_with_salt)
            hands[hand_id, player, 'house_encrypted_pad3'] = hashlib.sha3(pad3_with_salt)

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
    hands[hand_id, 'next_better'] = evaluator.get_next_better(active_players, [], all_in, dealer)
    if community_cards is not None:
        hands[hand_id, 'community_encrypted'] = community_cards
        hands[hand_id, 'community'] = [None, None, None]

@export
def reveal_otp(hand_id: str, pad: int, salt: int, index: int):
    player = ctx.caller
    assert index in (FLOP, TURN, RIVER), 'Invalid index.'
    active_players = hands[hand_id, 'active_players']
    assert active_players is not None, 'This hand does not exist.'
    player_index = active_players.index(player)
    assert player_index >= 0, 'You are not in this hand.'
    # verify authenticity of key
    assert hashlib.sha3(f'{pad}:{salt}') == hands[hand_id, player, f'house_encrypted_pad{index}'], 'Invalid key or salt.'
    hands[hand_id, player, f'pad{index}'] = pad

@export
def reveal(hand_id: str, index: int) -> str:
    assert index in (FLOP, TURN, RIVER), 'Invalid index.'
    active_players = hands[hand_id, 'active_players']
    community = hands[hand_id, 'community']
    enc = hands[hand_id, 'community_encrypted'][index-1]
    n_players = len(active_players)
    for i in range(n_players):
        player = active_players[-1-i]
        pad = hands[hand_id, player, f'pad{index}']
        assert pad is not None, f'Player {player} has not revealed their pad.'
        if i != n_players - 1:
            enc = otp.decrypt_hex(
                encrypted_str=enc,
                otp=pad,
                safe=False
            )
        else:
            enc = otp.decrypt(
                encrypted_str=enc,
                otp=pad,
                safe=False
            )
    community[index-1] = enc
    hands[hand_id, 'community'] = community

def handle_done_betting(hand_id: str, game_type: int, next_better: str, active_players: list, folded: list, all_in: list, dealer: str) -> str:
    if game_type == HOLDEM_POKER or game_type == OMAHA_POKER:
        # multi rounds
        round = hands[hand_id, 'round'] or 0
        round += 1
        hands[hand_id, 'round'] = round
        if round == 4:
            hands[hand_id, 'completed'] = True
        else:
            # Update stuff
            hands[hand_id, 'full_circle'] = False
            evaluator = get_hand_evaluator()
            next_better = evaluator.get_next_better(
                active_players, folded, all_in, dealer
            )
            hands[hand_id, 'first_better'] = next_better
    else:
        hands[hand_id, 'completed'] = True
    return next_better

@export
def bet_check_or_fold(hand_id: str, bet: float):
    player = ctx.caller
    
    assert hands[hand_id, player, 'player_encrypted_hand'] is not None, 'Hand does not exist'
    assert not hands[hand_id, 'completed'], 'This hand has already completed.'
    assert hands[hand_id, 'next_better'] == player, 'It is not your turn to bet.'

    active_players = hands[hand_id, 'active_players']
    folded = hands[hand_id, 'folded']
    all_in = hands[hand_id, 'all_in']

    orig_all_in = all_in.copy()

    call_bet = hands[hand_id, 'current_bet'] or 0
    player_previous_bet  = hands[hand_id, player, 'bet'] or 0
    dealer = hands[hand_id, 'dealer']

    evaluator = get_hand_evaluator()
    next_better = evaluator.get_next_better(active_players, folded, all_in, player)

    if dealer == player or (next_better is not None and next_better == hands[hand_id, 'first_better']):
        # Been around the circle once
        hands[hand_id, 'full_circle'] = True
        full_circle = True
    else:
        full_circle = hands[hand_id, 'full_circle']

    if next_better is None:
        # No need to bet, this is the end of the hand
        hands[hand_id, 'completed'] = True
    else:
        game_id = hands[hand_id, 'game_id']
        game_type = games[game_id, 'game_type']
        next_players_bet = hands[hand_id, next_better, 'bet']
        if bet < 0:
            # Folding
            folded.append(player)
            hands[hand_id, 'folded'] = folded
            if player in all_in:
                all_in.remove(player)
                hands[hand_id, 'all_in'] = all_in
            if len(folded) == len(active_players) - 1:
                hands[hand_id, 'completed'] = True
            current_bet = call_bet
        else:
            if bet == 0:
                # Checking
                max_bet = hands[hand_id, player, 'max_bet']
                if max_bet == player_previous_bet and player not in all_in:
                    all_in.append(player)
                    hands[hand_id, 'all_in'] = all_in
                current_bet = player_previous_bet
            else:
                # Betting
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
                hands[hand_id, player, 'bet'] = current_bet
                hands[hand_id, 'current_bet'] = current_bet
                hands[hand_id, 'pot'] += bet
                games[game_id, player] -= bet
            assert max_bet == current_bet or current_bet >= call_bet, 'Current bet is above your bet and you did not go all in.'                    
        if next_players_bet is not None and next_players_bet == current_bet and full_circle:
            next_better = handle_done_betting(hand_id, game_type, next_better, active_players, folded, orig_all_in, dealer)

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

    assert bet_should_equal == player_bet or player in hands[hand_id, 'all_in'], 'Bets have not stabilized.'

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

        evaluator = get_hand_evaluator()

        if game_type == BLIND_POKER:
            j = 0
            for p in active_players:
                if p != player:
                    if p not in folded:
                        card = cards[j]
                        rank = evaluator.evaluate([card])
                        if hands[hand_id, p, 'rank'] is None:
                            hands[hand_id, p, 'rank'] = rank
                            hands[hand_id, p, 'hand'] = card
                    j += 1        
        else:
            if game_type == HOLDEM_POKER or game_type == OMAHA_POKER:
                # Add community cards
                community = hands[hand_id, 'community']
                assert community is not None, 'Please reveal the community cards first.'
                cards.extend(community[0].split(','))
                cards.extend(community[1:])
            rank = evaluator.evaluate(cards)
            hands[hand_id, player, 'rank'] = rank
            hands[hand_id, player, 'hand'] = cards

        return 'Verification succeeded.'

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
        evaluator = get_hand_evaluator()
        ranks = calculate_ranks(hand_id, remaining)
        if len(all_in) > 0:
            # Need to calculate split pots
            all_in_map = {}
            for player in all_in:
                # Check all in amount
                amount = hands[hand_id, player, 'max_bet']
                all_in_map[player] = amount
            all_pots = sorted(all_in_map.values())
            unique_pots = []
            for bet in all_pots:
                if bet not in unique_pots:
                    unique_pots.append(bet)
            total_payed_out = 0
            previous_pot_payout = 0
            for bet in unique_pots:
                players_in_pot = []
                for player in remaining:
                    if player not in all_in_map or all_in_map[player] >= bet:
                        players_in_pot.append(player)
                pot_winners = evaluator.find_winners(ranks, players_in_pot)
                pot_payout = (bet * len(players_in_pot)) - previous_pot_payout
                total_payed_out += pot_payout
                payout = pot_payout / len(pot_winners)
                for winner in pot_winners:
                    if winner not in payouts:
                        payouts[winner] = 0
                    payouts[winner] += payout     
                previous_pot_payout += pot_payout
                      
            remaining_to_payout = pot - total_payed_out
            not_all_in = set(remaining).difference(set(all_in))
            assert remaining_to_payout >= 0, 'Invalid remaining to payout.'
            assert remaining_to_payout == 0 or len(not_all_in) > 0, 'Invalid state when calculating side pots.'            
            if remaining_to_payout > 0:
                if len(not_all_in) == 1:
                    winners = not_all_in
                else:
                    winners = evaluator.find_winners(ranks, not_all_in)
                payout = remaining_to_payout / len(winners)
                for winner in winners:
                    if winner not in payouts:
                        payouts[winner] = 0
                    payouts[winner] += payout
        else:
            winners = evaluator.find_winners(ranks, remaining)
            payout = pot / len(winners)
            for winner in winners:
                payouts[winner] = payout

    game_id = hands[hand_id, 'game_id']
    for player, payout in payouts.items():
        games[game_id, player] += payout

    hands[hand_id, 'winners'] = list(payouts.keys())
    hands[hand_id, 'payouts'] = payouts
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