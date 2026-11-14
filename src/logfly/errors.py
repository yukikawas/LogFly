"""logfly 用到的异常类型。

单独一个模块，是为了让 options / clock / logger 这些模块都能引用它，
又不会互相 import 成环。
"""


class ParameterError(ValueError):
    """参数不合法时抛出。

    继承 ``ValueError`` 有两个好处：

    * 想精确处理时用 ``except ParameterError``；
    * 想粗略兜住时 ``except ValueError`` 也能捕获，和 Python 内建习惯一致。

    2.x 里参数错了只是打印一行错误然后返回 ``None``，调用方无法判断成败。
    现在统一抛异常，让错误在调用处立刻暴露。
    """


#: 2.x 的旧名字（全大写），保留一个别名，老代码 ``except logfly.ParameterERROR`` 仍然有效。
ParameterERROR = ParameterError
