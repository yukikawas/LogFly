"""路径解析与写入编排——logfly 的核心。

2.x 的 ``write_log`` 是一个 145 行的函数，把参数校验、路径拼接、控制台打印、
文件写入全揉在一起，而且 "file / fileCLI × add / new" 四个组合各抄了一遍
几乎一样的写入块。这里拆成：

* 路径怎么算（本模块的 ``log_root`` / ``hidden_root`` / ``create_log_folder``）；
* 一行日志怎么落到终端或文件（:mod:`logfly.sinks`）；
* 什么时候写哪里（:class:`Logger`）。

调用方式保持 2.x 不变，``logfly.write_log(...)`` 仍然可以直接用。
"""

from pathlib import Path

from . import clock
from .errors import ParameterError
from .options import as_bool, as_mode, as_position
from .sinks import ConsoleSink, FileSink

#: 默认的子目录名，对应 ``logs/default-log/<date>/``。
DEFAULT_FOLDER = 'default-log'
#: 默认日志根目录名。
DEFAULT_LOG_DIR = 'logs'
#: 隐藏日志目录名，默认在 ``~/.1o9f1y``（沿用 2.x 的命名）。
HIDDEN_DIR = '.1o9f1y'
#: 库内部自报信息（比如建目录、执行命令）用的日志名。
LOG_FILE_STEM = 'logfly-log'

#: 文件名和目录名里不允许出现的东西——避免 ``../`` 把日志写到项目外面。
_FORBIDDEN_IN_NAME = ('/', '\\', '..')


def hidden_root():
    """隐藏日志的根目录，默认 ``~/.1o9f1y``。

    单独抽成函数，测试里可以替换它，不用真的往用户主目录写东西。
    """
    return Path.home() / HIDDEN_DIR


def log_root(base_dir=None):
    """日志根目录。

    ``base_dir`` 为空时取当前工作目录下的 ``logs``（和 2.x 一致）；
    传入时直接把它当作根目录，测试和 CI 因此可以把日志写到临时目录。
    """
    return Path(base_dir) if base_dir is not None else Path.cwd() / DEFAULT_LOG_DIR


def _check_component(value, option):
    """校验文件名 / 目录名片段，禁止路径分隔符和 ``..``。"""
    if not isinstance(value, str) or not value.strip():
        raise ParameterError('参数 {0} 必须是非空字符串，收到 {1!r}'.format(option, value))
    for bad in _FORBIDDEN_IN_NAME:
        if bad in value:
            raise ParameterError(
                '参数 {0} 不能包含 {1!r}（会把日志写到目录外面），收到 {2!r}'.format(
                    option, bad, value
                )
            )
    return value


def create_log_folder(folder_name=DEFAULT_FOLDER, hidden='no', base_dir=None):
    """建好当天要用的日志目录，返回它的路径。

    默认目录是 ``./logs/<folder_name>/<date>/``；``hidden='yes'`` 时
    额外建 ``~/.1o9f1y/<folder_name>/<date>/``。
    """
    folder_name = _check_component(folder_name, 'folder_name')
    today = clock.format_date()

    date_dir = log_root(base_dir) / folder_name / today
    date_dir.mkdir(parents=True, exist_ok=True)

    if as_bool(hidden, 'hidden'):
        (hidden_root() / folder_name / today).mkdir(parents=True, exist_ok=True)

    return date_dir


class Logger:
    """绑定一套配置的写日志对象。

    适合程序里反复写同一种日志::

        log = logfly.get_logger(folder_name='myapp')
        log.info('程序启动')
        log.warning('磁盘快满了')

    每个实例保存目录 / 开关，省得每次调用都把这些参数重传一遍。
    """

    def __init__(self, folder_name=DEFAULT_FOLDER, hidden='no', color='yes',
                 str_message='yes', base_dir=None, name=LOG_FILE_STEM,
                 position='fileCLI'):
        self.folder_name = _check_component(folder_name, 'folder_name')
        self.name = _check_component(name, 'name')
        self.position = as_position(position)
        self.hidden = as_bool(hidden, 'hidden')
        self.color = as_bool(color, 'color')
        self.str_message = as_bool(str_message, 'str_message')
        self.base_dir = Path(base_dir) if base_dir is not None else None

    # ---- 便捷方法 -------------------------------------------------
    def info(self, message, **kwargs):
        """写一条 ``[INFO]``。"""
        return self.write('INFO', message, **kwargs)

    def warning(self, message, **kwargs):
        """写一条 ``[WARNING]``。"""
        return self.write('WARNING', message, **kwargs)

    def error(self, message, **kwargs):
        """写一条 ``[ERROR]``。"""
        return self.write('ERROR', message, **kwargs)

    def success(self, message, **kwargs):
        """写一条 ``[PASS]``（2.x 里表示"通过"的级别）。"""
        return self.write('PASS', message, **kwargs)

    # ---- 核心 -----------------------------------------------------
    def _resolve_message(self, message):
        if self.str_message:
            return str(message)
        if not isinstance(message, str):
            raise ParameterError(
                "str_message='no' 时 message 必须是 str，收到 {0}".format(type(message).__name__)
            )
        return message

    def write(self, level, message, mode='add', name=None, position=None):
        """写一条日志，返回写入的日志文件路径（只写终端时返回 None）。"""
        level = str(level).upper()
        text = self._resolve_message(message)
        mode = as_mode(mode)
        position = as_position(position or self.position)
        name = _check_component(name or self.name, 'name')

        today = clock.format_date()
        if mode == 'add':
            filename = '{0}-{1}.log'.format(name, today)
        else:  # 'new'
            filename = '{0}-{1}.log'.format(name, clock.format_compact())

        when = clock.format_datetime()
        written = None

        if position in ('CLI', 'fileCLI'):
            ConsoleSink(color=self.color).emit(name, when, level, text)

        if position in ('file', 'fileCLI'):
            target = log_root(self.base_dir) / self.folder_name / today / filename
            FileSink(target, append=(mode == 'add')).emit(when, level, text)
            written = target

            if self.hidden:
                # 隐藏目录里的副本总是追加：文件名按日期或时间戳区分，不会串。
                shadow = hidden_root() / self.folder_name / today / filename
                FileSink(shadow, append=True).emit(when, level, text)

        return written


def get_logger(**kwargs):
    """创建一个 :class:`Logger`，参数与 :class:`Logger` 相同。"""
    return Logger(**kwargs)


def write_log(name, position, level, message, mode='add',
              folder_name=DEFAULT_FOLDER, hidden='no', color='yes',
              str_message='yes', base_dir=None):
    """写一条日志——2.x 的主接口，签名保持不变。

    :param name: 日志文件名（不含日期和扩展名）。
    :param position: ``'CLI'`` / ``'file'`` / ``'fileCLI'``。
    :param level: 自定义级别，写进日志时会转成大写并加方括号。
    :param message: 日志正文，默认先 ``str()`` 一次。
    :param mode: ``'add'`` 按天追加；``'new'`` 每次调用生成新文件。
    :param folder_name: ``logs`` 下的子目录名。
    :param hidden: ``'yes'`` 时在 ``~/.1o9f1y`` 再存一份。
    :param color: ``'yes'`` 时终端输出带颜色。
    :param str_message: ``'no'`` 时不调用 ``str()``，此时 ``message`` 必须是 str。
    :param base_dir: 日志根目录，默认 ``./logs``；测试里可以指向临时目录。
    """
    logger = Logger(
        folder_name=folder_name,
        hidden=hidden,
        color=color,
        str_message=str_message,
        base_dir=base_dir,
        name=name,
        position=position,
    )
    return logger.write(level, message, mode=mode)
