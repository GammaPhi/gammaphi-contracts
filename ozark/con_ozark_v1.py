# con_ozark_v1

denomination = Variable()
total_deposit_balance = Variable()
token_contract = Variable()
merkle_tree_contract = Variable()
verifier_contract = Variable()
commitments = Hash(default_value=None)
nullifier_hashes = Hash(default_value=None)
I = importlib


@construct
def init():
    # Set variables
    token_contract.set('con_phi_lst001')
    merkle_tree_contract.set('con_merkle_tree_v1')
    verifier_contract.set('con_verifier_v1')
    total_deposit_balance.set(0)
    denomination.set(1000)


@export
def deposit(commitment: str):
    assert commitments[commitment] is None, 'The commitment has been submitted.'
    I.import_module(merkle_tree_contract.get()).insert(commitment)
    commitments[commitment] = True
    process_deposit(ctx.caller)    


def process_deposit(caller: str):
    amount = denomination.get()
    I.import_module(token_contract.get()).transfer_from(
        to=ctx.this,
        amount=amount,
        main_account=caller
    )
    total_deposit_balance.set(total_deposit_balance.get() + amount)


@export
def withdraw(a: list, b: list, c: list, root: str, nullifier_hash: str, recipient: str, relayer: str = '0', fee: str = '0', refund: str = '0'):
    assert int(fee) < denomination.get(), 'Fee exceeds transfer value.'
    assert nullifier_hashes[nullifier_hash] is None, 'The note has already been spent.'
    merkle_tree = I.import_module(merkle_tree_contract.get())
    assert merkle_tree.is_known_root(root), 'Cannot find your merkle root.'
    verifier = I.import_module(verifier_contract.get())
    assert verifier.verify_proof(
        a=a, b=b, c=c,
        inputs=[
            int(root, 10), 
            int(nullifier_hash, 10),
            int(recipient, 10),
            int(relayer, 10),
            int(fee, 10),
            int(refund, 10),
        ],
    ), 'Invalid withdraw proof.'

    nullifier_hashes[nullifier_hash] = True

    process_withdraw(recipient, relayer, int(fee, 10), int(refund, 10))


def process_withdraw(recipient: str, relayer: str, fee: int, refund: int):
    assert refund == 0, 'Refund not supported.'

    amount = denomination.get() - fee
    assert amount > 0, 'Nothing to withdraw.'

    token = I.import_module(token_contract.get())

    token.transfer(
        to=recipient,
        amount=amount
    )

    if fee > 0:
        token.transfer(
            to=relayer,
            amount=fee
        )

    total_deposit_balance.set(total_deposit_balance.get() - (amount + fee))

