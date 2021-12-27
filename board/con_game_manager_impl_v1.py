
I = importlib

GAME_NAMES = ['checkers', 'chess', 'go']

CONTRACT_FOR_GAME_TYPE = {
    'checkers': 'con_checkers_v1',
    'chess': 'con_chess_v1',
    'go': 'con_go_v1',
}

def play_again(state: dict, initial_state: dict):
    assert state.get('completed') is not None and state['completed'], 'Game has not completed yet.'
    state['current_player'] = initial_state['current_player']
    state['board'] = initial_state['board']
    creator_team = state['creator_team']
    opponent_team = state['opponent_team']
    state['creator_wins'] = 0
    state['opponent_wins'] = 0
    state['creator_team'] = opponent_team
    state['opponent_team'] = creator_team
    state['round'] = 1
    state['winner'] = None
    state['completed'] = None
    state['creator_paid'] = None
    state['opponent_paid'] = None


def next_round(state: dict, initial_state: dict):
    assert state.get('winner') is not None, 'Previous round has not completed yet.'
    assert state.get('completed') is None or not state['completed'], 'Rounds have completed. Please play again.'
    state['current_player'] = initial_state['current_player']
    state['board'] = initial_state['board']
    creator_team = state['creator_team']
    opponent_team = state['opponent_team']
    state['creator_team'] = opponent_team
    state['opponent_team'] = creator_team
    state['round'] += 1
    state['winner'] = None


def create_game(payload: dict, caller: str, metadata: Any) -> str:
    other_player = payload.get('other_player')
    public = payload.get('public', False)
    creator_first = payload.get('creator_first', True)
    wager = payload.get('wager', 0)
    rounds = payload.get('rounds', 1)
    game_type = payload.get('type')

    assert game_type in GAME_NAMES, 'Invalid game type.'

    initial_state = I.import_module(CONTRACT_FOR_GAME_TYPE[game_type]).get_initial_state()

    assert public or other_player is not None, 'No opponent specified in private game.'
    assert not (public and other_player is not None), 'Opponent specified in public game.'
    assert isinstance(wager, int) or isinstance(wager, float), 'Wager must be numeric.'
    assert wager >= 0, 'Wager cannot be negative.'
    assert isinstance(rounds, int), 'Rounds must be an integer.'
    assert rounds >= 1, 'Rounds must be >= 1.'

    game_state = initial_state.copy()
    game_id = hashlib.sha3(caller+str(now))
    
    assert metadata[game_type, game_id, 'state'] is None, 'Game already exists.'
    
    game_state['creator'] = caller
    game_state['public'] = public
    game_state['round'] = 1

    if rounds > 1:
        game_state['rounds'] = rounds

    if (creator_first and game_type in ['checkers', 'go']) \
         or (not creator_first and game_type == 'chess'):
        game_state['creator_team'] = 'b'
        game_state['opponent_team'] = 'w'
    else:
        game_state['creator_team'] = 'w'
        game_state['opponent_team'] = 'b'

    if wager > 0:
        I.import_module(ctx.owner).force_deposit(
            amount=wager,
            main_account=caller,
        )  
        game_state['wager'] = wager
    game_state['creator_paid'] = True

    add_game_for_user(caller, game_type, game_id, metadata)

    if other_player is not None:
        game_state['opponent'] = other_player
        add_game_for_user(other_player, game_type, game_id, metadata)
    else:
        # Public
        public_games = metadata[game_type, 'public'] or []
        public_games.append(game_id)
        metadata[game_type, 'public'] = public_games

    # Update game state
    metadata[game_type, game_id, 'state'] = game_state
    return game_id


def add_game_for_user(player: str, game_type: str, game_id: str, metadata: Any):
    num_games = metadata[game_type, player, 'count'] or 0
    num_games += 1
    metadata[game_type, player, 'count'] = num_games
    metadata[game_type, player, f'game-{num_games}'] = game_id


def store_historical_state(state: dict, game_type: str, game_id: str, metadata: Any):
    history_count = metadata[game_type, game_id, 'history-count'] or 0
    history_count += 1
    metadata[game_type, game_id, 'history', history_count] = state
    metadata[game_type, game_id, 'history-count'] = history_count


