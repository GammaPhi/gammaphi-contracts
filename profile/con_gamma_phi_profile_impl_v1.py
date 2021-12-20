# con_gamma_phi_profile_impl_v1


DEFAULT_METADATA_FIELDS = [
    'username',
    'display_name',
    'telegram',
    'twitter',
    'instagram',
    'facebook',
    'discord',
    'icon_base64',
    'icon_url',
    'public_rsa_key',
    'frens'
]


@export
def interact(payload: dict, state: dict, caller: str):
    # state
    total_users = state['total_users']
    metadata = state['metadata']
    usernames = state['usernames']
    owner = state['owner']

    # action
    function = payload['action']


    if function == 'create_profile':
        create_profile(
            payload.get('username'),
            caller,
            metadata,
            usernames,
            total_users,
            payload.get('display_name'),
            payload.get('telegram'),
            payload.get('twitter'),
            payload.get('instagram'),
            payload.get('facebook'),
            payload.get('discord'),
            payload.get('icon_base64'),
            payload.get('icon_url'),
            payload.get('public_rsa_key'),
        )
    elif function == 'add_frens':
        add_frens(
            payload.get('frens'),
            caller,
            metadata,
            usernames,
        )
    elif function == 'remove_frens':
        remove_frens(
            payload.get('frens'),
            caller,
            metadata,
            usernames,
        )
    elif function == 'delete_profile':
        delete_profile(
            caller,
            metadata,
            usernames,
            total_users,
        )
    elif function == 'force_delete_profile':
        force_delete_profile(
            payload.get('user_address'),
            caller,
            metadata,
            usernames,
            total_users,
            owner
        )
    elif function == 'update_profile':
        update_profile(
            payload.get('key'),
            payload.get('value'),
            caller,
            metadata,
            usernames,
        )
    elif function == 'force_update_profile':
        force_update_profile(
            payload.get('user_address'),
            payload.get('key'),
            payload.get('value'),
            caller,
            metadata,
            usernames,
            owner
        )
    elif function == 'force_update_metadata':
        force_update_metadata(
            payload.get('user_address'),
            payload.get('key'),
            payload.get('value'),
            caller,
            metadata,
            owner,
        )
    elif function == 'force_update_usernames':
        force_update_usernames(
            payload.get('key'),
            payload.get('value'),
            caller,
            usernames,
            owner,
        )


def create_profile(
        username: str,
        caller: str,
        metadata: Any,
        usernames: Any,
        total_users: Any,
        display_name: str = None,
        telegram: str = None,
        twitter: str = None,
        instagram: str = None,
        facebook: str = None,
        discord: str = None,
        icon_base64: str = None,
        icon_url: str = None,
        public_rsa_key: str = None, # Expected to be "{n}|{e}"
    ):

    user_address = caller
    
    validate_username(username)
    assert usernames[username] is None, f'Username {username} already exists.'
    
    usernames[username] = user_address
    metadata[user_address, 'username'] = username    
    metadata[user_address, 'display_name'] = display_name or username
    if telegram is not None:
        metadata[user_address, 'telegram'] = telegram
    if twitter is not None:
        metadata[user_address, 'twitter'] = twitter
    if instagram is not None:
        metadata[user_address, 'instagram'] = instagram
    if facebook is not None:
        metadata[user_address, 'facebook'] = facebook
    if discord is not None:
        metadata[user_address, 'discord'] = discord
    if icon_base64 is not None:
        metadata[user_address, 'icon_base64'] = icon_base64
    if icon_url is not None:
        metadata[user_address, 'icon_url'] = icon_url
    metadata[user_address, 'frens'] = []
    update_public_rsa_key(user_address=user_address, key=public_rsa_key, metadata=metadata)
    total_users.set(total_users.get()+1)


def add_frens(frens: list,        
              caller: str,
              metadata: Any,
              usernames: Any):
    user_address = caller
    assert metadata[user_address, 'username'] is not None, 'You do not have a profile. Please create one first.'
    current_frens = metadata[user_address, 'frens'] or []
    for fren in frens:
        # Check for address or username
        fren_address = usernames[fren]
        if fren_address is None:
            fren_address = fren
        
        assert metadata[fren_address, 'username'] is not None, f'{fren_address} does not have a profile.'
        assert fren_address != user_address, 'You cannot add yourself as a fren'

        if fren_address not in current_frens:
            current_frens.append(fren_address)
    metadata[user_address, 'frens'] = current_frens


