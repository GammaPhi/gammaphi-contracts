import currency as tau
import con_phi as phi

tau_balances = ForeignHash(foreign_contract='currency', foreign_name='balances')

owner = Variable()

round_1_price = Variable()
round_1_quantity = Variable()

round_2_price = Variable()
round_2_quantity = Variable()


@construct
def seed():
    round_1_price.set(0.002)
    round_1_quantity.set(100_000_000)
    round_2_price.set(0.004)
    round_2_quantity.set(100_000_000)
    owner.set(ctx.caller)


@export
def set_round_1_price(price: float):
    error = "Only owner can update this"
    assert ctx.caller == owner.get(), error

    round_1_price.set(price)


@export
def set_round_2_price(price: float):
    error = "Only owner can update this"
    assert ctx.caller == owner.get(), error

    round_2_price.set(price)


@export
def set_round_1_quantity(quantity: int):
    error = "Only owner can update this"
    assert ctx.caller == owner.get(), error

    round_1_quantity.set(quantity)


@export
def set_round_2_quantity(quantity: int):
    error = "Only owner can update this"
    assert ctx.caller == owner.get(), error

    round_2_quantity.set(quantity)


@export
def purchase_round_1(amount_tau: float):
    assert amount_tau > 0, 'Cannot purchase negative amounts!'
    purchaser = ctx.caller

    assert tau_balances[purchaser] >= amount_tau, 'Not enough tau!'

    amount = amount_tau / round_1_price.get()

    assert round_1_quantity.get() > amount, 'Not enough remaining in round 1'

    round_1_quantity.set(round_1_quantity.get() - amount)

    tau.transfer_from(amount_tau, ctx.this, purchaser)
    phi.transfer(amount, purchaser)


@export
def purchase_round_2(amount_tau: float):
    assert amount_tau > 0, 'Cannot purchase negative amounts!'
    purchaser = ctx.caller

    assert tau_balances[purchaser] >= amount_tau, 'Not enough tau!'

    amount = amount_tau / round_2_price.get()

    assert round_2_quantity.get() > amount, 'Not enough remaining in round 1'

    round_2_quantity.set(round_2_quantity.get() - amount)

    tau.transfer_from(amount_tau, ctx.this, purchaser)
    phi.transfer(amount, purchaser)

@export
def pay_out_phi(amount: float):
    error = "Negative amount is not allowed"
    assert amount > 0, error

    error = "Only owner can payout tokens"
    assert ctx.caller == owner.get(), error

    # Transfer tokens from contract to owner
    phi.transfer(
        amount=amount,
        to=ctx.caller)

@export
def pay_out_tau(amount: float):
    error = "Negative amount is not allowed"
    assert amount > 0, error

    error = "Only owner can payout tokens"
    assert ctx.caller == owner.get(), error

    # Transfer tokens from contract to owner
    tau.transfer(
        amount=amount,
        to=ctx.caller)