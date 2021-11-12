import currency as tau
import con_phi as phi

tau_balances = ForeignHash(foreign_contract='currency', foreign_name='balances')
phi_balances = ForeignHash(foreign_contract='con_phi', foreign_name='balances')

owner = Variable()

min_bet = Variable()
max_bet = Variable()

wheel_multipliers = Variable()

random.seed()

@construct
def seed():
    min_bet.set(1)
    max_bet.set(1000)
    wheel_multipliers.set([10, 1, 0, 2, 0, 3, 0, 0, 0, 1, 0, 0, 0, 2, 0, 0, 0, 1, 0, 1, 0, 3, 0, 0])
    owner.set(ctx.caller)

@export
def flip_phi(amount: float, odds: float = 0.5):
    assert odds >= 0.001, 'Odds must be >= 0.001'
    assert odds <= 0.999, 'Odds must be <= 0.999'
    assert phi_balances[ctx.caller] >= amount, 'Insufficient funds!'
    assert amount >= min_bet.get(), f'Must bet at least {min_bet.get()}'
    assert amount <= max_bet.get(), f'Cannot bet more than {max_bet.get()}'
    payout = amount / odds
    assert payout - amount < phi_balances[ctx.this], f'Not enough money in the bank :('
    phi.transfer_from(amount=amount, to=ctx.this, main_account=ctx.caller)
    r = random.randint(0, 999)
    if r < odds * 1000:
        phi.transfer(amount=payout, to=ctx.caller)

@export
def spin_wheel(amount: float):
    assert phi_balances[ctx.caller] >= amount, 'Insufficient funds!'
    assert amount >= min_bet.get(), f'Must bet at least {min_bet.get()}'
    assert amount <= max_bet.get(), f'Cannot bet more than {max_bet.get()}'
    multipliers = wheel_multipliers.get()
    max_payout = amount * max(multipliers)
    assert max_payout - amount < phi_balances[ctx.this], f'Not enough money in the bank :('
    phi.transfer_from(amount=amount, to=ctx.this, main_account=ctx.caller)
    num = len(multipliers)
    lucky_spin = random.randint(0, num-1)
    multiplier = multipliers[lucky_spin]
    if multiplier > 0:
        phi.transfer(amount=multiplier * amount, to=ctx.caller)
    return lucky_spin

@export
def roll_dice(amount: float):
    assert phi_balances[ctx.caller] >= amount, 'Insufficient funds!'
    assert amount >= min_bet.get(), f'Must bet at least {min_bet.get()}'
    assert amount <= max_bet.get(), f'Cannot bet more than {max_bet.get()}'
    
    n_dice = 5

    multi_5_kind = 185.14285714285717
    multi_4_kind = multi_5_kind * (6.0/150.0)
    multi_full_house = multi_5_kind * (6.0/300.0)
    multi_3_kind = multi_5_kind * (6.0/1200.0)
    multi_2_pair = multi_5_kind * (6.0/1800.0)
    multi_2_kind = multi_5_kind * (6.0/3600.0)
    multi_straight = multi_5_kind * (6.0/720.0)
    

    max_payout = amount * multi_5_kind

    assert max_payout - amount < phi_balances[ctx.this], f'Not enough money in the bank :('

    phi.transfer_from(amount=amount, to=ctx.this, main_account=ctx.caller)

    rolls = []

    for i in range(n_dice):
        rolls.append(random.randint(1, 6))

    unique = set(rolls)

    n_unique = len(unique)

    count_map = {x: rolls.count(x) for x in unique}
    counts = list(count_map.values())

    if n_unique == n_dice:
        # Straight
        multiplier = multi_straight
    elif n_unique == 1:
        # 5 of a kind
        multiplier = multi_5_kind
    elif n_unique == 2:
        # Check
        if max(counts) == 4:
            # 4 of a kind
            multiplier = multi_4_kind
        else:
            # Full house       
            multiplier = multi_full_house
    elif n_unique == 3:
        if max(counts) == 3:
            # 3 of a kind
            multiplier = multi_3_kind
        else:
            # 2 pair
            multiplier = multi_2_pair
    else:
        # single pair
        multiplier = multi_2_kind

    if multiplier > 0:
        phi.transfer(amount=multiplier * amount, to=ctx.caller)

    return rolls

@export
def set_wheel_multipliers(multipliers: list):
    error = "Only the owner can adjust the min amount"
    assert owner.get() == ctx.caller, error
    wheel_multipliers.set(multipliers)

@export
def set_min(amount: int):
    error = "Only the owner can adjust the min amount"
    assert owner.get() == ctx.caller, error
    min_bet.set(amount)

@export
def set_max(amount: int):
    error = "Only the owner can adjust the max amount"
    assert owner.get() == ctx.caller, error
    max_bet.set(amount)


@export
def change_ownership(new_owner: str):
    assert ctx.caller == owner.get(), 'Only the owner can change ownership!'

    owner.set(new_owner)

@export
def pay_out(amount: float):
    error = "Negative amount is not allowed"
    assert amount > 0, error

    error = "Only owner can payout tokens"
    assert ctx.caller == owner.get(), error

    # Transfer tokens from contract to owner
    phi.transfer(
        amount=amount,
        to=ctx.caller)