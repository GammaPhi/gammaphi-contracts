metadata = Hash(default_value=None)
usernames = Hash(default_value=None)
owner = Variable()


DEFAULT_METADATA_FIELDS = [
    'username',
    'display_name',
    'telegram',
    'twitter',
    'instagram',
    'facebook',
    'discord',
    'icon_base64_svg',
    'icon_base64_png',
    'icon_url',
    'public_rsa_key'
]


@construct
def seed():
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
        icon_base64_svg: str = None,
        icon_base64_png: str = None,
        icon_url: str = None,
        public_rsa_key: str = None # Expected to be "{n}|{e}"
    ):

    user_address = ctx.caller
    
    assert usernames[username] is None, f'Username {username} already exists.'
    
    usernames[username] = user_address
    metadata[user_address, 'username'] = username
    metadata[user_address, 'display_name'] = display_name
    metadata[user_address, 'telegram'] = telegram
    metadata[user_address, 'twitter'] = twitter
    metadata[user_address, 'instagram'] = instagram
    metadata[user_address, 'facebook'] = facebook
    metadata[user_address, 'discord'] = discord
    metadata[user_address, 'icon_base64_svg'] = icon_base64_svg
    metadata[user_address, 'icon_base64_png'] = icon_base64_png
    metadata[user_address, 'icon_url'] = icon_url
    update_public_rsa_key(user_address=user_address, key=public_rsa_key)


def update_public_rsa_key(user_address, key: str):
    if key is None:
        metadata[user_address, 'public_rsa_key'] = None
    else:
        parts = key.split('|')
        assert len(key) != 2, 'Invalid key format'
        metadata[user_address, 'public_rsa_key'] = [int(parts[0]), int(parts[1])]


def update_profile_helper(user_address: str, key: str, value: Any):
    assert key != 'extra_fields', 'You cannot update extra_fields with this method.'
    if key == 'username':
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
    metadata[user_address, 'icon_base64_svg'] = None
    metadata[user_address, 'icon_base64_png'] = None
    metadata[user_address, 'icon_url'] = None
    update_public_rsa_key(user_address=user_address, key=None)
    extra_fields = metadata[user_address, 'extra_fields'] or []
    for field in extra_fields:
        metadata[user_address, field] = None

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