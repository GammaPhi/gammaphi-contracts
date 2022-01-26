# con_sports_betting

# Imports
I = importlib


# State
settings = Hash(default_value=None)
stakes = Hash(default_value=0)
reserve_balance = Variable()
total_staked = Variable()


# DAO
proposal_id = Variable()
finished_proposals = Hash()
sig = Hash(default_value=False)
proposal_details = Hash()
status = Hash()


# Constants
TOKEN_CONTRACT_STR = 'token'
OWNER_STR = 'owner'
MINIMUM_PROPOSAL_DURATION_STR = 'min_proposal_duration'
REQUIRED_APPROVAL_PERCENTAGE_STR = 'required_approval_percentage'
MINIMUM_QUORUM_STR = 'min_quorum'
STAKING_LOCKUP_DAYS_STR = 'stake_lockup'


# Actions
metadata = Hash(default_value=None)
contracts_list = Variable()
state = {
    'stakes': stakes, # should this be read only?
    'settings': settings, # should this be read only?
    'metadata': metadata,
    'reserve_balance': reserve_balance,
    'total_staked': total_staked,
    'TOKEN_CONTRACT_STR': TOKEN_CONTRACT_STR,
    'OWNER_STR': OWNER_STR,
    'MINIMUM_PROPOSAL_DURATION_STR': MINIMUM_PROPOSAL_DURATION_STR,
    'REQUIRED_APPROVAL_PERCENTAGE_STR': REQUIRED_APPROVAL_PERCENTAGE_STR,
    'MINIMUM_QUORUM_STR': MINIMUM_QUORUM_STR,
    'STAKING_LOCKUP_DAYS_STR': STAKING_LOCKUP_DAYS_STR,
}
actions = Hash()


# Action interface
action_interface = [
    I.Func('interact', args=('payload', 'state', 'caller')),
]


@construct
def init(token_contract: str = 'con_phi_lst001'):
    settings[OWNER_STR] = ctx.caller
    settings[TOKEN_CONTRACT_STR] = token_contract

    settings[STAKING_LOCKUP_DAYS_STR] = 14
    reserve_balance.set(0)
    total_staked.set(0)
    contracts_list.set([])

    # DAO
    proposal_id.set(0)
    settings[MINIMUM_PROPOSAL_DURATION_STR] = 7 #Number is in days
    settings[REQUIRED_APPROVAL_PERCENTAGE_STR] = 0.5 #Keep this at 50%, unless there are special circumstances
    settings[MINIMUM_QUORUM_STR] = 0.1 #Set minimum amount of votes needed


def register_action(action: str, contract: str):
    assert actions[action] is None, 'Action already registered!'
    # Attempt to import the contract to make sure it is already submitted
    p = I.import_module(contract)

    # Assert ownership is election_house and interface is correct
    assert I.owner_of(p) == ctx.this, \
        'This contract must control the action contract!'

    assert I.enforce_interface(p, action_interface), \
        'Action contract does not follow the correct interface!'

    contracts = contracts_list.get()
    contracts.append(contract)
    contracts_list.set(contracts)
    actions[action] = contract


def override_action(action: str, contract: str):
    original_contract = actions[action]
    assert original_contract is not None, 'Action not already registered!'
    # Attempt to import the contract to make sure it is already submitted
    p = I.import_module(contract)

    # Assert ownership is election_house and interface is correct
    assert I.owner_of(p) == ctx.this, \
        'This contract must control the action contract!'

    assert I.enforce_interface(p, action_interface), \
        'Action contract does not follow the correct interface!'

    contracts = contracts_list.get()
    if original_contract in contracts:
        contracts.remove(original_contract)
    contracts.append(contract)
    contracts_list.set(contracts)
    actions[action] = contract


def unregister_action(action: str):
    contract = actions[action]
    assert contract is not None, 'Action does not exist!'

    contracts = contracts_list.get()
    if contract in contracts:
        contracts.remove(contract)
    contracts_list.set(contracts)
    actions[action] = None


# Do not export this one
def interact_internal(action: str, payload: dict, caller: str) -> Any:
    contract = actions[action]
    assert contract is not None, 'Invalid action!'

    module = I.import_module(contract)

    result = module.interact(payload, state, caller)
    return result


@export # Safe to export
def interact(action: str, payload: dict) -> Any:
    return interact_internal(action, payload, ctx.caller)


# Do not export this one
def bulk_interact_internal(action: str, payloads: list, caller: str):
    for payload in payloads:
        interact_internal(action, payload, caller)


@export # Safe to export
def bulk_interact(action: str, payloads: list):
    for payload in payloads:
        interact(action, payload)


@export
def force_change_setting(key: str, value: Any, to_float: bool = False):
    assert ctx.caller == settings[OWNER_STR], 'Only the owner can directly change settings.'
    if to_float:
        value = float(value)
    settings[key] = value


