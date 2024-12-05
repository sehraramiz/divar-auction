import gettext as gettext_module
import pathlib

from contextvars import ContextVar
from typing import Literal

from auction.config import config


BASE_DIR = pathlib.PurePath(__file__).parent
localedir = BASE_DIR / "locales"
_lang_ctx_var: ContextVar[str] = ContextVar("lang_code", default="fa")
Direction = Literal["ltr", "rtl"]


def set_lang_code(lang_code: str) -> None:
    _lang_ctx_var.set(lang_code)


def get_lang_code() -> str:
    lang = _lang_ctx_var.get()
    return lang if lang in config.supported_languages else "fa"


def get_layout_direction() -> Direction:
    rtl_languages = ["fa"]
    lang = _lang_ctx_var.get()
    return "rtl" if lang in rtl_languages else "ltr"


def gettext(msg: str) -> str:
    lang_code = get_lang_code()
    translation = gettext_module.translation(
        "messages", localedir, languages=[lang_code]
    )
    return translation.gettext(msg)
