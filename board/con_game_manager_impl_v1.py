# con_game_manager_impl_v1
# owner: con_game_manager_v1

I = importlib

CONTRACT_FOR_GAME_TYPE = Variable()
TIME_LIMIT_DAYS = 2


@construct
def init():
    CONTRACT_FOR_GAME_TYPE.set({
        'checkers': 'con_checkers_v1',
        'chess': 'con_chess_v1',
        'go': 'con_go_v1',
    })


def reset_game_state(state: dict, initial_state: dict):
    creator_team = state['creator_team']
    opponent_team = state['opponent_team']

    state.clear()

    state['current_player'] = initial_state['current_player']
    state['board'] = initial_state['board']
    # Swap teams
    state['creator_team'] = opponent_team
    state['opponent_team'] = creator_team
    state['round_start'] = now



def play_again(state: dict, initial_state: dict):
    assert state.get('completed') is not None and state['completed'], 'Game has not completed yet.'
    reset_game_state(state, initial_state)


def next_round(state: dict, initial_state: dict):
    assert state.get('winner') is not None or state.get('stalemate'), 'Previous round has not completed yet.'
    assert state.get('completed') is None or not state['completed'], 'Rounds have completed. Please play again.'
    creator_paid = state.get('creator_paid')
    opponent_paid = state.get('opponent_paid')
    creator_wins = state.get('creator_wins')
    opponent_wins = state.get('opponent_wins')
    reset_game_state(state, initial_state)
    if creator_paid is not None:
        state['creator_paid'] = creator_paid
    if opponent_paid is not None:
        state['opponent_paid'] = opponent_paid
    if creator_wins is not None:
        state['creator_wins'] = creator_wins
    if opponent_wins is not None:
        state['opponent_wins'] = opponent_wins


def create_game(payload: dict, caller: str, metadata: Any) -> str:
    other_player = payload.get('other_player')
    public = payload.get('public', False)
    creator_first = payload.get('creator_first', True)
    wager = payload.get('wager', 0)
    rounds = payload.get('rounds', 1)
    game_type = payload.get('type')
    game_name = payload.get('game_name', payload.get('name'))

    contract_for_game_type = CONTRACT_FOR_GAME_TYPE.get()

    assert game_type in contract_for_game_type, 'Invalid game type.'

    initial_state = I.import_module(contract_for_game_type[game_type]).get_initial_state()

    assert public or other_player is not None, 'No opponent specified in private game.'
    assert not (public and other_player is not None), 'Opponent specified in public game.'
    assert isinstance(wager, int) or isinstance(wager, float), 'Wager must be numeric.'
    assert wager >= 0, 'Wager cannot be negative.'
    assert isinstance(rounds, int), 'Rounds must be an integer.'
    assert rounds >= 1, 'Rounds must be >= 1.'

    game_state = initial_state.copy()

    if not creator_first:
        tmp = game_state['opponent_team']
        game_state['opponent_team'] = game_state['creator_team']
        game_state['creator_team'] = tmp

    game_metadata = {}

    game_id = hashlib.sha3(caller+str(now))
    
    assert metadata[game_type, game_id, 'state'] is None, 'Game already exists.'
    
    game_metadata['creator'] = caller
    game_metadata['public'] = public
    game_metadata['rounds'] = rounds
    if game_name is not None:
        game_metadata['name'] = game_name

    if wager > 0:
        I.import_module(ctx.owner).force_deposit(
            amount=wager,
            main_account=caller,
        )  
        game_metadata['wager'] = wager

    game_state['creator_paid'] = True
    game_state['round_start'] = now

    add_game_for_user(caller, game_type, game_id, metadata)

    if other_player is not None:
        game_metadata['opponent'] = other_player
        add_game_for_user(other_player, game_type, game_id, metadata)
    else:
        # Public
        public_games = metadata[game_type, 'public'] or []
        public_games.append(game_id)
        metadata[game_type, 'public'] = public_games

    # Update state
    set_game_state(metadata, game_type, game_id, game_state)
    set_game_metadata(metadata, game_type, game_id, game_metadata)

    # Return game_id
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
    

def get_game_metadata(metadata: Any, game_type: str, game_id: str) -> dict:
    game_state = metadata[game_type, game_id, 'metadata']
    assert game_state is not None, 'Game does not exist.'
    return game_state


def set_game_metadata(metadata: Any, game_type: str, game_id: str, state: dict):
    metadata[game_type, game_id, 'metadata'] = state
    

def assert_in_game(caller: str, game_metadata: dict):
    assert game_metadata['creator'] == caller or game_metadata['opponent'] == caller, 'You are not in this game.'


