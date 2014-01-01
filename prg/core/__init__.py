import logging
import inspect

INIT_MODULE = 'init_module'

__myclasses__ = {}
__inited__ = []

__logger__ = logging.getLogger("global")
__logger__.setLevel(logging.INFO)

SCOPE_INPUT = 'inputs'
SCOPE_RECEIVER = 'receivers'

def load_class(elem, config, scope):
    fullname = scope + '.' + elem
    if fullname not in __myclasses__:
        __logger__.info("Loading class of type %s as %s", elem, scope)
        mod = __load_module__(fullname)
        if mod is None:
                mod = __load_module__('modules.' + elem)
        if mod is None:
            parent = '.'.join(('modules.' + elem).split('.')[:-1])
            mod = __load_module__(parent, elem)
        if mod is None:
            raise ValueError("%s not found in scope %s" % (elem, scope))
        required_class = __get_class__(elem, mod, scope)
        __myclasses__[fullname] = required_class
        __init_module__(config, elem, mod, scope)

    return __myclasses__[fullname]


def __get_class__(elem, mod, scope):
    classname = elem.split(".")[-1]
    if hasattr(mod, classname) and inspect.isclass(getattr(mod, classname)):
        return getattr(mod, classname)
    elif hasattr(mod, 'config'):
        return getattr(mod, 'config')[scope]


def __load_module__(name, fromname = None):
    if fromname is None:
        fromname = name

    fromname = fromname.split(".")[-1]
    try:
        return __import__(name, globals=globals(), fromlist=[fromname])
    except:
        return None


def __init_module__(config, elem, mod, scope):
    if ('modules.' in mod.__package__):
        parent = __load_module__(mod.__package__)
        if parent is not None and hasattr(parent, INIT_MODULE) and parent not in __inited__:
            __logger__.info("Initializing parent of %s" % elem)
            __init__(parent, config, scope)

    if hasattr(mod, INIT_MODULE):
        __init__(mod, config, scope)


def __init__(elem, config, scope):
    init_method = getattr(elem, INIT_MODULE)
    argcount = init_method.func_code.co_argcount
    key = None
    if argcount == 2:
        key = '%s.%s' %(elem, scope)
    else:
        key = elem
    if key in __inited__:
        return

    __logger__.info("Initializing %s" % elem)
    if argcount == 2:
        __inited__.append(key)
        init_method(config, scope)
    elif argcount == 1:
        __inited__.append(key)
        init_method(config)
    elif argcount == 0:
        __inited__.append(key)
        init_method()
    else:
        __logger__.info("Initmethod in %s can have 0 to 2 args" % elem)
