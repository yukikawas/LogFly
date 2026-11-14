#####################
# Author: Yuki Sui
# Date: 2023-8-7
#####################
"""logfly —— 给 Python 入门项目用的简易日志工具。

模块分工::

    logfly.errors    异常类型
    logfly.options   'yes'/'no' 与固定取值的校验
    logfly.clock     时间格式化与时间戳换算
    logfly.sinks     把一行日志写到终端或文件
    logfly.logger    路径解析 + 写入编排（核心）
    logfly.tools     建文件/目录、移动文件、执行命令

2.x 的调用方式全部保留::

    import logfly
    logfly.write_log('name', 'fileCLI', 'info', 'hello')

新增的写法（推荐）::

    log = logfly.get_logger(folder_name='myapp')
    log.info('程序启动')
"""

from .clock import (
    format_compact,
    format_date,
    format_datetime,
    format_time,
    get_time,
    time_transfer,
    timestamp_to_datetime,
    datetime_to_timestamp,
)
from .errors import ParameterERROR, ParameterError
from .logger import (
    DEFAULT_FOLDER,
    DEFAULT_LOG_DIR,
    HIDDEN_DIR,
    LOG_FILE_STEM,
    Logger,
    create_log_folder,
    get_logger,
    hidden_root,
    log_root,
    write_log,
)
from .sinks import HAS_COLORAMA
from .tools import create_or_check_file, error, mv_file, run_cmd

__version__ = '2.6.0'
#: 2.x 的旧变量名，表示 colorama 是否可用。
__colorama_init__ = HAS_COLORAMA

__all__ = [
    # 主接口
    'write_log',
    'get_logger',
    'Logger',
    # 工具
    'create_or_check_file',
    'create_log_folder',
    'mv_file',
    'run_cmd',
    'error',
    # 时间
    'get_time',
    'time_transfer',
    'format_datetime',
    'format_date',
    'format_time',
    'format_compact',
    'timestamp_to_datetime',
    'datetime_to_timestamp',
    # 路径
    'log_root',
    'hidden_root',
    # 常量与异常
    'DEFAULT_FOLDER',
    'DEFAULT_LOG_DIR',
    'HIDDEN_DIR',
    'LOG_FILE_STEM',
    'ParameterError',
    'ParameterERROR',
    'HAS_COLORAMA',
    '__version__',
]
