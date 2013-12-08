import cherrypy
from simplejson import JSONEncoder

# encoder = JSONEncoder()
#
# def jsonify_tool_callback(*args, **kwargs):
#     response = cherrypy.response
#     response.headers['Content-Type'] = 'application/json'
#     if isinstance(response.body, dict):
#         response.body = encoder.encode(response.body)
#     else:
#         response.body = encoder.iterencode(response.body)
#
#
# cherrypy.tools.jsonify = cherrypy.Tool('before_finalize', jsonify_tool_callback, priority=30)


from automatetheweb import AutomateTheWeb
from web.rules import Rules


def init(config, rule_context):
    """
    @type config: config.AutomationConfig
    """
    theweb = AutomateTheWeb(rule_context)
    cherrypy.tree.mount(theweb)
    cherrypy.tree.mount(Rules(rule_context), '/rule',
        {'/':
            {'request.dispatch': cherrypy.dispatch.MethodDispatcher()}
        })
    cherrypy.config.update({"server.socket_port": config.getSetting(['web', 'port'], 8089)})
    cherrypy.engine.start()

    return theweb


