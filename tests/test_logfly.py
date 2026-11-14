"""logfly 的测试。

所有测试都把 ``base_dir`` 指向 pytest 的临时目录，绝不往项目里写
``logs/``——这样测试不依赖当前工作目录，也不会互相污染。
"""

import threading

import pytest

import logfly
from logfly import ParameterError

FROZEN_DATE = '2023-08-07'
FROZEN_DATETIME = '2023-08-07 18:30:05'
FROZEN_COMPACT = '20230807183005'


@pytest.fixture
def frozen(monkeypatch):
    """冻结时间，让文件名和日志内容可以精确断言。"""
    monkeypatch.setattr(logfly.clock, 'format_date', lambda when=None: FROZEN_DATE)
    monkeypatch.setattr(logfly.clock, 'format_datetime', lambda when=None: FROZEN_DATETIME)
    monkeypatch.setattr(logfly.clock, 'format_compact', lambda when=None: FROZEN_COMPACT)


@pytest.fixture
def hidden_dir(tmp_path, monkeypatch):
    """把隐藏日志目录换到临时目录，不去碰真实的用户主目录。"""
    target = tmp_path / 'home-hidden'
    monkeypatch.setattr(logfly.logger, 'hidden_root', lambda: target)
    return target


def log_path(base, name, folder='default-log', date=FROZEN_DATE):
    return base / folder / date / '{0}-{1}.log'.format(name, date)


def read_exact(path):
    """按原样读文件内容。

    ``Path.read_text`` 会做通用换行转换，把 ``\\r\\n`` 变成 ``\\n``，
    这样就看不出我们刻意保留的 CRLF 了，所以这里用 ``newline=''``。
    """
    with open(str(path), encoding='utf-8', newline='') as handle:
        return handle.read()


# ---------------------------------------------------------------- 版本

def test_version():
    assert logfly.__version__.startswith('2.')


# ---------------------------------------------------------------- 写入位置

def test_file_position_writes_file_only(tmp_path, frozen, capsys):
    written = logfly.write_log('app', 'file', 'info', 'hello', base_dir=tmp_path)

    path = log_path(tmp_path, 'app')
    assert written == path
    assert read_exact(path) == '2023-08-07 18:30:05 [INFO] hello\r\n'
    assert capsys.readouterr().out == ''


def test_cli_position_prints_and_creates_nothing(tmp_path, frozen, capsys):
    logfly.write_log('app', 'CLI', 'info', 'hello', color='no', base_dir=tmp_path)

    assert capsys.readouterr().out.strip() == 'app 2023-08-07 18:30:05 [INFO] hello'
    # 只写终端时不应该顺手建 logs/ 目录
    assert not (tmp_path / 'default-log').exists()


def test_filecli_position_does_both(tmp_path, frozen, capsys):
    logfly.write_log('app', 'fileCLI', 'warning', 'careful', color='no', base_dir=tmp_path)

    assert 'app 2023-08-07 18:30:05 [WARNING] careful' in capsys.readouterr().out
    assert '[WARNING] careful' in log_path(tmp_path, 'app').read_text(encoding='utf-8')


def test_position_is_case_insensitive(tmp_path, frozen, capsys):
    logfly.write_log('app', 'filecli', 'info', 'x', color='no', base_dir=tmp_path)
    assert '[INFO] x' in log_path(tmp_path, 'app').read_text(encoding='utf-8')


# ---------------------------------------------------------------- 模式

def test_mode_add_appends(tmp_path, frozen):
    logfly.write_log('app', 'file', 'info', 'first', base_dir=tmp_path)
    logfly.write_log('app', 'file', 'info', 'second', base_dir=tmp_path)

    lines = log_path(tmp_path, 'app').read_text(encoding='utf-8').splitlines()
    assert lines == [
        '2023-08-07 18:30:05 [INFO] first',
        '2023-08-07 18:30:05 [INFO] second',
    ]


