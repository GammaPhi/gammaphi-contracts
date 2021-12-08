# con_gamma_phi_upgrade_v1
import con_phi_lst001 as phi_new
import con_phi as phi_old


old_phi_balances = ForeignHash(foreign_contract='con_phi', foreign_name='balances')
new_phi_balances = ForeignHash(foreign_contract='con_phi_lst001', foreign_name='balances')

owner = Variable()


@construct
def seed():
    owner.set(ctx.caller)


@export
def redeem_phi():
    purchaser = ctx.caller

    amount = old_phi_balances[purchaser]

    assert amount > 0, 'You do not have anything to redeem.'
    assert old_phi_balances[purchaser, ctx.this] > 0, 'You have not approved enough to redeem.'

    contract_balance = new_phi_balances[ctx.this]

    assert contract_balance >= amount, 'Not enough new PHI in this contract. Please contact Gamma Phi team (@gammaphi_lamden on Twitter)'

    phi_old.transfer_from(amount, ctx.this, purchaser)
    phi_new.transfer(amount, purchaser)


@export
def withdraw_phi_new(amount: float):
    error = "Negative amount is not allowed"
    assert amount > 0, error

    error = "Only owner can payout tokens"
    assert ctx.caller == owner.get(), error

    # Transfer tokens from contract to owner
    phi_new.transfer(
        amount=amount,
        to=ctx.caller)


@export
def withdraw_phi_old(amount: float):
    error = "Negative amount is not allowed"
    assert amount > 0, error

    error = "Only owner can payout tokens"
    assert ctx.caller == owner.get(), error

    # Transfer tokens from contract to owner
    phi_old.transfer(
        amount=amount,
        to=ctx.caller)

@export
def change_ownership(new_owner: str):
    assert ctx.caller == owner.get(), 'Only the owner can change ownership!'

    owner.set(new_owner)