def remove_frens(frens: list,        
                caller: str,
                metadata: Any,
                usernames: Any):
    user_address = caller
    assert metadata[user_address, 'username'] is not None, 'You do not have a profile. Please create one first.'
    current_frens = metadata[user_address, 'frens'] or []
    for fren in frens:
        # Check for address or username
        fren_address = usernames[fren]
        if fren_address is None:
            fren_address = fren
        
        if fren_address in current_frens:
            current_frens.remove(fren_address)
    metadata[user_address, 'frens'] = current_frens


def validate_username(username: str):
    assert username is not None and len(username) > 0, 'Username cannot be null or empty'
    assert isinstance(username, str), 'Username must be a string.'
    assert len(username) <= 16, 'Usernames cannot be longer than 16 characters.'
    assert all([c.isalnum() or c in ('_', '-') for c in username]), 'Username has invalid characters. Each character must be alphanumeric, a hyphen, or an underscore.'
    assert username[0] not in ('-', '_') and username[-1] not in ('-', '_'), 'Usernames cannot start or end with a hyphen or underscore.'
    

def update_public_rsa_key(user_address: str, key: str, metadata: Any):
    if key is None:
        metadata[user_address, 'public_rsa_key'] = None
    else:
        assert len(key.split('|')) == 2, 'Invalid key format'
        metadata[user_address, 'public_rsa_key'] = key


def update_profile_helper(user_address: str, key: str, value: Any, metadata: Any, usernames: Any):
    assert key != 'extra_fields', 'You cannot update extra_fields with this method.'
    assert metadata[user_address, 'username'] is not None, 'You do not have a profile. Please create one first.'
    
    if key == 'username':
        validate_username(value)

        username = metadata[user_address, 'username']
        assert username is not None, 'This user does not exist.'
        assert usernames[value] is None, f'Username {value} already exists.'
        assert value is not None, 'No username provided. Call delete_profile to remove a user profile.'

        usernames[value] = user_address

    elif key == 'public_rsa_key':
        update_public_rsa_key(user_address=user_address, key=value, metadata=metadata)

    elif key not in DEFAULT_METADATA_FIELDS:
        extra_fields = metadata[user_address, 'extra_fields'] or []
        if key not in extra_fields:
            extra_fields.append(key)
            metadata[user_address, 'extra_fields'] = extra_fields

    metadata[user_address, key] = value


def delete_profile_helper(user_address: str, metadata: Any, usernames: Any, total_users: Any):
    username = metadata[user_address, 'username']
    assert username is not None, 'This user does not exist.'
    usernames[username] = None
    metadata[user_address, 'username'] = None
    metadata[user_address, 'display_name'] = None
    metadata[user_address, 'telegram'] = None
    metadata[user_address, 'twitter'] = None
    metadata[user_address, 'instagram'] = None
    metadata[user_address, 'facebook'] = None
    metadata[user_address, 'discord'] = None
    metadata[user_address, 'icon_base64'] = None
    metadata[user_address, 'icon_url'] = None
    metadata[user_address, 'frens'] = None
    update_public_rsa_key(user_address=user_address, key=None, metadata=metadata)
    extra_fields = metadata[user_address, 'extra_fields'] or []
    for field in extra_fields:
        metadata[user_address, field] = None
    # Subtract from total user count
    total_users.set(total_users.get()-1)


def delete_profile(caller: str, metadata: Any, usernames: Any, total_users: Any):
    delete_profile_helper(caller, metadata, usernames, total_users)


def force_delete_profile(user_address: str, caller: str, metadata: Any, usernames: Any, total_users: Any, owner: Any):
    assert caller == owner.get(), 'Only the owner can call force_delete_profile'
    delete_profile_helper(user_address, metadata, usernames, total_users)


def update_profile(key: str, value: Any, caller: str, metadata: Any, usernames: Any):
    update_profile_helper(caller, key, value, metadata, usernames)


def force_update_profile(user_address: str, key: str, value: Any, caller: str, metadata: Any, usernames: Any, owner: Any):
    assert caller == owner.get(), 'Only the owner can call force_update_profile'
    update_profile_helper(user_address, key, value, metadata, usernames)


def force_update_metadata(user_address: str, key: str, value: Any, caller: str, metadata: Any, owner: Any):
    assert caller == owner.get(), 'Only the owner can call force_update_metadata'
    metadata[user_address, key] = value


def force_update_usernames(key: str, value: Any, caller: str, usernames: Any, owner: Any):
    assert caller == owner.get(), 'Only the owner can call force_update_usernames'
    usernames[key] = value