def test_mode_new_overwrites(tmp_path, frozen):
    logfly.write_log('app', 'file', 'info', 'first', base_dir=tmp_path)
    logfly.write_log('app', 'file', 'info', 'second', mode='new', base_dir=tmp_path)

    path = tmp_path / 'default-log' / FROZEN_DATE / 'app-{0}.log'.format(FROZEN_COMPACT)
    assert read_exact(path) == '2023-08-07 18:30:05 [INFO] second\r\n'


def test_custom_folder_name(tmp_path, frozen):
    logfly.write_log('app', 'file', 'info', 'x', folder_name='myapp', base_dir=tmp_path)
    assert log_path(tmp_path, 'app', folder='myapp').exists()


# ---------------------------------------------------------------- 隐藏副本

def test_hidden_writes_second_copy(tmp_path, frozen, hidden_dir):
    logfly.write_log('app', 'file', 'info', 'secret', hidden='yes', base_dir=tmp_path)

    assert '[INFO] secret' in log_path(tmp_path, 'app').read_text(encoding='utf-8')
    shadow = hidden_dir / 'default-log' / FROZEN_DATE / 'app-{0}.log'.format(FROZEN_DATE)
    assert '[INFO] secret' in shadow.read_text(encoding='utf-8')


def test_hidden_accepts_boolean(tmp_path, frozen, hidden_dir):
    logfly.write_log('app', 'file', 'info', 'x', hidden=True, base_dir=tmp_path)
    assert (hidden_dir / 'default-log' / FROZEN_DATE).is_dir()


# ---------------------------------------------------------------- 颜色

def test_color_yes_emits_ansi(tmp_path, frozen, capsys):
    logfly.write_log('app', 'CLI', 'error', 'boom', color='yes', base_dir=tmp_path)
    assert '\033[' in capsys.readouterr().out


def test_color_no_is_plain(tmp_path, frozen, capsys):
    logfly.write_log('app', 'CLI', 'error', 'boom', color='no', base_dir=tmp_path)
    assert '\033[' not in capsys.readouterr().out


# ---------------------------------------------------------------- 参数校验

@pytest.mark.parametrize('position', ['stdout', '', None, 1])
def test_invalid_position_raises(tmp_path, position):
    with pytest.raises(ParameterError):
        logfly.write_log('app', position, 'info', 'x', base_dir=tmp_path)


def test_invalid_mode_raises(tmp_path):
    with pytest.raises(ParameterError):
        logfly.write_log('app', 'file', 'info', 'x', mode='append', base_dir=tmp_path)


def test_invalid_switch_raises(tmp_path):
    with pytest.raises(ParameterError) as excinfo:
        logfly.write_log('app', 'file', 'info', 'x', hidden='maybe', base_dir=tmp_path)
    assert 'hidden' in excinfo.value.args[0]


def test_parameter_error_is_valueerror():
    assert issubclass(ParameterError, ValueError)
    assert logfly.ParameterERROR is ParameterError


@pytest.mark.parametrize('name', ['../evil', 'sub/dir', 'sub\\dir', ''])
def test_name_cannot_escape_log_dir(tmp_path, name):
    with pytest.raises(ParameterError):
        logfly.write_log(name, 'file', 'info', 'x', base_dir=tmp_path)


def test_str_message_no_requires_str(tmp_path, frozen):
    with pytest.raises(ParameterError):
        logfly.write_log('app', 'file', 'info', 123, str_message='no', base_dir=tmp_path)


def test_str_message_default_converts(tmp_path, frozen):
    logfly.write_log('app', 'file', 'info', 123, base_dir=tmp_path)
    assert '[INFO] 123' in log_path(tmp_path, 'app').read_text(encoding='utf-8')


# ---------------------------------------------------------------- 时间

@pytest.mark.parametrize('flag,expected', [
    ('datetime', FROZEN_DATETIME),
    ('date', FROZEN_DATE),
])
def test_get_time_string_flags(frozen, flag, expected):
    assert logfly.get_time(flag) == expected


def test_get_time_timestamp_is_number():
    assert isinstance(logfly.get_time('timestamp'), float)


def test_get_time_invalid_raises():
    with pytest.raises(ParameterError):
        logfly.get_time('oops')


