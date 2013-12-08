import cherrypy

class AutomateTheWeb(object):
    def __init__(self, allrules):
        """
        @type allrules: rules.RuleContext
        """
        self.allrules = allrules

    @cherrypy.expose
    def index(self):
        return "This will be the web page.."

    def stop(self):
        cherrypy.engine.stop()
