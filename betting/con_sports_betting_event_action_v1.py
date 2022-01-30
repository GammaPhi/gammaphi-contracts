# con_sports_betting_event_action_v1
# owner: con_sports_betting
I = importlib

# State
events = Hash(default_value=None)
total_num_events = Variable()
settings = Hash(default_value=None)

# Disputes
dispute_id = Variable()
finished_disputes = Hash()
dispute_sigs = Hash(default_value=False)
dispute_details = Hash()
dispute_status = Hash()
bets = Hash(default_value=0)


# Constants
MAIN_CONTRACT = 'con_sports_betting'
CLAIM_HOLDING_PERIOD_DAYS_STR = 'claim_holding_duration'
REQUIRED_DISPUTE_APPROVAL_PERCENTAGE_STR = 'required_dispute_approval_percentage'
DISPUTE_DURATION_DAYS_STR = 'min_dispute_duration'
MINIMUM_DISPUTE_QUORUM_STR = 'min_dispute_quorum'
MAX_DISPUTE_DURATION_DAYS_STR = 'max_dispute_duration'
REQUIRED_STAKE_ADD_EVENT_STR = 'add_event_stake'
REQUIRED_STAKE_VALIDATE_EVENT_STR = 'validate_event_stake'
TIE_FEE_PERCENT_STR = 'fie_tie'
FEE_PERCENT_STR = 'fee'
EVENT_CREATOR_FEE_PERCENT_STR = 'creator_fee'
EVENT_VALIDATOR_FEE_PERCENT_STR = 'validator_fee'
RESERVE_FEE_PERCENT_STR = 'reserve_fee'
BURN_FEE_PERCENT_STR = 'burn_fee'
TRUSTED_EVENT_CREATORS_STR = 'trusted_creators'
TRUSTED_EVENT_VALIDATORS_STR = 'trusted_validators'
BURN_ADDRESS_STR = 'burn_address'


# State from parent contract
stakes = ForeignHash(foreign_contract=MAIN_CONTRACT, foreign_name='stakes')
parent_settings = ForeignHash(foreign_contract=MAIN_CONTRACT, foreign_name='settings')


@construct
def init():
    settings[REQUIRED_STAKE_ADD_EVENT_STR] = 5_000_000
    settings[REQUIRED_STAKE_VALIDATE_EVENT_STR] = 50_000_000
    settings[FEE_PERCENT_STR] = 0.01
    settings[TIE_FEE_PERCENT_STR] = 0.005
    settings[EVENT_CREATOR_FEE_PERCENT_STR] = 0.1
    settings[EVENT_VALIDATOR_FEE_PERCENT_STR] = 0.5
    settings[RESERVE_FEE_PERCENT_STR] = 0.4
    settings[BURN_FEE_PERCENT_STR] = 0.0
    settings[TRUSTED_EVENT_CREATORS_STR] = []
    settings[TRUSTED_EVENT_VALIDATORS_STR] = []
    settings[BURN_ADDRESS_STR] = 'x00BURN00x'
    total_num_events.set(0)
    # Disputes
    settings[DISPUTE_DURATION_DAYS_STR] = 1
    settings[MINIMUM_DISPUTE_QUORUM_STR] = 0.2
    settings[REQUIRED_DISPUTE_APPROVAL_PERCENTAGE_STR] = 0.5
    settings[CLAIM_HOLDING_PERIOD_DAYS_STR] = 1
    # gives just under (MAX_DISPUTE_DURATION_DAYS_STR-DISPUTE_DURATION_DAYS_STR) days to file a dispute
    settings[MAX_DISPUTE_DURATION_DAYS_STR] = 3 
    dispute_id.set(0)


@export
def interact(payload: dict, state: Any, caller: str) -> Any:
    function = payload['function']
    kwargs = payload['kwargs']
    kwargs['caller'] = caller
    kwargs['state'] = state
    if function == 'validate_event':
        return validate_event(**kwargs)
    elif function == 'add_event':
        return add_event(**kwargs)
    elif function == 'place_bet':
        return place_bet(**kwargs)
    elif function == 'claim_bet':
        return claim_bet(**kwargs)
    elif function == 'create_dispute':
        return create_dispute(**kwargs)
    elif function == 'vote_dispute':
        return vote_dispute(**kwargs)
    elif function == 'determine_dispute_result':
        return determine_dispute_results(**kwargs)
    else:
        assert False, f'Invalid function: {function}'


def validate_event(event_id: int, winning_option_id: int, caller: str, state: Any):
    assert stakes[caller] >= get_setting_helper(REQUIRED_STAKE_VALIDATE_EVENT_STR), 'Not enough stake.'
    assert caller in get_setting_helper(TRUSTED_EVENT_VALIDATORS_STR), 'You are not a trusted validator.'
    assert events[event_id, 'validator'] is None, 'This event has already been validated.'
    events[event_id, 'live'] = False
    if winning_option_id == -1:
        # Tie
        bets[event_id, 'tie'] = True
    else:         
        bets[event_id, winning_option_id, 'win'] = True
    events[event_id, 'validator'] = caller
    events[event_id, 'validated_time'] = now