def test_timestamp_to_datetime_handles_seconds_and_millis(monkeypatch):
    monkeypatch.setattr(logfly.clock.time, 'localtime', lambda secs=None: (2023, 8, 7, 18, 30, 5, 0, 219, 0))
    assert logfly.timestamp_to_datetime(1691404205) == '2023-08-07 18:30:05'
    assert logfly.timestamp_to_datetime(1691404205000) == '2023-08-07 18:30:05'


def test_timestamp_to_datetime_invalid_raises():
    with pytest.raises(ParameterError):
        logfly.timestamp_to_datetime('not-a-number')


def test_datetime_roundtrip():
    seconds = logfly.datetime_to_timestamp(FROZEN_DATETIME)
    assert logfly.timestamp_to_datetime(seconds) == FROZEN_DATETIME


def test_datetime_to_timestamp_invalid_raises():
    with pytest.raises(ParameterError):
        logfly.datetime_to_timestamp('2023/08/07')


def test_time_transfer_invalid_flag_raises():
    with pytest.raises(ParameterError):
        logfly.time_transfer(1691404205, 'oops')


# ---------------------------------------------------------------- create_or_check_file

def test_create_file_reports_created(tmp_path, frozen, capsys):
    target = tmp_path / 'new.txt'
    assert logfly.create_or_check_file('file', str(target)) == target
    assert target.exists()

    out = capsys.readouterr().out
    assert 'created!' in out
    assert 'already exists' not in out


def test_create_file_reports_existing(tmp_path, frozen, capsys):
    target = tmp_path / 'new.txt'
    target.write_text('', encoding='utf-8')

    logfly.create_or_check_file('file', str(target))
    assert 'already exists' in capsys.readouterr().out


def test_create_file_warning_off_is_silent(tmp_path, frozen, capsys):
    target = tmp_path / 'new.txt'
    target.write_text('', encoding='utf-8')

    logfly.create_or_check_file('file', str(target), warning='no')
    assert capsys.readouterr().out == ''


def test_create_path(tmp_path, frozen):
    target = tmp_path / 'a' / 'b'
    logfly.create_or_check_file('path', str(target))
    assert target.is_dir()


def test_create_or_check_file_invalid_kind(tmp_path):
    with pytest.raises(ParameterError):
        logfly.create_or_check_file('folder', str(tmp_path / 'x'))


# ---------------------------------------------------------------- run_cmd

def test_run_cmd_returns_output(tmp_path):
    assert logfly.run_cmd('echo 1111', base_dir=tmp_path) == '1111'


def test_run_cmd_logs_output(tmp_path, frozen):
    logfly.run_cmd('echo hello-cmd', base_dir=tmp_path)
    content = log_path(tmp_path, 'logfly-log').read_text(encoding='utf-8')
    assert '[INFO] hello-cmd' in content


def test_run_cmd_check_raises(tmp_path):
    with pytest.raises(Exception):
        logfly.run_cmd('exit 1', check=True, base_dir=tmp_path)


# ---------------------------------------------------------------- 并发

def test_concurrent_writes_do_not_interleave(tmp_path, frozen, capsys):
    log = logfly.get_logger(base_dir=tmp_path, position='file', color='no')

    def worker(index):
        for round_index in range(20):
            log.write('INFO', 't{0}-{1}'.format(index, round_index))

    threads = [threading.Thread(target=worker, args=(i,)) for i in range(8)]
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join()

    lines = log_path(tmp_path, 'logfly-log').read_text(encoding='utf-8').splitlines()
    assert len(lines) == 160
    for line in lines:
        assert line.startswith('2023-08-07 18:30:05 [INFO] t')


# ---------------------------------------------------------------- Logger 便捷接口

def test_get_logger_convenience_methods(tmp_path, frozen, capsys):
    log = logfly.get_logger(base_dir=tmp_path, position='fileCLI', color='no')
    log.info('i')
    log.warning('w')
    log.error('e')
    log.success('s')

    content = log_path(tmp_path, 'logfly-log').read_text(encoding='utf-8')
    for level in ('INFO', 'WARNING', 'ERROR', 'PASS'):
        assert '[{0}]'.format(level) in content

    out = capsys.readouterr().out
    assert '[PASS] s' in out
