from core import SCOPE_INPUT
from modules.astral.AstralInput import init, AstralInput

def init_module(config, scope):
    if scope == SCOPE_INPUT:
        init(config)

config = {SCOPE_INPUT: AstralInput}