@export
def stake(amount: float):
    assert amount > 0, 'Must be positive.'
    current_amount = stakes[ctx.caller] or 0
    if current_amount > amount:
        # unstake
        assert (stakes[ctx.caller, 'time'] + datetime.timedelta(days=1) * (settings[STAKING_LOCKUP_DAYS_STR])) <= now, "Cannot unstake yet!"
        amount_to_unstake = current_amount - amount
        I.import_module(settings[TOKEN_CONTRACT_STR]).transfer(
            to=ctx.caller,
            amount=amount_to_unstake
        )
        total_staked.set(total_staked.get() - amount_to_unstake)
    elif current_amount < amount:
        # stake
        amount_to_stake = amount - current_amount
        I.import_module(settings[TOKEN_CONTRACT_STR]).transfer_from(
            to=ctx.this,
            amount=amount_to_stake,
            main_account=ctx.caller
        )
        stakes[ctx.caller, 'time'] = now
        total_staked.set(total_staked.get() + amount_to_stake)
    stakes[ctx.caller] = amount


@export
def create_register_action_proposal(action: str, contract: str, voting_time_in_days: int, description: str): 
    assert voting_time_in_days >= settings[MINIMUM_PROPOSAL_DURATION_STR]
    p_id = proposal_id.get()
    proposal_id.set(p_id + 1)
    proposal_details[p_id, "action"] = action
    proposal_details[p_id, "contract"] = contract
    proposal_details[p_id, "type"] = "register_action"
    modify_proposal(p_id, description, voting_time_in_days)
    return p_id


@export
def create_override_action_proposal(action: str, contract: str, voting_time_in_days: int, description: str): 
    assert voting_time_in_days >= settings[MINIMUM_PROPOSAL_DURATION_STR]
    p_id = proposal_id.get()
    proposal_id.set(p_id + 1)
    proposal_details[p_id, "action"] = action
    proposal_details[p_id, "contract"] = contract
    proposal_details[p_id, "type"] = "override_action"
    modify_proposal(p_id, description, voting_time_in_days)
    return p_id


@export
def create_unregister_action_proposal(action: str, voting_time_in_days: int, description: str): 
    assert voting_time_in_days >= settings[MINIMUM_PROPOSAL_DURATION_STR]
    p_id = proposal_id.get()
    proposal_id.set(p_id + 1)
    proposal_details[p_id, "action"] = action
    proposal_details[p_id, "type"] = "unregister_action"
    modify_proposal(p_id, description, voting_time_in_days)
    return p_id


@export
def create_interact_proposal(action: str, payload: dict, voting_time_in_days: int, description: str, caller: str = None): 
    assert voting_time_in_days >= settings[MINIMUM_PROPOSAL_DURATION_STR]
    p_id = proposal_id.get()
    proposal_id.set(p_id + 1)
    proposal_details[p_id, "action"] = action
    proposal_details[p_id, "payload"] = payload
    if caller is not None:
        proposal_details[p_id, "caller"] = caller
    proposal_details[p_id, "type"] = "interact"
    modify_proposal(p_id, description, voting_time_in_days)
    return p_id


@export
def create_bulk_interact_proposal(action: str, payloads: dict, voting_time_in_days: int, description: str, caller: str = None): 
    assert voting_time_in_days >= settings[MINIMUM_PROPOSAL_DURATION_STR]
    p_id = proposal_id.get()
    proposal_id.set(p_id + 1)
    proposal_details[p_id, "action"] = action
    proposal_details[p_id, "payloads"] = payloads
    if caller is not None:
        proposal_details[p_id, "caller"] = caller
    proposal_details[p_id, "type"] = "bulk_interact"
    modify_proposal(p_id, description, voting_time_in_days)
    return p_id


@export
def create_change_setting_proposal(setting: str, value: Any, voting_time_in_days: int, description: str, to_float: bool = False): 
    assert voting_time_in_days >= settings[MINIMUM_PROPOSAL_DURATION_STR]
    p_id = proposal_id.get()
    proposal_id.set(p_id + 1)
    if to_float:
        value = float(value)
    proposal_details[p_id, "setting"] = setting
    proposal_details[p_id, "value"] = value
    proposal_details[p_id, "type"] = "change_setting"
    modify_proposal(p_id, description, voting_time_in_days)
    return p_id


@export
def create_transfer_proposal(token_contract: str, amount: float, to: str, description: str, voting_time_in_days: int): #Transfer tokens held by the AMM treasury here
    assert voting_time_in_days >= settings[MINIMUM_PROPOSAL_DURATION_STR]
    p_id = proposal_id.get()
    proposal_id.set(p_id + 1)
    proposal_details[p_id, "token_contract"] = token_contract
    proposal_details[p_id, "amount"] = amount
    proposal_details[p_id, "receiver"] = to
    proposal_details[p_id, "type"] = "transfer"
    modify_proposal(p_id, description, voting_time_in_days)
    return p_id