def assert_both_parties_paid(game_state: dict):
    assert 'creator_paid' in game_state and game_state['creator_paid'], 'Creator has not paid yet.'
    assert 'opponent_paid' in game_state and game_state['opponent_paid'], 'Opponent has not paid.'


def assert_round_not_completed(game_state: dict):
    assert game_state.get('completed') is None and game_state.get('winner') is None and game_state.get('stalemate') is None, 'This round has already completed.'


def assert_round_completed(game_state: dict):
    assert game_state.get('winner') is not None or game_state.get('stalemate'), 'This round has not yet completed.'


def handle_round_end(game_state: dict, game_metadata: dict):
    if game_state.get('stalemate'):
        return
    winner = game_state['winner']
    wager = game_metadata.get('wager', 0)
    creator_team = game_state['creator_team']
    if creator_team == winner:
        winner_address = game_metadata['creator']
        game_state['creator_wins'] = game_state.get('creator_wins', 0) + 1
    else:
        winner_address = game_metadata['opponent']
        game_state['opponent_wins'] = game_state.get('opponent_wins', 0) + 1
    rounds = game_metadata.get('rounds', 1)
    creator_wins = game_state.get('creator_wins', 0)
    opponent_wins = game_state.get('opponent_wins', 0)
    if creator_wins > rounds // 2 or opponent_wins > rounds // 2:
        game_state['completed'] = True
        if wager > 0:
            amount_to_pay = 0.0
            if game_state.get('opponent_paid'):
                amount_to_pay += wager
            if game_state.get('creator_paid'):
                amount_to_pay += wager
            if amount_to_pay > 0:
                I.import_module(ctx.owner).force_withdraw(
                    player=winner_address,
                    amount=amount_to_pay
                )

