from core import SCOPE_RECEIVER
from modules.klikaanklikuit.KlikAanKlikUitReceiver import KlikAanKlikUitReceiver, init_module as init_receiver

def init_module(config, scope):
    if scope == SCOPE_RECEIVER:
        init_receiver(config)

config = {SCOPE_RECEIVER: KlikAanKlikUitReceiver}