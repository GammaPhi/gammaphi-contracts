# con_gamma_phi_profile_v2
metadata = Hash(default_value=None)
usernames = Hash(default_value=None)
total_users = Variable()
owner = Variable()


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


@construct
def seed():
    total_users.set(0)
    owner.set(ctx.caller)


@export
def create_profile(
        username: str,
        display_name: str,
        telegram: str = None,
        twitter: str = None,
        instagram: str = None,
        facebook: str = None,
        discord: str = None,
        icon_base64: str = None,
        icon_url: str = None,
        public_rsa_key: str = None # Expected to be "{n}|{e}"
    ):

    user_address = ctx.caller
    
    validate_username(username)
    assert usernames[username] is None, f'Username {username} already exists.'
    
    usernames[username] = user_address
    metadata[user_address, 'username'] = username
    metadata[user_address, 'display_name'] = display_name or username
    metadata[user_address, 'telegram'] = telegram
    metadata[user_address, 'twitter'] = twitter
    metadata[user_address, 'instagram'] = instagram
    metadata[user_address, 'facebook'] = facebook
    metadata[user_address, 'discord'] = discord
    metadata[user_address, 'icon_base64'] = icon_base64
    metadata[user_address, 'icon_url'] = icon_url
    metadata[user_address, 'frens'] = []
    update_public_rsa_key(user_address=user_address, key=public_rsa_key)
    total_users.set(total_users.get()+1)


@export
def add_frens(frens: list):
    user_address = ctx.caller
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


@export 
def remove_frens(frens: list):
    user_address = ctx.caller
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
    

def update_public_rsa_key(user_address, key: str):
    if key is None:
        metadata[user_address, 'public_rsa_key'] = None
    else:
        parts = key.split('|')
        assert len(key) != 2, 'Invalid key format'
        metadata[user_address, 'public_rsa_key'] = [int(parts[0]), int(parts[1])]


def update_profile_helper(user_address: str, key: str, value: Any):
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
        update_public_rsa_key(user_address=user_address, key=value)

    elif key not in DEFAULT_METADATA_FIELDS:
        extra_fields = metadata[user_address, 'extra_fields'] or []
        if key not in extra_fields:
            extra_fields.append(key)
            metadata[user_address, 'extra_fields'] = extra_fields

    metadata[user_address, key] = value


def delete_profile_helper(user_address: str):
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
    update_public_rsa_key(user_address=user_address, key=None)
    extra_fields = metadata[user_address, 'extra_fields'] or []
    for field in extra_fields:
        metadata[user_address, field] = None
    # Subtract from total user count
    total_users.set(total_users.get()-1)

@export
def delete_profile():
    delete_profile_helper(user_address=ctx.caller)


@export
def force_delete_profile(user_address: str):
    assert ctx.caller == owner.get(), 'Only the owner can call force_delete_profile'
    delete_profile_helper(user_address=user_address)


@export
def update_profile(key: str, value: Any):
    update_profile_helper(user_address=ctx.caller, key=key, value=value)


@export
def force_update_profile(user_address: str, key: str, value: Any):
    assert ctx.caller == owner.get(), 'Only the owner can call force_update_profile'
    update_profile_helper(user_address=user_address, key=key, value=value)

@export
def change_ownership(new_owner: str):
    assert ctx.caller == owner.get(), 'Only the owner can change ownership!'

    owner.set(new_owner)