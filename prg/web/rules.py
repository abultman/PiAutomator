import cherrypy

def todict(obj, classkey=None):
    if isinstance(obj, dict):
        for k in obj.keys():
            obj[k] = todict(obj[k], classkey)
        return obj
    elif hasattr(obj, "__iter__"):
        return [todict(v, classkey) for v in obj]
    elif hasattr(obj, "__dict__"):
        data = dict([(key, todict(value, classkey))
            for key, value in obj.__dict__.iteritems()
            if not callable(value) and not key.startswith('_')])
        if classkey is not None and hasattr(obj, "__class__"):
            data[classkey] = obj.__class__.__name__
        return data
    else:
        return obj


class Rules(object):
    exposed = True

    def __init__(self, rule_context):
        """
        @type rule_context: rules.RuleContext
        """
        self.rule_context = rule_context
        pass

    @cherrypy.tools.json_out()
    def GET(self, id=None):
        if id==None:
            # return self.rule_context
            return {"rules": {
                k: {
                    'name' : v.rule_state.rule_name,
                    'url': cherrypy.url(path = v.rule_state.rule_id)
                } for k,v in self.rule_context.rules.items()
            }}
        elif id in self.rule_context.rules:
            rule = self.rule_context.rules[id]
            struct = {"rule" : {
                'type' : rule.__class__.__name__,
                'rule_id' : rule.rule_state.rule_id,
                'rule_text' : rule.rule_state.rule_name,
                'state' : rule.rule_state.data
            }, "all_rules" : cherrypy.url("../rule/")}
            print rule.actions
            return struct

        else:
            return "You suck"