def add_event(metadata: dict, wager: dict, timestamp: int, caller: str, state: Any) -> str:
    # Event details
    '''
    {
        metadata: {
            name: 'Serena Williams v Naomi Osaka',            
            sport: 'Tennis',
            season: '2022',
            venue: 'Australian Open',
            description: 'Tennis / Australian Open 2022',
            league: 'WTA',
            tournament: 'Australian Open 2022',
            ... other
        }
        timestamp: int(time.time()),
        wagers: [{
            name: 'Moneyline',
            options: ['Serena Williams', 'Naomi Osaka']
        }]
    }
    '''
    assert stakes[caller] >= get_setting_helper(REQUIRED_STAKE_ADD_EVENT_STR), 'Not enough stake.'
    assert caller in get_setting_helper(TRUSTED_EVENT_CREATORS_STR), 'You are not a trusted event creator.'
    assert timestamp > get_current_time(), 'Timestamp is in the past.'
    event_id = total_num_events.get()
    events[event_id, 'metadata'] = metadata
    events[event_id, 'timestamp'] = timestamp
    events[event_id, 'live'] = True
    events[event_id, 'creator'] = caller
    events[event_id, 'wager'] = wager
    # validate wager
    assert 'name' in wager, 'Each wager must have a name.'        
    assert 'options' in wager, 'Each wager must have a list of options.'
    options = wager['options']
    assert isinstance(options, list), 'Options must be a list.'
    for option_id in range(len(options)):
        assert isinstance(options[option_id], str), 'Each option must be a string.'
    assert 'away_team' in metadata, 'away_team must be present in metadata.'
    assert 'home_team' in metadata, 'home_team must be present in metadata.'
    assert 'sport' in metadata, 'sport must be present in metadata.'
    assert 'date' in metadata, 'date must be present in metadata.'
    total_num_events.set(event_id + 1)


def place_bet(event_id: int, option_id: int, amount: float, caller: str, state: Any):
    assert amount > 0, 'Must be positive.'
    assert events[event_id, 'live'], 'This event is not live.'
    assert events[event_id, 'timestamp'] > get_current_time(), 'Event has already started.'
    I.import_module(get_setting_helper(state['TOKEN_CONTRACT_STR'])).transfer_from(
        to=ctx.this,
        amount=amount,
        main_account=caller
    )
    bets[event_id] += amount
    bets[event_id, caller] += amount
    bets[event_id, option_id] += amount
    bets[event_id, option_id, caller] += amount
    # Store bet so we can retrieve from a UI
    num_bets = bets[caller, 'num_bets'] or 0
    bets[caller, 'bet', num_bets] = event_id   
    num_bets += 1
    bets[caller, 'num_bets'] = num_bets



def claim_bet(event_id: int, option_id: int, caller: str, state: Any):
    amount = bets[event_id, option_id, caller]
    assert amount > 0, 'No amount to claim.'
    assert not events[event_id, 'live'], 'Betting is still live.'
    assert events[event_id, 'timestamp'] < get_current_time(), 'Event has not started yet.'
    validated_time = events[event_id, 'validated_time']
    assert validated_time is not None, 'Validation has not occurred yet.'
    assert (validated_time + datetime.timedelta(days=get_setting_helper(CLAIM_HOLDING_PERIOD_DAYS_STR))) <= now, "Holding period not over!"
    is_tie = bets[event_id, 'tie']
    assert is_tie or bets[event_id, option_id, 'win'], 'You did not win this bet.'
    if is_tie:        
        fee = amount * get_setting_helper(TIE_FEE_PERCENT_STR)
        payout = (amount - fee)
        handle_fees(event_id, fee, caller, state)
    else:        
        wager_total = bets[event_id]
        option_total = bets[event_id, option_id]
        other_options_total = wager_total - option_total
        payout = amount # Initial bet amount
        if other_options_total > 0:
            # Plus winnings
            ratio = other_options_total / option_total
            winnings = amount * ratio
            fee = winnings * get_setting_helper(FEE_PERCENT_STR)
            payout += (winnings - fee)
            handle_fees(event_id, fee, caller, state)
    I.import_module(get_setting_helper(state['TOKEN_CONTRACT_STR'])).transfer(
        to=caller,
        amount=payout
    )
    # Prevent reclaiming
    bets[event_id, option_id, caller] = 0


# Disputes
def create_dispute(event_id: int, current_option_id: int, expected_option_id: int, description: str, caller: str, state: Any):
    assert current_option_id != expected_option_id, 'These cannot be the same.'
    assert events[event_id, 'validator'] is not None, 'This has not been validated yet.'
    if current_option_id == -1:
        assert bets[event_id, 'tie'], 'This was not a tie.'
    else:
        assert bets[event_id, current_option_id, 'win'], 'This was not the result.'    
    amount = bets[event_id, caller]
    assert amount > 0, 'No amount in this wager.'
    p_id = dispute_id.get()
    dispute_id.set(p_id + 1)
    dispute_details[p_id, 'event_id'] = event_id
    dispute_details[p_id, "current_option_id"] = current_option_id
    dispute_details[p_id, "expected_option_id"] = expected_option_id
    modify_dispute(p_id, description, get_setting_helper(DISPUTE_DURATION_DAYS_STR))
    return p_id


