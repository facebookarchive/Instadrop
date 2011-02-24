import os
import inspect
from google.appengine.ext import webapp
from google.appengine.ext.webapp import template


def _render_template(self, template_path, context={}):
    path = os.path.join(os.path.dirname(
        inspect.getfile(self.__class__)),
        "templates/" + template_path)
    self.response.out.write(template.render(path, context))
webapp.RequestHandler.render_template = _render_template