@export
def interact(payload: dict, state: dict, caller: str) -> Any:
    metadata = state['metadata']
    owner = state['owner']
    action = payload['action']

    if action == 'create':
        return create_game(payload, caller, metadata)
    elif action == 'update_contracts':
        assert caller == owner.get(), 'Only the owner can call update_contracts.'
        CONTRACT_FOR_GAME_TYPE.set(payload['contracts'])
    else:
        game_id = payload['game_id']
        game_type = payload['type']
        game_state = get_game_state(metadata, game_type, game_id)
        game_metadata = get_game_metadata(metadata, game_type, game_id)
        is_creator = game_metadata['creator'] == caller
        contract_for_game_type = CONTRACT_FOR_GAME_TYPE.get()
        wager = game_metadata.get('wager', 0)

        if action != 'join':
            assert_in_game(caller, game_metadata)

        assert game_type in contract_for_game_type, 'Invalid game type.'

        if action == 'pay_up':
            assert wager > 0, 'No need to pay up.'
            I.import_module(ctx.owner).force_deposit(
                amount=wager,
                main_account=caller,
            )  
            if is_creator:
                assert not game_state.get('creator_paid'), 'Already paid.'
                game_state['creator_paid'] = True
            else:
                assert not game_state.get('opponent_paid'), 'Already paid.'
                game_state['opponent_paid'] = True

        elif action == 'forfeit_round':
            assert_round_not_completed(game_state)
            assert_both_parties_paid(game_state)
            if is_creator:
                winner = game_state['opponent_team']
            else:
                winner = game_state['creator_team']
            game_state['winner'] = winner
            handle_round_end(game_state, game_metadata)
                                         
        elif action == 'request_end':
            assert_round_not_completed(game_state)
            assert_both_parties_paid(game_state)
            assert game_state.get('creator_requested_end') is None and game_state.get('opponent_requested_end') is None, 'End request has already been submitted.'
            if is_creator:
                game_state['creator_requested_end'] = True
            else:
                game_state['opponent_requested_end'] = True

        elif action == 'accept_end':
            assert_round_not_completed(game_state)
            assert_both_parties_paid(game_state)
            assert game_state.get('creator_accepted_end') is None and game_state.get('opponent_accepted_end') is None, 'End request has already been accepted.'
            if is_creator:
                assert game_state['opponent_requested_end'], 'Opponent did not request an end to this round.'
                game_state['creator_accepted_end'] = True
            else:
                assert game_state['creator_requested_end'], 'Creator did not request an end to this round.'
                game_state['opponent_accepted_end'] = True
            contract = I.import_module(contract_for_game_type[game_type])
            contract.force_end_round(game_state, game_metadata)
            game_state['completed'] = True
            handle_round_end(game_state, game_metadata)

        elif action == 'early_end':
            if is_creator:
                # Assert creator paid and opponent did not
                assert 'creator_paid' in game_state and game_state['creator_paid'], 'You did not pay yet.'
                assert 'opponent_paid' not in game_state or not game_state['opponent_paid'], 'Opponent has already paid.'
                del game_state['creator_paid']
            else:
                assert 'opponent_paid' in game_state and game_state['opponent_paid'], 'You did not pay yet.'
                assert 'creator_paid' not in game_state or not game_state['creator_paid'], 'Opponent has already paid.'
                del game_state['opponent_paid']

            contract = I.import_module(contract_for_game_type[game_type])
            contract.force_end_round(game_state, game_metadata)
            game_state['completed'] = True
            if wager > 0:
                I.import_module(ctx.owner).force_withdraw(
                    player=caller,
                    amount=wager
                )   

        elif action == 'enforce_time_limit':
            # TODO implement this guy
            assert_round_not_completed(game_state)
            
            round_start = game_state.get('round_start')
            assert round_start is not None, 'No round has been started.'
            current_player = game_state['current_player']

            if is_creator:
                assert current_player != game_state['creator_team'], 'Cannot enforce time limit on your own turn.'
                last_played_key = 'opponent_played_at'
            else:
                assert current_player == game_state['creator_team'], 'Cannot enforce time limit on your own turn.'
                last_played_key = 'creator_played_at'

            last_relevant_time = max([
                game_state.get('opponent_played_at', round_start),
                game_state.get('creator_played_at', round_start),
            ])
            unlockable_at = last_relevant_time + datetime.timedelta(days=TIME_LIMIT_DAYS)
            assert now > unlockable_at, f'You must wait {TIME_LIMIT_DAYS} days to enforce the time limit.'
            contract = I.import_module(contract_for_game_type[game_type])
            contract.force_end_round(game_state, game_metadata)
            game_state['completed'] = True
            payout = 0.0
            if 'creator_paid' in game_state and game_state['creator_paid']:
                del game_state['creator_paid']
                payout += wager
            if 'opponent_paid' in game_state and game_state['opponent_paid']:
                del game_state['opponent_paid']
                payout += wager
            if payout > 0:
                I.import_module(ctx.owner).force_withdraw(
                    player=caller,
                    amount=payout
                )               

        elif action == 'next_round':
            store_historical_state(game_state, game_type, game_id, metadata)
            initial_state = I.import_module(contract_for_game_type[game_type]).get_initial_state()
            next_round(game_state, initial_state)

        elif action == 'play_again':
            store_historical_state(game_state, game_type, game_id, metadata)
            initial_state = I.import_module(contract_for_game_type[game_type]).get_initial_state()
            play_again(game_state, initial_state)
            if wager > 0:
                I.import_module(ctx.owner).force_deposit(
                    amount=wager,
                    main_account=caller,
                )  
                if is_creator:
                    game_state['creator_paid'] = True
                else:
                    game_state['opponent_paid'] = True
            else:
                game_state['opponent_paid'] = True
                game_state['creator_paid'] = True

        elif action == 'join':
            public = game_metadata['public']
            opponent = game_metadata.get('opponent')
            if public:
                assert opponent is None, 'There is already an opponent.'
            else:
                assert opponent == caller, 'You were not invited.'               
            assert caller != game_metadata['creator'], 'You are the creator of this game.'
            game_metadata['opponent'] = caller
            if wager > 0:
                I.import_module(ctx.owner).force_deposit(
                    amount=wager,
                    main_account=caller,
                )  
            game_state['opponent_paid'] = True
            if public:
                add_game_for_user(caller, game_type, game_id, metadata)
            set_game_metadata(metadata, game_type, game_id, game_metadata)

        elif action == 'move':
            assert_round_not_completed(game_state)
            if is_creator:
                team = game_state['creator_team']
                assert game_state['creator_paid'], 'You have not paid yet.'
                last_played_key = 'creator_played_at'
            else:
                team = game_state['opponent_team']
                assert game_state.get('opponent_paid'), 'You have not paid yet.'
                last_played_key = 'opponent_played_at'
            I.import_module(contract_for_game_type[game_type]).move(
                caller=caller,
                team=team,
                payload=payload,
                state=game_state,
                metadata=game_metadata,
            )
            game_state[last_played_key] = now
            if game_state.get('winner') is not None:
                assert_both_parties_paid(game_state)                
                handle_round_end(game_state, game_metadata)

        else:
            assert False, f'Unknown action: {action}.'

        # Update game state
        set_game_state(metadata, game_type, game_id, game_state)
