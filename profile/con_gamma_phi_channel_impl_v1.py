# con_gamma_phi_channel_impl_v1
# owner: con_gamma_phi_profile_v5

import con_rsa_encryption as rsa

random.seed()

@export
def interact(payload: dict, state: dict, caller: str):
    # state
    total_users = state['total_users']
    metadata = state['metadata']
    usernames = state['usernames']
    owner = state['owner']
    channels = state['channels']

    # action
    function = payload['action']

    if function == 'create_channel':
        create_channel(
            caller, 
            payload.get('users'), 
            payload.get('channel_name'), 
            channels,
            metadata, 
            usernames
        )
    elif function == 'update_channel':
        update_channel(
            caller, 
            payload.get('users'), 
            payload.get('channel_name'), 
            channels,
            metadata, 
            usernames
        )

def generate_key() -> str:
    return random.getrandbits(256).to_bytes(256 // 8, "big").hex()

def update_channel(caller: str, users: list, channel_name: str, channels: Any, metadata: Any, usernames: Any):
    # sha256 key
    assert metadata[caller, 'username'] is not None, 'This user does not exist.'
    assert channel_name is not None, 'channel_name cannot be null.'
    assert channels[channel_name, 'owner'] is not None, 'Channel does not exist.'
    assert channels[channel_name, 'owner'] == caller, 'You do not own this channel.'
    if caller in users:
        users.remove(caller)

    all_users = [caller] + users
    key = generate_key()

    user_addresses = []    
    for user in all_users:
        user_address = usernames[user]
        if user_address is None:
            user_address = user
        rsa_key = metadata[user, 'public_rsa_key']
        assert rsa_key is not None, f'User {user} has not setup their encryption keys.'
        rsa_keys = rsa_key.split('|')
        encrypted = rsa.encrypt(
            message_str=key,
            n=int(rsa_keys[0]),
            e=int(rsa_keys[1])  
        )
        metadata[user, 'keys', channel_name] = encrypted 
        user_addresses.append(user_address)

    channels[channel_name, 'users'] = user_addresses


def validate_channel_name(channel_name: str):
    assert channel_name is not None and len(channel_name) > 0, 'channel_name cannot be null or empty'
    assert isinstance(channel_name, str), 'channel_name must be a string.'
    assert len(channel_name) <= 32, 'channel_name cannot be longer than 32 characters.'
    assert all([c.isalnum() or c in ('_', '-') for c in channel_name]), 'channel_name has invalid characters. Each character must be alphanumeric, a hyphen, or an underscore.'
    assert channel_name[0] not in ('-', '_') and channel_name[-1] not in ('-', '_'), 'channel_name cannot start or end with a hyphen or underscore.'
    

def create_channel(caller: str, users: list, channel_name: str, channels: Any, metadata: Any, usernames: Any):
    # sha256 key
    assert metadata[caller, 'username'] is not None, 'This user does not exist.'
    assert channel_name is not None, 'channel_name cannot be null.'
    assert channels[channel_name, 'owner'] is None, 'Channel already exists.'

    validate_channel_name(channel_name)

    if caller in users:
        users.remove(caller)

    all_users = [caller] + users

    channels[channel_name, 'owner'] = caller

    key = generate_key()

    user_addresses = []    
    for user in all_users:
        user_address = usernames[user]
        if user_address is None:
            user_address = user
        rsa_key = metadata[user, 'public_rsa_key']
        assert rsa_key is not None, f'User {user} has not setup their encryption keys.'
        rsa_keys = rsa_key.split('|')
        encrypted = rsa.encrypt(
            message_str=key,
            n=int(rsa_keys[0]),
            e=int(rsa_keys[1])  
        )
        metadata[user, 'keys', channel_name] = encrypted 
        user_addresses.append(user_address)

    channels[channel_name, 'users'] = user_addresses
