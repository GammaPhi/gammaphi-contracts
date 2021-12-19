# con_poker_card_games_v3
import con_phi_lst001 as phi
I = importlib

phi_balances = ForeignHash(foreign_contract='con_phi_lst001', foreign_name='balances')

games = Hash(default_value=None)
hands = Hash(default_value=None)
game_names = Hash(default_value=None)
players_games = Hash(default_value=[])
players_invites = Hash(default_value=[])

player_metadata_contract = Variable()
game_controller_contract = Variable()
hand_controller_contract = Variable()

owner = Variable()


@construct
def seed():
    owner.set(ctx.caller)
    player_metadata_contract.set('con_gamma_phi_profile_v4')
    hand_controller_contract.set('con_poker_hand_controller_v3')
    game_controller_contract.set('con_poker_game_controller_v2')

@export
def update_player_metadata_contract(contract: str):
    assert ctx.caller == owner.get(), 'Only the owner can call update_player_metadata_contract()'
    player_metadata_contract.set(contract)


@export
def update_hand_controller_contract(contract: str):
    assert ctx.caller == owner.get(), 'Only the owner can call update_player_metadata_contract()'
    hand_controller_contract.set(contract)


@export
def update_game_controller_contract(contract: str):
    assert ctx.caller == owner.get(), 'Only the owner can call update_player_metadata_contract()'
    game_controller_contract.set(contract)


@export
def add_chips_to_game(game_id: str, amount: float):
    player = ctx.caller
    module = I.import_module(game_controller_contract.get())
    module.add_chips_to_game(
        game_id=game_id,
        amount=amount,
        player=player,
        games=games,
    )

@export
def withdraw_chips_from_game(game_id: str, amount: float):
    player = ctx.caller
    module = I.import_module(game_controller_contract.get())
    module.withdraw_chips_from_game(
        game_id=game_id,
        amount=amount,
        player=player,
        games=games,
    )


@export
def respond_to_invite(game_id: str, accept: bool):
    player = ctx.caller
    module = I.import_module(game_controller_contract.get())
    module.respond_to_invite(
        game_id=game_id,
        accept=accept,
        player=player,
        games=games,
        players_invites=players_invites,
        players_games=players_games
    )


@export
def decline_all_invites():
    # Nuclear option
    player = ctx.caller
    module = I.import_module(game_controller_contract.get())
    module.decline_all_invites(
        player=player,
        players_invites=players_invites
    )


@export
def start_game(name: str, 
               other_players: list,
               game_config: dict,
               public: bool = False) -> str:

    creator = ctx.caller
    module = I.import_module(game_controller_contract.get())
    return module.start_game(
        name=name,
        other_players=other_players,
        game_config=game_config,
        creator=creator,
        games=games,
        players_games=players_games,
        players_invites=players_invites,
        game_names=game_names,
        public=public
    )


@export
def add_player_to_game(game_id: str, player_to_add: str):
    player = ctx.caller
    module = I.import_module(game_controller_contract.get())
    module.add_player_to_game(
        game_id=game_id,
        player_to_add=player_to_add,
        player=player,
        games=games,
        players_invites=players_invites,
    )


@export
def leave_game(game_id: str):
    player = ctx.caller
    module = I.import_module(game_controller_contract.get())
    module.leave_game(
        game_id=game_id,
        player=player,
        force=False,
        games=games,
        players_games=players_games
    )


@export
def force_withdraw(player: str, amount: float):
    assert ctx.caller == game_controller_contract.get(), 'Only the game controller contract can call this method.'
    phi.transfer(
        amount=amount,
        to=player
    )


@export
def force_transfer(player: str, amount: float):
    assert ctx.caller == game_controller_contract.get(), 'Only the game controller contract can call this method.'
    assert phi_balances[player, ctx.this] >= amount, 'You have not approved enough for this amount of chips'
    phi.transfer_from(amount, ctx.this, player)


@export
def kick_from_game(game_id: str, player: str):
    creator = ctx.caller
    module = I.import_module(game_controller_contract.get())
    module.kick_from_game(
        game_id=game_id,
        creator=creator,
        player=player,
        games=games,
        players_games=players_games,
    )


@export
def ban_player(game_id: str, player: str):
    creator = ctx.caller
    module = I.import_module(game_controller_contract.get())
    module.ban_player(
        game_id=game_id,
        creator=creator,
        player=player,
        games=games,
        players_games=players_games,
    )


@export
def unban_player(game_id: str, player: str):
    creator = ctx.caller
    module = I.import_module(game_controller_contract.get())
    module.unban_player(
        game_id=game_id,
        creator=creator,
        player=player,
        games=games,
    )


@export
def start_hand(game_id: str) -> str:
    dealer = ctx.caller
    module = I.import_module(hand_controller_contract.get())
    return module.start_hand(
        game_id=game_id,
        dealer=dealer,
        games=games,
        hands=hands,
    )


@export
def ante_up(hand_id: str):
    player = ctx.caller
    module = I.import_module(hand_controller_contract.get())
    module.ante_up(
        hand_id=hand_id,
        player=player,
        games=games,
        hands=hands,
    )


@export
def deal_cards(hand_id: str):
    dealer = ctx.caller
    module = I.import_module(hand_controller_contract.get())
    player_metadata = ForeignHash(foreign_contract=player_metadata_contract.get(), foreign_name='metadata')
    module.deal_cards(
        hand_id=hand_id,
        dealer=dealer,
        games=games,
        hands=hands,
        player_metadata=player_metadata
    )


@export
def reveal_otp(hand_id: str, pad: int, salt: int, index: int):
    player = ctx.caller
    module = I.import_module(hand_controller_contract.get())
    module.reveal_otp(
        hand_id=hand_id,
        pad=pad,
        salt=salt,
        index=index,
        player=player,
        hands=hands,
    )


@export
def reveal(hand_id: str, index: int) -> str:
    module = I.import_module(hand_controller_contract.get())
    return module.reveal(
        hand_id=hand_id,
        index=index,
        hands=hands,
    )


@export
def bet_check_or_fold(hand_id: str, bet: float):
    player = ctx.caller
    module = I.import_module(hand_controller_contract.get())
    module.bet_check_or_fold(
        hand_id=hand_id,
        bet=bet,
        player=player,
        games=games,
        hands=hands,
    )


@export
def verify_hand(hand_id: str, player_hand_str: str) -> str:
    player = ctx.caller
    module = I.import_module(hand_controller_contract.get())
    return module.verify_hand(
        hand_id=hand_id,
        player_hand_str=player_hand_str,
        player=player,
        games=games,
        hands=hands,
    )


@export
def payout_hand(hand_id: str):
    module = I.import_module(hand_controller_contract.get())
    module.payout_hand(
        hand_id=hand_id,
        games=games,
        hands=hands,
    )


@export
def leave_hand(player: str, game_id: str, hand_id: str, force: bool):
    assert ctx.caller == game_controller_contract.get(), 'Only the game controller contract can call this method.'
    module = I.import_module(hand_controller_contract.get())
    module.leave_hand(
        game_id=game_id,
        hand_id=hand_id,
        player=player,
        force=force,
        games=games,
        hands=hands
    )


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