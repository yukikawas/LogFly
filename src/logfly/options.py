"""把用户传入的选项规范成布尔值或固定取值。

2.x 用字符串 ``'yes'`` / ``'no'`` 当开关，问题是：

* 拼错成 ``'yse'`` 时，各个函数要各自记得校验，漏写就静默走错分支；
* 同一个概念在 5 个函数里各写一遍 ``if == 'yes' ... elif == 'no' ... else raise``。

这里集中做一次校验：字符串和 True/False 都接受，非法值统一抛
:class:`~logfly.errors.ParameterError`，调用方就不用重复判断了。
"""

from .errors import ParameterError

_YES = frozenset({'yes', 'y', 'true', '1'})
_NO = frozenset({'no', 'n', 'false', '0'})

#: ``write_log`` 支持的位置，顺序即报错信息里的展示顺序。
POSITIONS = ('CLI', 'file', 'fileCLI')

#: ``write_log`` 支持的写入模式。
MODES = ('add', 'new')


def as_bool(value, option):
    """把 ``'yes'`` / ``'no'``（或 True / False）转成 bool。

    ``option`` 只用于拼报错信息，例如 ``as_bool('maybe', 'hidden')``
    会告诉你 ``hidden`` 这个参数错了。
    """
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        text = value.strip().lower()
        if text in _YES:
            return True
        if text in _NO:
            return False
    raise ParameterError(
        "参数 {0} 必须是 'yes' 或 'no'（也接受 True/False），收到 {1!r}".format(option, value)
    )


def as_position(value):
    """校验日志位置，返回规范写法（大小写不敏感）。"""
    if isinstance(value, str):
        text = value.strip().lower()
        for position in POSITIONS:
            if text == position.lower():
                return position
    raise ParameterError(
        "参数 position 必须是 {0} 之一，收到 {1!r}".format(' / '.join(POSITIONS), value)
    )


def as_mode(value):
    """校验写入模式，返回 ``'add'`` 或 ``'new'``。"""
    if isinstance(value, str):
        text = value.strip().lower()
        if text in MODES:
            return text
    raise ParameterError("参数 mode 必须是 'add' 或 'new'，收到 {0!r}".format(value))