@export
def create_approval_proposal(token_contract: str, amount: float, to: str, description: str, voting_time_in_days: int): #Approve the transfer of tokens held by the AMM treasury here
    assert voting_time_in_days >= settings[MINIMUM_PROPOSAL_DURATION_STR]
    p_id = proposal_id.get()
    proposal_id.set(p_id + 1)
    proposal_details[p_id, "token_contract"] = token_contract
    proposal_details[p_id, "amount"] = amount
    proposal_details[p_id, "receiver"] = to
    proposal_details[p_id, "type"] = "approval"
    modify_proposal(p_id, description, voting_time_in_days)
    return p_id


@export
def vote(p_id: int, result: bool): #Vote here
    sig[p_id, ctx.caller] = result
    voters = proposal_details[p_id, "voters"] or []
    voters.append(ctx.caller)
    proposal_details[p_id, "voters"] = voters


@export
def determine_results(p_id: int): #Vote resolution takes place here
    assert (proposal_details[p_id, "time"] + datetime.timedelta(days=1) * (proposal_details[p_id, "duration"])) <= now, "Proposal not over!" #Checks if proposal has concluded
    assert finished_proposals[p_id] is not True, "Proposal already resolved" #Checks that the proposal has not been resolved before (to prevent double spends)
    assert p_id < proposal_id.get()
    finished_proposals[p_id] = True #Adds the proposal to the list of resolved proposals
    approvals = 0
    total_votes = 0
    for x in proposal_details[p_id, "voters"]:
        stake = stakes[x] or 0
        if sig[p_id, x] == True:
            approvals += stake
        total_votes += stake
    quorum = total_staked.get()
    if approvals < (quorum * settings[MINIMUM_QUORUM_STR]): #Checks that the minimum approval percentage has been reached (quorum)
        return False
    if approvals / total_votes >= settings[REQUIRED_APPROVAL_PERCENTAGE_STR]: #Checks that the approval percentage of the votes has been reached (% of total votes)
        if proposal_details[p_id, "type"] == "transfer": 
            t_c = I.import_module(proposal_details[p_id, "token_contract"])
            t_c.transfer(proposal_details[p_id, "amount"], proposal_details[p_id, "receiver"])
        elif proposal_details[p_id, "type"] == "approval":
            t_c = I.import_module(proposal_details[p_id, "token_contract"])
            t_c.approve(proposal_details[p_id, "amount"], proposal_details[p_id, "receiver"])
        elif proposal_details[p_id, "type"] == "register_action":
            register_action(
                action=proposal_details[p_id, "action"],
                contract=proposal_details[p_id, "contract"]
            )
        elif proposal_details[p_id, "type"] == "unregister_action":
            unregister_action(
                action=proposal_details[p_id, "action"],
            )
        elif proposal_details[p_id, "type"] == "override_action":
            override_action(
                action=proposal_details[p_id, "action"],
                contract=proposal_details[p_id, "contract"]
            )
        elif proposal_details[p_id, "type"] == "interact":
            interact_internal(
                action=proposal_details[p_id, "action"],
                payload=proposal_details[p_id, "payload"],
                caller=proposal_details[p_id, "caller"] or ctx.this,
            )
        elif proposal_details[p_id, "type"] == "bulk_interact":
            bulk_interact_internal(
                action=proposal_details[p_id, "action"],
                payloads=proposal_details[p_id, "payloads"],
                caller=proposal_details[p_id, "caller"] or ctx.this,
            )
        elif proposal_details[p_id, "type"] == "change_setting":
            # allowlist settings?
            settings[proposal_details[p_id, "setting"]] = proposal_details[p_id, "value"]
        status[p_id] = True
        return True
    else:
        status[p_id] = False
        return False


@export 
def proposal_information(p_id: int): #Get proposal information, provided as a dictionary
    info =	{
        "setting": proposal_details[p_id, "setting"],
        "value": proposal_details[p_id, "value"],
        "token_contract": proposal_details[p_id, "token_contract"],
        "proposal_creator": proposal_details[p_id, "proposal_creator"],
        "description": proposal_details[p_id, "description"],
        "time": proposal_details[p_id, "time"],
        "type": proposal_details[p_id, "type"],
        "duration": proposal_details[p_id, "duration"],
        "receiver": proposal_details[p_id, "receiver"]
    }
    return info


def modify_proposal(p_id: int, description: str, voting_time_in_days: int):
    proposal_details[p_id, "proposal_creator"] = ctx.caller
    proposal_details[p_id, "description"] = description
    proposal_details[p_id, "time"] = now
    proposal_details[p_id, "duration"] = voting_time_in_days

