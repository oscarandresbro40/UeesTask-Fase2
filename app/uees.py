from jinja2 import ChoiceLoader, FileSystemLoader
from fastapi.templating import Jinja2Templates

from app import web as web_module


templates = Jinja2Templates(directory="app/templates_uees")
templates.env.loader = ChoiceLoader(
    [
        FileSystemLoader("app/templates_uees"),
        FileSystemLoader("app/templates"),
    ]
)
web_module.templates = templates
app = web_module.app
