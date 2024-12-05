from fastapi.templating import Jinja2Templates

from auction.config import config
from auction.i18n import get_layout_direction, gettext


templates = Jinja2Templates(directory=config.templates_dir_path)
templates = Jinja2Templates(directory=config.templates_dir_path)
templates.env.globals["_"] = gettext
templates.env.globals["_dir"] = get_layout_direction
