from core import SCOPE_INPUT
from modules.llap.LLAP import LLAP, init

def init_module(config, scope):
    if scope == SCOPE_INPUT:
        init(config)

config = {SCOPE_INPUT: LLAP}