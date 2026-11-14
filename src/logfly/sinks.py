"""日志的输出目标：终端和文件。

每个 sink 只负责"把一行日志写到某个地方"，不认识 ``folder_name``、
``mode`` 这类业务概念——路径怎么算交给 :mod:`logfly.logger`。
这样 2.x 里"终端格式 + 文件格式"各写四遍的问题就不存在了。
"""

import sys
import threading
from pathlib import Path

try:  # colorama 只负责让老式 Windows 控制台也能显示颜色，装不装都能跑
    from colorama import Fore, init as _init_colorama

    _init_colorama(autoreset=True)
    HAS_COLORAMA = True
except ModuleNotFoundError:  # pragma: no cover - 取决于运行环境
    HAS_COLORAMA = False

#: 日志级别 -> 颜色。级别不区分大小写，未收录的级别用灰色。
_LEVEL_COLORS = {
    'INFO': '\033[0;34m',
    'WARNING': '\033[0;33m',
    'ERROR': '\033[0;31m',
    'PASS': '\033[0;32m',
}
_DEFAULT_COLOR = '\033[0;37m'
_COLOR_RESET = '\033[0m'

#: 多个线程同时写同一个文件时，保证"一条日志一次写完"，不会交错成半行。
_WRITE_LOCK = threading.Lock()


class ConsoleSink:
    """把日志打印到终端，可选带颜色。"""

    def __init__(self, color=True, stream=None):
        self.color = color
        self.stream = stream

    def _decorate(self, line, level):
        if not self.color:
            return line
        color = _LEVEL_COLORS.get(level.upper(), _DEFAULT_COLOR)
        return color + line + _COLOR_RESET

    def emit(self, name, when, level, message):
        line = '{0} {1} [{2}] {3}'.format(name, when, level, message)
        stream = self.stream or sys.stdout
        stream.write(self._decorate(line, level) + '\n')
        stream.flush()


class FileSink:
    """把日志写进一个文件。

    ``append=True`` 追加（``mode='add'``），``append=False`` 覆盖
    （``mode='new'``）。
    """

    def __init__(self, path, append=True):
        self.path = Path(path)
        self.append = append

    def emit(self, when, level, message):
        # 行尾用 \r\n，和 2.x 生成的日志文件保持一致，方便沿用旧日志的解析脚本。
        line = '{0} [{1}] {2}\r\n'.format(when, level, message)
        with _WRITE_LOCK:
            self.path.parent.mkdir(parents=True, exist_ok=True)
            with open(self.path, 'a' if self.append else 'w', encoding='utf-8', newline='') as handle:
                handle.write(line)
