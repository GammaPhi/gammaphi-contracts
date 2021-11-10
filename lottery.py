import currency as tau
import con_eh_game_token_1 as phi

phi_balances = ForeignHash(foreign_contract='con_eh_game_token_1', foreign_name='balances')

owner = Variable()

user_list = Variable()
ticket_list = Variable()
total = Variable()

balances = Hash(default_value=0)

random.seed()

@construct
def seed():
    user_list.set([])
    ticket_list.set([])
    total.set(0)
    owner.set(ctx.caller)

@export
def deposit_phi(amount: int):
    # 1 PHI == 1 lottery ticket
    assert phi_balances[ctx.caller] >= amount, 'Insufficient funds!'

    total.set(total.get() + amount)

    users = user_list.get()
    tickets = ticket_list.get()

    users.append(ctx.caller)
    tickets.append(total.get())

    user_list.set(users)
    ticket_list.set(tickets)

    balances[ctx.caller] += amount

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
    tickets = ticket_list.get()

    winner = None

    for i in range(len(users)):
        if lucky_number < tickets[i]:
            winner = users[i]
            break

    assert winner is not None, 'Unable to draw a valid user'

    # Clear previous state
    distinct_users = set(users)
    for user in distinct_users:
        balances[user] = 0

    user_list.set([])
    ticket_list.set([])

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