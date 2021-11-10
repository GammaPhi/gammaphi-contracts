import currency as tau
import con_eh_game_token_1 as phi

tau_balances = ForeignHash(foreign_contract='currency', foreign_name='balances')
phi_balances = ForeignHash(foreign_contract='con_eh_game_token_1', foreign_name='balances')

owner = Variable()

round_1_price = Variable()
round_1_quantity = Variable()

round_2_price = Variable()
round_2_quantity = Variable()

min_bet = Variable()
max_bet = Variable()

wheel_multipliers = Variable()

random.seed()

@construct
def seed():
    min_bet.set(1)
    max_bet.set(1000)
    round_1_price.set(0.01)
    round_1_quantity.set(50_000_000)
    round_2_price.set(0.05)
    round_2_quantity.set(50_000_000)
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
def purchase_round_1(amount_tau: float):
    assert amount_tau > 0, 'Cannot purchase negative amounts!'
    purchaser = ctx.caller

    assert tau_balances[purchaser] >= amount_tau, 'Not enough tau!'

    amount = amount_tau / round_1_price.get()

    assert round_1_quantity.get() > amount, 'Not enough remaining in round 1'

    round_1_quantity.set(round_1_quantity.get() - amount)

    tau.transfer_from(amount_tau, owner.get(), purchaser)
    phi.transfer(amount, purchaser)

@export
def purchase_round_2(amount_tau: float):
    assert amount_tau > 0, 'Cannot purchase negative amounts!'
    purchaser = ctx.caller

    assert tau_balances[purchaser] >= amount_tau, 'Not enough tau!'

    amount = amount_tau / round_2_price.get()

    assert round_2_quantity.get() > amount, 'Not enough remaining in round 1'

    round_2_quantity.set(round_2_quantity.get() - amount)

    tau.transfer_from(amount_tau, owner.get(), purchaser)
    phi.transfer(amount, purchaser)

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