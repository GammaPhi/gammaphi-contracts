# con_poker_game_controller_v2
# owner: con_poker_card_games_v4

I = importlib


ONE_CARD_POKER = 0
BLIND_POKER = 1
STUD_POKER = 2
HOLDEM_POKER = 3
OMAHA_POKER = 4
ALL_GAME_TYPES = [ONE_CARD_POKER, BLIND_POKER, STUD_POKER, HOLDEM_POKER, OMAHA_POKER]
NO_LIMIT = 0
POT_LIMIT = 1
ALL_BETTING_TYPES = [NO_LIMIT, POT_LIMIT]


def get_players_and_assert_exists(game_id: str, games: Any) -> dict:
    players = games[game_id, 'players']
    assert players is not None, f'Game {game_id} does not exist.'
    return players


def create_game_id(name: str) -> str:
    return hashlib.sha3(":".join([name, str(now)]))


@export
def add_chips_to_game(game_id: str, amount: float, player: str, games: Any):
    assert amount > 0, 'Amount must be a positive number'
    players = get_players_and_assert_exists(game_id, games)
    assert player in players, 'You do not belong to this game.'
    games[game_id, player] = (games[game_id, player] or 0.0) + amount
    I.import_module(ctx.owner).force_transfer(player=player, amount=amount)


@export
def withdraw_chips_from_game(game_id: str, amount: float, player: str, games: Any):
    assert amount > 0, 'Amount must be a positive number'
    current_chip_count = games[game_id, player] or 0
    assert current_chip_count >= amount, 'You cannot withdraw more than you have.'
    games[game_id, player] = current_chip_count - amount
    I.import_module(ctx.owner).force_withdraw(player=player, amount=amount)
    

@export
def respond_to_invite(game_id: str, accept: bool, player: str, games: Any, players_invites: Any, players_games: Any):
    player_invites = players_invites[player] or []
    players = get_players_and_assert_exists(game_id, games)
    assert player not in players, 'You are already a part of this game.'
    declined = players_invites[player, 'declined'] or []
    public = games[game_id, 'public']
    assert game_id in player_invites or game_id in declined or public, 'You have not been invited to this game.'
    if public:
        # check banned players
        assert player not in (games[game_id, 'banned'] or []), 'You have been banned from this public game.'
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
def decline_all_invites(player: str, players_invites: Any):
    invites = players_invites[player] or []
    for invite in invites:
        players_invites[player, invite] = False
    players_invites[player] = []
    
def send_invite_requests(game_id: str, others: list, players_invites: Any):
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
               creator: str,
               game_config: dict,
               games: Any,
               game_names: Any,
               players_games: Any,
               players_invites: Any,
               public: bool = False) -> str:
    
    game_type = game_config['game_type']
    bet_type = game_config['bet_type']
    assert game_type in ALL_GAME_TYPES, f'Invalid game type: {game_type}.'
    assert bet_type in ALL_BETTING_TYPES, f'Invalid betting type: {bet_type}.'

    ante = game_config['ante']
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
        n_cards_total = game_config['n_cards_total']
        n_hole_cards = game_config['n_hole_cards']
        assert n_cards_total is not None, 'Must specify n_cards_total for stud poker.'
        assert n_hole_cards is not None, 'Must specify n_hole_cards for stud poker.'
        assert n_cards_total == 5 or n_cards_total == 7, 'n_cards_total must equal 5 or 7.'
        assert n_hole_cards > 0, 'n_hole_cards must be positive.'
        assert n_hole_cards <= n_cards_total, 'n_hole_cards must be less than or equal to n_cards_total.'
        games[game_id, 'n_cards_total'] = n_cards_total
        games[game_id, 'n_hole_cards'] = n_hole_cards

    players_games[creator] = (players_games[creator] or []) + [game_id]
    send_invite_requests(game_id, other_players, players_invites)

    return game_id

@export
def add_player_to_game(game_id: str, player_to_add: str, player: str, games: Any, players_invites: Any):
    assert player != player_to_add, 'You cannot add yourself to a game.'
    creator = games[game_id, 'creator']
    assert player == creator, 'Only the game creator can add players.'
    players = get_players_and_assert_exists(game_id, games)
    assert player_to_add not in players, 'Player is already in the game.'
    invitees = games[game_id, 'invitees']
    assert player_to_add not in invitees, 'Player has already been invited.'
    invitees.append(player_to_add)
    games[game_id, 'invitees'] = invitees
    send_invite_requests(game_id, [player_to_add], players_invites)

@export
def leave_game(game_id: str, player: str, force: bool, games: Any, players_games: Any):
    players = get_players_and_assert_exists(game_id, games)
    assert player in players, 'You are not in this game.'

    chips = games[game_id, player]

    hand_id = games[game_id, 'current_hand']

    if hand_id is not None:
        I.import_module(ctx.owner).leave_hand(            
            game_id=game_id,
            hand_id=hand_id,
            player=player,
            force=force,
        )        

    if chips is not None and chips > 0:
        # Withdraw their chips
        withdraw_chips_from_game(game_id, chips, player, games)

    player_games = players_games[player]
    player_games.remove(game_id)
    players_games[player] = player_games
    players.remove(player)
    games[game_id, 'players'] = players


@export
def kick_from_game(game_id: str, creator: str, player: str, games: Any, players_games: Any):
    assert creator == games[game_id, 'creator'], 'Only the game creator can remove players from the game.'
    assert creator != player, 'You cannot force kick yourself out of the game.'
    # Kick them out
    leave_game(game_id, player, True, games, players_games)


@export
def ban_player(game_id: str, creator: str, player: str, games: Any, players_games: Any):
    assert games[game_id, 'public'], 'You can only ban people from public games.'
    kick_from_game(game_id, creator, player, games, players_games)
    banned = games[game_id, 'banned'] or []
    banned.append(player)
    games[game_id, 'banned'] = banned


@export
def unban_player(game_id: str, creator: str, player: str, games: Any):
    assert games[game_id, 'public'], 'You can only unban people from public games.'
    assert creator == games[game_id, 'creator'], 'Only the game creator can remove players from the game.'
    assert creator != player, 'You cannot unban yourself from the game.'
    banned = games[game_id, 'banned'] or []
    if player in banned:
        banned.remove(player)
        games[game_id, 'banned'] = banned
        