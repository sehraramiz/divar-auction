from fastapi.templating import Jinja2Templates

from auction.core.config import config
from auction.core.i18n import get_layout_direction, gettext, localize_number


templates = Jinja2Templates(directory=config.templates_dir_path)
templates = Jinja2Templates(directory=config.templates_dir_path)
templates.env.globals["_"] = gettext
templates.env.globals["_dir"] = get_layout_direction
templates.env.filters["localize_number"] = localize_number
