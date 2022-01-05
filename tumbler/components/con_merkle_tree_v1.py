# con_merkle_tree_v1

import con_tumbler_verifier_v1 as verifier
import con_mimc_sponge_v1 as mimc_sponge


current_root_index = Variable()
next_index = Variable()
levels = Variable()
roots_var = Variable()
filled_subtrees_var = Variable()

ROOT_HISTORY_SIZE = 30
FIELD_SIZE = 21888242871839275222246405745257275088548364400416034343698204186575808495617
ZERO_VALUE = 21663839004416932945382355908790599225266501822907911457504978515578255421292


nullifier_hashes = Hash(default_value=None)
commitments = Hash(default_value=None)
denomination = Variable()
total_deposit_balance = Variable()
token_contract = Variable()
I = importlib


@construct
def init(tree_levels: int = 20):
    assert tree_levels > 0, 'tree_levels should be greater than zero'
    assert tree_levels < 32, 'tree_levels should be less than 32'
    filled_subtrees = []
    roots = [None] * ROOT_HISTORY_SIZE

    for i in range(tree_levels):
        filled_subtrees.append(zeros(i))

    roots[0] = zeros(tree_levels-1)

    # Set variables
    current_root_index.set(0)
    next_index.set(0)
    levels.set(tree_levels)
    roots_var.set(roots)
    filled_subtrees_var.set(filled_subtrees)

    token_contract.set('con_phi_lst001')
    total_deposit_balance.set(0)
    denomination.set(1000)


@export
def insert(leaf: str) -> int:
    current_index = next_index.get()
    tree_levels = levels.get()
    assert current_index != 2**tree_levels, 'Merkle tree is full. No more leaves can be added.'

    filled_subtrees = filled_subtrees_var.get()
    roots = roots_var.get()

    current_level_hash = str(leaf)

    for i in range(tree_levels):
        if current_index % 2 == 0:
            left = current_level_hash
            right = zeros(i)
            filled_subtrees[i] = current_level_hash
        else:
            left = filled_subtrees[i]
            right = current_level_hash

        current_level_hash = mimc_sponge.hash_left_right(left, right)

        current_index /= 2

    root_index = current_root_index.get()
    next_root_index = int((root_index + 1) % ROOT_HISTORY_SIZE)
    roots[next_root_index] = current_level_hash

    next_index.set(int(current_index + 1))
    current_root_index.set(next_root_index)
    roots_var.set(roots)
    filled_subtrees_var.set(filled_subtrees)
    return current_index


@export
def is_known_root(root: str) -> bool:
    if root is None or len(root) == 0 or int(root) == 0:
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


