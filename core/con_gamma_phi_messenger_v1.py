# con_gamma_phi_messenger_v1

messages_hash = Hash(default_value=None)


@export
def send_message(to: str, message: Any):
    sender = ctx.caller

    counter = messages_hash[sender, to, 'counter'] or 0
    counter += 1

    messages_hash[sender, to, counter, 'message'] = message
    messages_hash[sender, to, counter, 'timestamp'] = now    
    messages_hash[sender, to, 'counter'] = counter