def vote_dispute(p_id: int, result: bool, caller: str, state: Any): #Vote here
    dispute_sigs[p_id, caller] = result
    voters = dispute_details[p_id, "voters"] or []
    voters.append(caller)
    dispute_details[p_id, "voters"] = voters


def determine_dispute_results(p_id: int, caller: str, state: Any): #Vote resolution takes place here
    assert (dispute_details[p_id, "time"] + datetime.timedelta(days=1) * (dispute_details[p_id, "duration"])) <= now, "Proposal not over!" #Checks if proposal has concluded
    assert finished_disputes[p_id] is not True, "Proposal already resolved" #Checks that the proposal has not been resolved before (to prevent double spends)
    assert p_id < dispute_id.get()
    event_id = dispute_details[p_id, 'event_id']
    assert (events[event_id, 'validated_time'] + datetime.timedelta(days=1) * (get_setting_helper(MAX_DISPUTE_DURATION_DAYS_STR))) >= now, "Dispute took too long!" #Checks if proposal has concluded
    finished_disputes[p_id] = True #Adds the proposal to the list of resolved proposals
    approvals = 0
    total_votes = 0
    for x in dispute_details[p_id, "voters"]:
        wagered = bets[event_id, x] or 0
        staked = stakes[x] or 0
        votes = wagered + pow(staked, 0.5)
        if dispute_sigs[p_id, x] == True:
            approvals += votes
        total_votes += votes
    quorum = bets[event_id] # Total in wager
    if approvals < (quorum * get_setting_helper(MINIMUM_DISPUTE_QUORUM_STR)): #Checks that the minimum approval percentage has been reached (quorum)
        return False
    if approvals / total_votes >= get_setting_helper(REQUIRED_DISPUTE_APPROVAL_PERCENTAGE_STR): #Checks that the approval percentage of the votes has been reached (% of total votes)
        # Change result
        expected_option_id = dispute_details[p_id, "expected_option_id"]
        current_option_id = dispute_details[p_id, "current_option_id"]
        # Unset this option
        if current_option_id == -1:
            # Tie
            bets[event_id, 'tie'] = None
        else:         
            bets[event_id, current_option_id, 'win'] = None
        # Set this option
        if expected_option_id == -1:
            # Tie
            bets[event_id, 'tie'] = True
        else:         
            bets[event_id, expected_option_id, 'win'] = True
        # TODO punish validator?
        dispute_status[p_id] = True
        return True
    else:
        dispute_status[p_id] = False
        return False


# Helpers
def modify_dispute(p_id: int, description: str, voting_time_in_days: int):
    dispute_details[p_id, "dispute_creator"] = caller
    dispute_details[p_id, "description"] = description
    dispute_details[p_id, "time"] = now
    dispute_details[p_id, "duration"] = voting_time_in_days


def get_current_time():
    # https://developers.lamden.io/docs/smart-contracts/datetime-module/
    td = now - datetime.datetime(1970, 1, 1, 0, 0, 0)
    return td.seconds


def handle_fees(event_id: int, total_fee: float, caller: str, state: Any):
    reserve_balance = state['reserve_balance']
    fee_for_event_creator = total_fee * get_setting_helper(EVENT_CREATOR_FEE_PERCENT_STR)
    fee_for_event_validator = total_fee * get_setting_helper(EVENT_VALIDATOR_FEE_PERCENT_STR)
    fee_for_reserve = total_fee * get_setting_helper(RESERVE_FEE_PERCENT_STR)
    fee_for_burn = total_fee * get_setting_helper(BURN_FEE_PERCENT_STR)
    assert (fee_for_burn + fee_for_event_creator + fee_for_event_validator + fee_for_reserve) == total_fee, 'Invalid fee percentages.'
    token = I.import_module(get_setting_helper(state['TOKEN_CONTRACT_STR'])))
    if fee_for_event_creator > 0:
        creator = events[event_id, 'creator']
        if creator != caller:
            token.transfer_from(
                to=events[event_id, 'creator'],
                amount=fee_for_event_creator,
                main_account=caller,
            )
    if fee_for_event_validator > 0:
        validator = events[event_id, 'validator']
        if validator != caller:
            token.transfer_from(
                to=validator,
                amount=fee_for_event_validator,
                main_account=caller,
            )
    if fee_for_reserve > 0:
        reserve_balance.set(reserve_balance.get() + fee_for_reserve)
        token.transfer_from(
            to=ctx.owner,
            amount=fee_for_event_validator,
            main_account=caller,
        )
    if fee_for_burn > 0:
        token.transfer_from(
            to=get_setting_helper(BURN_ADDRESS_STR),
            amount=fee_for_burn,
            main_account=caller,
        )


def get_setting_helper(setting: str) -> Any:
    # Helper function that will prioritize the parent setters 
    # This makes it easier for the DAO to update settings in this child contract
    return parent_settings[setting] or settings[setting]


