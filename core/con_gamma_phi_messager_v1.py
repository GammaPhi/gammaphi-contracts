# con_gamma_phi_messager_v1

messages_hash = Hash(default_value=[])


@export
def send_message(to: str, message: str):
    sender = ctx.caller
    messages = messages_hash[sender, to] or []
    messages.append(message)
    messages_hash[sender, to] = messages