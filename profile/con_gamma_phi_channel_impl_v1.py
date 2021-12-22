import con_rsa_encryption as rsa


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


def update_channel(caller: str, users: list, channel_name: str, channels: Any, metadata: Any, usernames: Any):
    # sha256 key
    assert metadata[caller, 'username'] is not None, 'This user does not exist.'
    assert channel_name is not None, 'channel_name cannot be null.'
    assert channels[channel_name, 'owner'] is None, 'Channel already exists.'
    assert channels[channel_name, 'owner'] == caller, 'You do not own this channel.'

    all_users = [caller] + users

    key = hashlib.sha256()

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


def create_channel(caller: str, users: list, channel_name: str, channels: Any, metadata: Any, usernames: Any):
    # sha256 key
    assert metadata[caller, 'username'] is not None, 'This user does not exist.'
    assert channel_name is not None, 'channel_name cannot be null.'
    assert channels[channel_name, 'owner'] is None, 'Channel already exists.'

    all_users = [caller] + users

    channels[channel_name, 'owner'] = caller

    key = hashlib.sha256()

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
