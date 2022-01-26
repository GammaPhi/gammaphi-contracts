# con_scheduler
import currency as tau
I = importlib

# Main variables
S = Hash(default_value=None)
total = Variable()


# Policy interface
action_interface = [
    I.Func('interact', args=('payload', 'caller')),
]


@construct
def init():
    total.set(0)


@export
def get_timestamp():
    # https://developers.lamden.io/docs/smart-contracts/datetime-module/
    td = now - datetime.datetime(1970, 1, 1, 0, 0, 0)
    return td.seconds


def assert_valid_action(action: dict):
    assert 'contract' in action, 'Please specify a contract in your action.'
    assert 'payload' in action, 'Please specify a payload object in your action.'
    # Attempt to import the contract to make sure it is already submitted
    p = I.import_module(action['contract'])

    # Assert ownership is election_house and interface is correct
    assert I.owner_of(p) == ctx.this, \
        'This contract must control the action contract!'

    assert I.enforce_interface(p, action_interface), \
        'Action contract does not follow the correct interface!'



@export
def schedule_action(action: dict, run_at: int, deposit: float) -> int:
    # Assertions
    assert_valid_action(action)
    assert deposit > 0, 'Deposit must be positive.'
    
    # Make sure in the future
    assert run_at > get_timestamp(), 'Cannot schedule a action in the past.'

    # Get next id
    uid = total.get()

    # Transfer TAU from caller
    tau.transfer_from(
        to=ctx.this,
        amount=deposit,
        main_account=ctx.caller
    )

    # Set state
    S[uid, 'action'] = action
    S[uid, 'run_at'] = run_at
    S[uid, 'deposit'] = deposit
    S[uid, 'completed'] = False
    S[uid, 'caller'] = ctx.caller
    total.set(uid + 1)

    return uid
    

@export
def cancel_scheduled_action(uid: int):
    deposit = S[uid, 'deposit']
    assert deposit is not None, 'This action does not exist.'
    assert S[uid, 'caller'] == ctx.caller, 'This is not your action.'
    S[uid, 'completed'] = True
    S[uid, 'cancelled'] = True
    # Return deposit to caller
    tau.transfer(
        to=ctx.caller,
        amount=S[uid, 'deposit']
    )


def run_action(action: dict, caller: str):
    # Import contract
    contract = I.import_module(action['contract'])

    # Run method
    contract.interact(        
        payload=action['payload'],
        caller=action
    )


@export
def execute_action(action: dict):    
    # Assertions
    assert_valid_action(action)

    # Run action
    run_action(
        action=action, 
        caller=ctx.caller
    )

    # Return deposit to caller
    tau.transfer(
        to=ctx.caller,
        amount=S[uid, 'deposit']
    )


@export
def execute_scheduled_action(uid: int):
    action = S[uid, 'action']
    
    # Assertions
    assert action is not None, 'This uid does not exist.'
    assert not S[uid, 'completed'], 'This action has already been run.'
    assert S[uid, 'run_at'] >= get_timestamp(), 'This action is not ready to run.'

    # Run method
    run_action(        
        payload=action['payload'],
        caller=S[uid, 'caller']
    )

    # Return deposit to caller
    tau.transfer(
        to=ctx.caller,
        amount=S[uid, 'deposit']
    )

    # Update state
    S[uid, 'completed'] = True