def get_game_state(metadata: Any, game_type: str, game_id: str) -> dict:
    game_state = metadata[game_type, game_id, 'state']
    assert game_state is not None, 'Game does not exist.'
    return game_state


def set_game_state(metadata: Any, game_type: str, game_id: str, state: dict):
    metadata[game_type, game_id, 'state'] = state
    

def assert_in_game(caller: str, game_state: dict):
    assert game_state['creator'] == caller or game_state['opponent'] == caller, 'You are not in this game.'


@export
def interact(payload: dict, state: dict, caller: str) -> Any:
    metadata = state['metadata']
    action = payload['action']

    if action == 'create':
        return create_game(payload, caller, metadata)
    
    else:
        game_id = payload['game_id']
        game_type = payload['type']
        game_state = get_game_state(metadata, game_type, game_id)
        if action != 'join':
            assert_in_game(caller, game_state)
        assert game_type in GAME_NAMES, 'Invalid game type.'

        if action == 'pay_up':
            wager = game_state.get('wager', 0)
            assert wager > 0, 'No need to pay up.'
            I.import_module(ctx.owner).force_deposit(
                amount=wager,
                main_account=caller,
            )  
            if caller == game_state['creator']:
                assert not game_state.get('creator_paid'), 'Already paid.'
                game_state['creator_paid'] = True
            else:
                assert not game_state.get('opponent_paid'), 'Already paid.'
                game_state['opponent_paid'] = True
        elif action == 'end_game':
            contract = I.import_module(CONTRACT_FOR_GAME_TYPE[game_type])
            contract.end_game(game_state)
        # TODO implement the next 4 conditionals
        elif action == 'forfeit_game':
            pass
        elif action == 'request_end':
            pass
        elif action == 'accept_end':
            pass
        elif action == 'enforce_time_limit':
            pass
        elif action == 'next_round':
            store_historical_state(game_state, game_type, game_id, metadata)
            initial_state = I.import_module(CONTRACT_FOR_GAME_TYPE[game_type]).get_initial_state()
            next_round(game_state, initial_state)

        elif action == 'play_again':
            store_historical_state(game_state, game_type, game_id, metadata)
            initial_state = I.import_module(CONTRACT_FOR_GAME_TYPE[game_type]).get_initial_state()
            play_again(game_state, initial_state)
            wager = game_state.get('wager', 0)
            if wager > 0:
                I.import_module(ctx.owner).force_deposit(
                    amount=wager,
                    main_account=caller,
                )  
                if caller == game_state['creator']:
                    game_state['creator_paid'] = True
                else:
                    game_state['opponent_paid'] = True
            else:
                game_state['opponent_paid'] = True
                game_state['creator_paid'] = True

        elif action == 'join':
            public = game_state['public']
            opponent = game_state.get('opponent')
            if public:
                assert opponent is None, 'There is already an opponent.'
            else:
                assert opponent == caller, 'You were not invited.'               
            assert caller != game_state['creator'], 'You are the creator of this game.'
            game_state['opponent'] = caller
            wager = game_state.get('wager', 0)
            if wager > 0:
                I.import_module(ctx.owner).force_deposit(
                    amount=wager,
                    main_account=caller,
                )  
            game_state['opponent_paid'] = True
            if public:
                add_game_for_user(caller, game_type, game_id, metadata)
        elif action == 'move':
            is_creator = game_state['creator'] == caller
            if is_creator:
                team = game_state['creator_team']
                assert game_state['creator_paid'], 'You have not paid yet.'
            else:
                assert caller == game_state['opponent'], 'You are not in this game.'
                team = game_state['opponent_team']
                assert game_state.get('opponent_paid'), 'You have not paid yet.'
            amount = I.import_module(CONTRACT_FOR_GAME_TYPE[game_type]).move(
                caller=caller,
                team=team,
                x1=payload['x1'],
                y1=payload['y1'],
                x2=payload['x2'],
                y2=payload['y2'],
                state=game_state
            )
            if amount > 0:
                I.import_module(ctx.owner).force_withdraw(
                    player=caller,
                    amount=amount
                )
        else:
            assert False, f'Unknown action: {action}.'

        # Update game state
        set_game_state(metadata, game_type, game_id, game_state)
