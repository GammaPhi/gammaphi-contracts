# con_gamma_phi_lottery_v2
import currency as tau
import con_phi_lst001 as phi

phi_balances = ForeignHash(foreign_contract='con_phi_lst001', foreign_name='balances')

owner = Variable()

user_list = Variable()
total = Variable()

balances = Hash(default_value=0)

random.seed()

@construct
def seed():
    user_list.set([])
    total.set(0)
    owner.set(ctx.caller)

@export
def deposit_phi(amount: int):
    # 1 PHI == 1 lottery ticket
    assert phi_balances[ctx.caller] >= amount, 'Insufficient funds!'

    users = set(user_list.get())

    users.add(ctx.caller)

    user_list.set(list(users))

    balances[ctx.caller] += amount

    total.set(total.get() + amount)

    phi.transfer_from(
        amount=amount,
        to=ctx.this,
        main_account=ctx.caller)

@export
def draw_winner():
    error = "Only the owner can draw a winner"
    assert owner.get() == ctx.caller, error

    total_tickets = total.get()

    assert total_tickets > 0, "There is nothing to draw!"

    lucky_number = random.randint(0, total_tickets-1)

    users = user_list.get()

    winner = None

    amount = 0

    for user in users:
        amount += balances[user]
        if lucky_number < amount:
            winner = user
            break

    assert winner is not None, 'Unable to draw a valid user'

    # Clear previous state
    for user in users:
        balances[user] = 0

    user_list.set([])
    total.set(0)

    # Send out prize
    phi.transfer(
        amount=total_tickets,
        to=winner)

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