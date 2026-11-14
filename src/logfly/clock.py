"""时间格式化与时间戳换算。

2.x 用一条 ``flag`` 字符串在 ``get_time`` / ``time_transfer`` 里分支，
拼错时同样静默返回 ``None``（于是 ``'\\\\.1o9f1y\\\\' + None`` 才炸）。
这里改成分工明确的小函数，非法输入立刻抛异常；
``get_time`` / ``time_transfer`` 作为兼容包装保留下来。
"""

import time

from .errors import ParameterError

#: 写进日志文件的时间格式，例如 ``2023-08-07 18:30:05``。
DATETIME_FORMAT = '%Y-%m-%d %H:%M:%S'
#: 日期目录名，例如 ``2023-08-07``。
DATE_FORMAT = '%Y-%m-%d'
#: 只到秒的时间，例如 ``18:30:05``。
TIME_FORMAT = '%H:%M:%S'
#: ``mode='new'`` 时用的紧凑时间，例如 ``20230807183005``。
COMPACT_FORMAT = '%Y%m%d%H%M%S'

#: 时间戳超过这个量级就当作毫秒。
#: 2.x 用 ``len(str(ts)) == 13`` 判断，2033 年之后 10 位秒级时间戳会变成
#: 11 位，那种长度判断就失效了；按数值判断不会过时。
_MILLISECOND_THRESHOLD = 1e11


def format_datetime(when=None):
    """返回 ``YYYY-MM-DD HH:MM:SS``。``when`` 为空表示当前时间。"""
    return time.strftime(DATETIME_FORMAT, time.localtime(when))


def format_date(when=None):
    """返回 ``YYYY-MM-DD``，用于日志目录名。"""
    return time.strftime(DATE_FORMAT, time.localtime(when))


def format_time(when=None):
    """返回 ``HH:MM:SS``。"""
    return time.strftime(TIME_FORMAT, time.localtime(when))


def format_compact(when=None):
    """返回 ``YYYYMMDDHHMMSS``，用于 ``mode='new'`` 的文件名。"""
    return time.strftime(COMPACT_FORMAT, time.localtime(when))


def timestamp():
    """返回当前 Unix 时间戳（浮点秒）。"""
    return time.time()


def _to_seconds(value):
    """把秒级或毫秒级时间戳统一成秒。"""
    try:
        number = float(value)
    except (TypeError, ValueError):
        raise ParameterError(
            '参数 time_stamp 必须是数字（秒级或毫秒级时间戳），收到 {0!r}'.format(value)
        )
    if abs(number) >= _MILLISECOND_THRESHOLD:
        number /= 1000.0
    return number


def timestamp_to_datetime(value):
    """秒级 / 毫秒级时间戳 -> ``YYYY-MM-DD HH:MM:SS``。"""
    return time.strftime(DATETIME_FORMAT, time.localtime(_to_seconds(value)))


def datetime_to_timestamp(value):
    """``YYYY-MM-DD HH:MM:SS`` -> 秒级时间戳。

    也接受 :class:`datetime.datetime` 对象，省得调用方自己转字符串。
    """
    if hasattr(value, 'timetuple'):  # datetime / date 对象
        return time.mktime(value.timetuple())
    if isinstance(value, str):
        try:
            return time.mktime(time.strptime(value, DATETIME_FORMAT))
        except ValueError:
            raise ParameterError(
                '参数 time_stamp 必须形如 "2023-08-07 18:30:05"，收到 {0!r}'.format(value)
            )
    raise ParameterError(
        '参数 time_stamp 必须是 "YYYY-MM-DD HH:MM:SS" 字符串或 datetime，收到 {0!r}'.format(value)
    )


def get_time(flag):
    """2.x 兼容接口：按 ``flag`` 取不同粒度的时间。

    支持 ``'datetime'`` / ``'date'`` / ``'times'`` / ``'datetimefile'`` /
    ``'timestamp'``。新代码建议直接调用上面那些具体函数。
    """
    if flag == 'datetime':
        return format_datetime()
    if flag == 'date':
        return format_date()
    if flag == 'times':
        return format_time()
    if flag == 'datetimefile':
        return format_compact()
    if flag == 'timestamp':
        return timestamp()
    raise ParameterError(
        '参数 flag 必须是 "datetime" / "date" / "times" / "datetimefile" / "timestamp" 之一，'
        '收到 {0!r}'.format(flag)
    )


def time_transfer(time_stamp, flag='timestamp2datetime'):
    """2.x 兼容接口：时间戳与日期时间字符串互转。"""
    if flag == 'timestamp2datetime':
        return timestamp_to_datetime(time_stamp)
    if flag == 'datetime2timestamp':
        return datetime_to_timestamp(time_stamp)
    raise ParameterError(
        '参数 flag 必须是 "timestamp2datetime" 或 "datetime2timestamp"，收到 {0!r}'.format(flag)
    )