def zeros(i: int) -> int:
    if i == 0:
        return int('0x2fe54c60d3acabf3343a35b6eba15db4821b340f76e741e2249685ed4899af6c', 16)
    elif i == 1:
        return int('0x256a6135777eee2fd26f54b8b7037a25439d5235caee224154186d2b8a52e31d', 16)
    elif i == 2:
        return int('0x1151949895e82ab19924de92c40a3d6f7bcb60d92b00504b8199613683f0c200', 16)
    elif i == 3:
        return int('0x20121ee811489ff8d61f09fb89e313f14959a0f28bb428a20dba6b0b068b3bdb', 16)
    elif i == 4:
        return int('0x0a89ca6ffa14cc462cfedb842c30ed221a50a3d6bf022a6a57dc82ab24c157c9', 16)
    elif i == 5:
        return int('0x24ca05c2b5cd42e890d6be94c68d0689f4f21c9cec9c0f13fe41d566dfb54959', 16)
    elif i == 6:
        return int('0x1ccb97c932565a92c60156bdba2d08f3bf1377464e025cee765679e604a7315c', 16)
    elif i == 7:
        return int('0x19156fbd7d1a8bf5cba8909367de1b624534ebab4f0f79e003bccdd1b182bdb4', 16)
    elif i == 8:
        return int('0x261af8c1f0912e465744641409f622d466c3920ac6e5ff37e36604cb11dfff80', 16)
    elif i == 9:
        return int('0x0058459724ff6ca5a1652fcbc3e82b93895cf08e975b19beab3f54c217d1c007', 16)
    elif i == 10:
        return int('0x1f04ef20dee48d39984d8eabe768a70eafa6310ad20849d4573c3c40c2ad1e30', 16)
    elif i == 11:
        return int('0x1bea3dec5dab51567ce7e200a30f7ba6d4276aeaa53e2686f962a46c66d511e5', 16)
    elif i == 12:
        return int('0x0ee0f941e2da4b9e31c3ca97a40d8fa9ce68d97c084177071b3cb46cd3372f0f', 16)
    elif i == 13:
        return int('0x1ca9503e8935884501bbaf20be14eb4c46b89772c97b96e3b2ebf3a36a948bbd', 16)
    elif i == 14:
        return int('0x133a80e30697cd55d8f7d4b0965b7be24057ba5dc3da898ee2187232446cb108', 16)
    elif i == 15:
        return int('0x13e6d8fc88839ed76e182c2a779af5b2c0da9dd18c90427a644f7e148a6253b6', 16)
    elif i == 16:
        return int('0x1eb16b057a477f4bc8f572ea6bee39561098f78f15bfb3699dcbb7bd8db61854', 16)
    elif i == 17:
        return int('0x0da2cb16a1ceaabf1c16b838f7a9e3f2a3a3088d9e0a6debaa748114620696ea', 16)
    elif i == 18:
        return int('0x24a3b3d822420b14b5d8cb6c28a574f01e98ea9e940551d2ebd75cee12649f9d', 16)
    elif i == 19:
        return int('0x198622acbd783d1b0d9064105b1fc8e4d8889de95c4c519b3f635809fe6afc05', 16)
    elif i == 20:
        return int('0x29d7ed391256ccc3ea596c86e933b89ff339d25ea8ddced975ae2fe30b5296d4', 16)
    elif i == 21:
        return int('0x19be59f2f0413ce78c0c3703a3a5451b1d7f39629fa33abd11548a76065b2967', 16)
    elif i == 22:
        return int('0x1ff3f61797e538b70e619310d33f2a063e7eb59104e112e95738da1254dc3453', 16)
    elif i == 23:
        return int('0x10c16ae9959cf8358980d9dd9616e48228737310a10e2b6b731c1a548f036c48', 16)
    elif i == 24:
        return int('0x0ba433a63174a90ac20992e75e3095496812b652685b5e1a2eae0b1bf4e8fcd1', 16)
    elif i == 25:
        return int('0x019ddb9df2bc98d987d0dfeca9d2b643deafab8f7036562e627c3667266a044c', 16)
    elif i == 26:
        return int('0x2d3c88b23175c5a5565db928414c66d1912b11acf974b2e644caaac04739ce99', 16)
    elif i == 27:
        return int('0x2eab55f6ae4e66e32c5189eed5c470840863445760f5ed7e7b69b2a62600f354', 16)
    elif i == 28:
        return int('0x002df37a2642621802383cf952bf4dd1f32e05433beeb1fd41031fb7eace979d', 16)
    elif i == 29:
        return int('0x104aeb41435db66c3e62feccc1d6f5d98d0a0ed75d1374db457cf462e3a1f427', 16)
    elif i == 30:
        return int('0x1f3c6fd858e9a7d4b0d1f38e256a09d81d5a5e3c963987e2d4b814cfab7c6ebb', 16)
    elif i == 31:
        return int('0x2c7a07d20dff79d01fecedc1134284a8d08436606c93693b67e333f671bf69cc', 16)
    else:
         assert False, "Index out of bounds"


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
def withdraw(a: list, b: list, c: list, root: str, nullifier_hash: str, recipient: str, relayer: str = '0', fee: str = '0', refund: str = '0'):
    assert int(fee) < denomination.get(), 'Fee exceeds transfer value.'
    assert nullifier_hashes[nullifier_hash] is None, 'The note has already been spent.'
    assert is_known_root(root), 'Cannot find your merkle root.'
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

