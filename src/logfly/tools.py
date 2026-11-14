"""文件与命令相关的辅助函数。

2.x 把这些和日志写入混在同一个模块里，还共用一个 145 行的函数；
现在它们只是"用 logfly 记一笔"的普通工具函数。
"""

import locale
import shutil
import subprocess
import sys
from pathlib import Path

from .errors import ParameterError
from .logger import LOG_FILE_STEM, write_log
from .options import as_bool


def _note(level, message):
    """写一条只出现在终端的库自身信息。"""
    write_log(LOG_FILE_STEM, 'CLI', level, message)


def create_or_check_file(pathorfile, name, warning='yes'):
    """确保文件或目录存在，返回它的 :class:`~pathlib.Path`。

    2.x 的行为差异已修正：原来无论是否真的新建，都会打印
    ``already exists``；现在只有**原本就存在**时才提示。

    :param pathorfile: ``'file'`` 或 ``'path'``。
    :param name: 文件路径或目录路径（支持相对路径）。
    :param warning: ``'yes'`` 时，原本已存在就提示。
    """
    if not isinstance(pathorfile, str):
        raise ParameterError(
            "参数 pathorfile 必须是 'file' 或 'path'，收到 {0!r}".format(pathorfile)
        )
    kind = pathorfile.strip().lower()
    if kind not in ('file', 'path'):
        raise ParameterError(
            "参数 pathorfile 必须是 'file' 或 'path'，收到 {0!r}".format(pathorfile)
        )

    warn = as_bool(warning, 'warning')
    target = Path(name)

    if target.exists():
        if warn:
            _note('warning', 'File(path) {0} already exists!'.format(name))
        return target

    if kind == 'path':
        target.mkdir(parents=True, exist_ok=True)
        _note('info', 'Path {0} created!'.format(name))
    else:
        target.parent.mkdir(parents=True, exist_ok=True)
        target.touch()
        _note('info', 'File {0} created!'.format(name))
    return target


def mv_file(original_file_name, new_file_name, folder_name='mv_file'):
    """移动文件，并把这件事记进日志。

    2.x 用的是 ``error`` 级别，成功移动却记成错误；这里改成 ``info``。
    """
    shutil.move(str(original_file_name), str(new_file_name))
    message = 'File {0} moved to {1}'.format(original_file_name, new_file_name)
    write_log(LOG_FILE_STEM, 'CLI', 'info', message, folder_name=folder_name)
    return Path(new_file_name)


def _decode(raw):
    """把子进程输出解码成文本。

    先按 UTF-8 试，失败再退回系统本地编码（中文 Windows 上是 cp936），
    最后用 ``replace`` 兜底，保证不因为一个坏字节就抛异常。
    """
    if not raw:
        return ''
    for encoding in ('utf-8', locale.getpreferredencoding(False) or 'utf-8'):
        try:
            return raw.decode(encoding)
        except UnicodeDecodeError:
            continue
    return raw.decode('utf-8', errors='replace')


def run_cmd(cmd, timeout=None, check=False, base_dir=None):
    """执行一条命令，返回它的标准输出（去掉首尾空白）。

    2.x 的实现只 ``readline()`` 一次就 ``return``，多行输出会丢，而且
    用 ``while True`` + 提前 ``return`` 导致循环形同虚设。这里等进程结束、
    拿完整输出。

    输出会逐行打印到终端，并写进日志文件（stderr 记为 ``warning``）。

    :param cmd: 命令行字符串，交给 shell 执行。
    :param timeout: 超时秒数，``None`` 表示不限。
    :param check: 为 True 时，非零退出码抛 :class:`subprocess.CalledProcessError`。
    :param base_dir: 日志根目录，默认 ``./logs``。
    """
    completed = subprocess.run(
        cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=timeout
    )
    stdout = _decode(completed.stdout)
    stderr = _decode(completed.stderr)

    for line in stdout.splitlines():
        text = line.rstrip()
        if not text:
            continue
        print(text)
        write_log(LOG_FILE_STEM, 'file', 'info', text, base_dir=base_dir)
    for line in stderr.splitlines():
        text = line.rstrip()
        if not text:
            continue
        print(text, file=sys.stderr)
        write_log(LOG_FILE_STEM, 'file', 'warning', text, base_dir=base_dir)

    if check:
        completed.check_returncode()
    return stdout.strip()


def error(exp, linenum, mode='logfly'):
    """2.x 的错误提示助手，保留以兼容老代码。

    新代码不要再用它：现在参数错误直接抛
    :class:`~logfly.errors.ParameterError`，不需要"打印一行就算"了。
    """
    if mode == 'logfly':
        message = (
            'ERROR occurred! at row ' + str(linenum) + '\r\n\r\n' + str(exp) + '\r\n\r\n'
            'please re-check it! \r\nAnd you can see the manual at '
            'https://github.com/tinqlo/logfly '
        )
        _note('error', message)
        return
    if mode == 'only print':
        print(
            'ERROR occurred!\r\n\r\n' + str(exp) + '\r\n\r\nplease re-check it! \r\n'
            'And you can see the manual at https://github.com/tinqlo/logfly '
        )
        return
    raise ParameterError(
        "参数 mode 必须是 'logfly' 或 'only print'，收到 {0!r}".format(mode)
    )
