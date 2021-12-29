# con_game_manager_v1

import con_phi_lst001 as phi
I = importlib

owner = Variable()
metadata = Hash(default_value=None)
contracts_list = Variable()
actions = Hash()

S = {
    'metadata': metadata,
    'owner': owner
}

# Policy interface
action_interface = [
    I.Func('interact', args=('payload', 'state', 'caller')),
]


@construct
def seed():
    owner.set(ctx.caller)
    contracts_list.set([])


@export
def register_action(action: str, contract: str):
    assert ctx.caller == owner.get(), 'Only owner can call!'
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


@export
def override_action(action: str, contract: str):
    assert ctx.caller == owner.get(), 'Only owner can call!'
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


@export
def unregister_action(action: str):
    assert ctx.caller == owner.get(), 'Only owner can call!'
    contract = actions[action]
    assert contract is not None, 'Action does not exist!'

    contracts = contracts_list.get()
    if contract in contracts:
        contracts.remove(contract)
    contracts_list.set(contracts)
    actions[action] = None


@export
def interact(action: str, payload: dict) -> Any:
    contract = actions[action]
    assert contract is not None, 'Invalid action!'

    module = I.import_module(contract)

    result = module.interact(payload, S, ctx.caller)
    return result

@export
def bulk_interact(action: str, payloads: list):
    for payload in payloads:
        interact(action, payload)


@export
def change_ownership(new_owner: str):
    assert ctx.caller == owner.get(), 'Only the owner can change ownership!'

    owner.set(new_owner)


@export
def force_withdraw(player: str, amount: float):
    assert ctx.caller in contracts_list.get(), 'You cannot call this method.'
    phi.transfer(
        amount=amount,
        to=player
    )

@export
def force_deposit(main_account: str, amount: float):
    assert ctx.caller in contracts_list.get(), 'You cannot call this method.'
    phi.transfer_from(
        to=ctx.this,
        amount=amount,
        main_account=main_account
    )