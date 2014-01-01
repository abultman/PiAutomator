from core import SCOPE_INPUT, SCOPE_RECEIVER
from modules.pilight.pilight_input import pilight_input, init_module as input_init
from modules.pilight.pilight_output import pilight_output


def init_module(config, scope):
    if scope == SCOPE_INPUT:
        input_init(config)

config = {
    SCOPE_INPUT: pilight_input,
    SCOPE_RECEIVER: pilight_output
}