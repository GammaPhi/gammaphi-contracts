import con_tumbler_verifier_v1 as verifier


current_root_index = Variable()
next_index = Variable()
levels = Variable()
roots_var = Variable()
zeros_var = Variable()
filled_subtrees_var = Variable()

ROOT_HISTORY_SIZE = 100
FIELD_SIZE = 21888242871839275222246405745257275088548364400416034343698204186575808495617
ZERO_VALUE = 21663839004416932945382355908790599225266501822907911457504978515578255421292


nullifier_hashes = Hash(default_value=None)
commitments = Hash(default_value=None)
denomination = Variable()
total_deposit_balance = Variable()
token_contract = Variable()
I = importlib


@construct
def init(tree_levels: int = 24):
    assert tree_levels > 0, 'tree_levels should be greater than zero'
    assert tree_levels < 32, 'tree_levels should be less than 32'
    filled_subtrees = []
    roots = [None] * ROOT_HISTORY_SIZE
    zeros = []

    current_zero = str(ZERO_VALUE)
    zeros.append(current_zero)
    filled_subtrees.append(current_zero)

    for i in range(1, tree_levels):
        current_zero = hash_left_right(current_zero, current_zero)
        zeros.append(current_zero)
        filled_subtrees.append(current_zero)

    roots[0] = hash_left_right(current_zero, current_zero)

    # Set variables
    current_root_index.set(0)
    next_index.set(0)
    levels.set(tree_levels)
    roots_var.set(roots)
    zeros_var.set(zeros)
    filled_subtrees_var.set(filled_subtrees)

    token_contract.set('con_phi_lst001')
    total_deposit_balance.set(0)
    denomination.set(1000)


def hash_left_right(left: str, right: str) -> str:
    return hashlib.sha256(str(left) + str(right))


@export
def insert(leaf: str) -> int:
    current_index = next_index.get()
    filled_subtrees = filled_subtrees_var.get()
    roots = roots_var.get()
    zeros = zeros_var.get()

    current_level_hash = str(leaf)

    for i in range(levels.get()):
        if current_index % 2 == 0:
            left = current_level_hash
            right = zeros[i]
            filled_subtrees[i] = current_level_hash
        else:
            left = filled_subtrees[i]
            right = current_level_hash

        current_level_hash = hash_left_right(left, right)

        current_index /= 2

    root_index = current_root_index.get()
    roots[root_index] = current_level_hash

    next_index.set(int(current_index + 1))
    current_root_index.set(int((root_index + 1) % ROOT_HISTORY_SIZE))
    roots_var.set(roots)
    zeros_var.set(zeros)
    filled_subtrees_var.set(filled_subtrees)
    return next_index.get() - 1

@export
def is_known_root(root: str) -> bool:
    if root is None or len(root) == 0:
        return False

    i = current_root_index.get()
    current_index = i

    roots = roots_var.get()

    first_loop = True

    while first_loop or i != current_index:
        first_loop = False
        if root == roots[i]:
            return True
        if i == 0:
            i = ROOT_HISTORY_SIZE
        i -= 1
    return False

@export
def get_last_root(i: str = None) -> str:
    return roots_var.get()[current_root_index.get()]



'''
Tornado
'''

@export
def deposit(commitment: str, encrypted_note: str):
    assert commitments[commitment] is None, 'The commitment has been submitted.'
    inserted_index = insert(commitment)
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
def withdraw(proof: dict, root: str, nullifier_hash: str, recipient: str, relayer: str, fee: int, refund: int):
    assert fee < denomination.get(), 'Fee exceeds transfer value.'
    assert nullifier_hashes[nullifier_hash] is None, 'The note has already been spent.'
    assert is_known_root(root), 'Cannot find your merkle root.'
    assert verifier.verify(
        proof=proof,
        inputs=[int(root, 16), nullifier_hash, recipient, relayer, fee, refund]
    ), 'Invalid withdraw proof.'

    nullifier_hashes[nullifier_hash] = True

    process_withdraw(recipient, relayer, fee, refund)


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
            amount = fee
        )

    total_deposit_balance.set(total_deposit_balance.get() - (amount + fee))


@export
def is_spent(nullifier_hash: str) -> bool:
    return nullifier_hashes[nullifier_hash] is not None

@export
def is_spent_array(nullifier_hash_array: list) -> list:
    spent = []
    for nullifier_hash in nullifier_hash_array:
        spent.append(is_spent(nullifier_hash))
    return spent

