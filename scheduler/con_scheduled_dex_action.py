# con_scheduled_action
# owner: con_scheduler
import con_scheduler as scheduler
import dex
import currency as tau

I = importlib
balances = Hash(default_value=0)
stakes = Hash(default_value=0)
lp_points = Hash(default_value=0)
schedules = Hash(default_value=None)
prices = ForeignHash(foreign_contract='dex', foreign_name='prices')


def buy(kwargs: dict, caller: str):
    contract = kwargs['contract']
    currency_amount = kwargs['currency_amount']
    minimum_received = kwargs.get('minimum_received', 0)
    token_fees = kwargs.get('token_fees', False)    
    assert currency_amount > 0, 'Amount must be positive.'
    assert balances[caller, 'currency'] >= currency_amount, 'You do not have enough funds.'
    tau.approve(
        to='dex',
        amount=currency_amount
    )
    tokens_purchased = dex.buy(
        contract=contract,
        currency_amount=currency_amount,
        minimum_received=minimum_received,
        token_fees=token_fees,
    )
    balances[caller, contract] += tokens_purchased
    balances[caller, 'currency'] -= currency_amount


def sell(kwargs: dict, caller: str):
    contract = kwargs['contract']
    token_amount = kwargs['token_amount']
    minimum_received = kwargs.get('minimum_received', 0)
    token_fees = kwargs.get('token_fees', False)
    assert token_amount > 0, 'Amount must be positive.'
    assert balances[caller, contract] >= token_amount, 'You do not have enough tokens.'
    I.import_module(contract).approve(
        to='dex',
        amount=token_amount
    )
    currency_purchased = dex.sell(
        contract=contract,
        token_amount=token_amount,
        minimum_received=minimum_received,
        token_fees=token_fees,
    )
    balances[caller, contract] -= token_amount
    balances[caller, 'currency'] += currency_purchased


def withdraw_from(kwargs: dict, caller: str):
    contract = kwargs['contract']
    amount = kwargs['amount']
    assert amount > 0, 'Amount must be positive.'
    # assert caller has balance
    assert balances[caller, contract] is not None, 'Caller does not have anything to withdraw.'
    assert amount <= balances[caller, contract], 'Caller does not have this much to withdraw.'
    I.import_module(contract).transfer(
        to=caller,
        amount=amount
    )
    balances[caller, contract] -= amount


def deposit_to(kwargs: dict, caller: str):
    contract = kwargs['contract']
    amount = kwargs['amount']
    assert amount > 0, 'Amount must be positive.'
    I.import_module(contract).transfer_from(
        to=ctx.this,
        amount=amount,
        main_account=caller,
    )
    balances[caller, contract] += amount


def cancel(caller: str):
    scheduled_uids = schedules[caller, 'scheduled_uids'] or []
    for uid in scheduled_uids:
        scheduler.cancel_scheduled_action(uid=uid)


def get_default_amm_token_contract() -> str:
    return ForeignHash(foreign_contract='dex', foreign_name='state')['TOKEN_CONTRACT']


def stake(kwargs: dict, caller: str):
    token_contract = kwargs.get('token_contract') # None is okay
    if token_contract is None:
        token_contract = get_default_amm_token_contract()
    amount = kwargs['amount']
    # Todo verify stake amounts for caller
    assert amount > 0, 'Must be a positive stake amount.'
    current_stake = stakes[caller, token_contract] or 0
    delta = (amount - current_stake)
    if delta > 0:
        # Staking more
        assert balances[caller, token_contract] >= delta, 'Not enough to stake this amount.'
        I.import_module(token_contract).approve(
            to='dex',
            amount=delta
        )      
    elif delta < 0:
        # Unstaking
        assert current_stake >= -delta, 'Not enough staked to unstake this amount.'

    dex.stake(
        amount=amount,
        token_contract=token_contract
    )  

    stakes[caller, token_contract] = amount
    balances[caller, token_contract] += delta


def add_liquidity(kwargs: dict, caller: str):
    contract = kwargs['contract']
    currency_amount = kwargs['currency_amount']
    assert currency_amount > 0, 'Amount must be positive.'
    assert balances[caller, 'currency'] >= currency_amount, 'Not enough TAU to add liquidity.'
    token_amount = currency_amount / prices[contract]
    assert balances[caller, contract] >= token_amount, 'Not enough tokens to add liquidity.'
    tau.approve(
        amount=currency_amount,
        to='dex'
    )
    I.import_module(contract).approve(
        amount=token_amount,
        to='dex'
    )
    lp_amount = dex.add_liquidity(
        contract=contract,
        currency_amount=currency_amount
    )
    lp_points[caller, contract] += lp_amount
    balances[caller, 'currency'] -= currency_amount
    balances[caller, contract] -= token_amount


def remove_liquidity(kwargs: dict, caller: str):
    contract = kwargs['contract']
    amount = kwargs['amount']
    assert amount > 0, 'Amount must be positive.'
    assert lp_points[caller, contract] > amount, 'Not enough liquidity to remove.'
    currency_amount, token_amount = dex.remove_liquidity(
        contract=contract,
        amount=amount
    )
    lp_points[caller, contract] -= amount
    balances[caller, 'currency'] += currency_amount
    balances[caller, contract] += token_amount


@export
def interact(payload: dict, caller: str):
    function = payload['function']
    kwargs = payload['kwargs']
    deposit = payload['deposit']
    schedule_interval_seconds = payload.get('schedule_interval_seconds')

    # Handle interaction
    if function == 'buy':
        buy(kwargs)
    elif function == 'sell':
        sell(kwargs)
    elif function == 'deposit':
        deposit_to(kwargs, caller)
    elif function == 'withdraw':
        withdraw_from(kwargs, caller)
    elif function == 'stake':
        stake(kwargs, caller)
    elif function == 'add_liquidity':
        add_liquidity(kwargs, caller)
    elif function == 'remove_liquidity':
        remove_liquidity(kwargs, caller)
    elif function == 'cancel':
        cancel(caller)

    # Reschedule if desired
    if (schedule_interval_seconds or 0) > 0:
        uid, rand = schedule_function(
            function=function,
            kwargs=kwargs,
            schedule_interval_seconds=schedule_interval_seconds,
            deposit=deposit
        )
        schedules[caller, rand] = uid
        scheduled_uids = schedules[caller, 'scheduled_uids'] or []
        scheduled_uids.append(uid)
        schedules[caller, 'scheduled_uids'] = scheduled_uids

    # Remove uid from scheduled_uids
    rand = kwargs.get('rand')
    if rand is not None:
        uid = schedules[caller, rand]
        if uid is not None:
            scheduled_uids = schedules[caller, 'scheduled_uids'] or []
            scheduled_uids.remove(uid)
            schedules[caller, 'scheduled_uids'] = scheduled_uids


def schedule_function(function: str, kwargs: dict, schedule_interval_seconds: int, deposit: int) -> tuple:
    current_time = scheduler.get_timestamp()
    rand = random.randint(0, 9999999)
    uid = scheduler.schedule_action(
        action={
            'payload': {
                'function': function,
                'kwargs': kwargs,       
                'deposit': deposit, 
                'rand': rand,
                'schedule_interval_seconds': schedule_interval_seconds        
            },
            'contract': ctx.this
        },
        run_at=current_time + schedule_interval_seconds,
        deposit=deposit,
    )
    return uid, rand
