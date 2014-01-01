from core import SCOPE_RECEIVER
from modules.toolcommand.ToolCommandReceiver import ToolCommandReceiver, init_module as receiver_init

def init_module(config, scope):
    if scope == SCOPE_RECEIVER:
        receiver_init()

config = {SCOPE_RECEIVER: ToolCommandReceiver}