# logfly

一个给 Python 入门项目用的轻量日志工具：一行调用，同时写终端和文件，按天归档。

- 版本：2.6.0
- Python：>= 3.7
- 依赖：`colorama`（可选安装，装上后老式 Windows 控制台也能显示颜色）

## 安装

```bash
pip install -e .

# 需要跑测试时
pip install -e ".[dev]"
```

## 快速开始

最简写法，和 2.x 完全一致：

```python
import logfly

logfly.write_log('app', 'fileCLI', 'info', '程序启动')
```

同一类日志反复写时，把配置绑一次：

```python
log = logfly.get_logger(folder_name='myapp')   # 默认同时写终端和文件

log.info('程序启动')
log.warning('磁盘快满了')
log.error('请求失败')
log.success('检查全部通过')
```

## 日志写在哪

`position` 决定日志出现在哪：

| 取值 | 终端 | 文件 |
| --- | :---: | :---: |
| `'CLI'` | 有 | 无 |
| `'file'` | 无 | 有 |
| `'fileCLI'` | 有 | 有 |

文件路径：

```
./logs/<folder_name>/<YYYY-MM-DD>/<name>-<YYYY-MM-DD>.log
```

`hidden='yes'` 时再存一份到用户主目录：

```
~/.1o9f1y/<folder_name>/<YYYY-MM-DD>/<name>-<YYYY-MM-DD>.log
```

## write_log 参数

| 参数 | 默认值 | 说明 |
| --- | --- | --- |
| `name` | 必填 | 日志文件名，日期和 `.log` 自动拼接 |
| `position` | 必填 | `'CLI'` / `'file'` / `'fileCLI'` |
| `level` | 必填 | 自定义级别，写入时转大写并加方括号 |
| `message` | 必填 | 日志正文 |
| `mode` | `'add'` | `'add'` 按天追加；`'new'` 每次调用生成新文件（文件名带 `YYYYMMDDHHMMSS`） |
| `folder_name` | `'default-log'` | `logs` 下的子目录名 |
| `hidden` | `'no'` | `'yes'` 时在主目录再存一份副本 |
| `color` | `'yes'` | 终端输出是否带颜色 |
| `str_message` | `'yes'` | 是否先对 `message` 调用 `str()`；设为 `'no'` 时 `message` 必须是 `str` |
| `base_dir` | `None` | 日志根目录，默认 `./logs` |

几个补充：

- 所有 `'yes'` / `'no'` 开关也接受 `True` / `False`；`position` 和 `mode` 不区分大小写。
- 返回写入的日志文件路径；只写终端时返回 `None`。
- 参数不合法抛 `logfly.ParameterError`（`ValueError` 子类），不再静默返回 `None`。

## 日志格式

文件里每行长这样：

```
2023-08-07 18:30:05 [INFO] message
```

终端输出会多带一个文件名：

```
app 2023-08-07 18:30:05 [INFO] message
```

文件行尾用 CRLF，和 2.x 生成的日志保持一致，旧日志的解析脚本不用改。

## 其他工具函数

| 函数 | 作用 |
| --- | --- |
| `create_or_check_file('file' 或 'path', name, warning='yes')` | 文件/目录不存在就创建；原本已存在时按 `warning` 提示 |
| `create_log_folder(folder_name, hidden='no', base_dir=None)` | 建好当天要用的日志目录，返回路径 |
| `mv_file(src, dst, folder_name='mv_file')` | 移动文件并记一条日志 |
| `run_cmd(cmd, timeout=None, check=False, base_dir=None)` | 执行命令，逐行打印并记录，返回完整标准输出 |
| `get_time(flag)` | 取 `'datetime'` / `'date'` / `'times'` / `'datetimefile'` / `'timestamp'` |
| `timestamp_to_datetime(ts)` | 时间戳（秒级或毫秒级）转 `YYYY-MM-DD HH:MM:SS` |
| `datetime_to_timestamp(s)` | `YYYY-MM-DD HH:MM:SS` 或 `datetime` 对象转时间戳 |
| `time_transfer(ts, flag)` | 上面两个的 2.x 兼容写法 |

## 2.6 的改动

- **出错抛异常**：参数不合法抛 `ParameterError`，不再打印一行后返回 `None`。旧名 `ParameterERROR` 仍可用。
- **新增 `base_dir`**：日志目录可配置，测试因此不依赖当前工作目录。
- **`run_cmd` 返回完整输出**：原来只 `readline()` 一次就返回，多行输出会丢；解码顺序也从 GBK 优先改成 UTF-8 优先，修掉中文乱码。
- **`create_or_check_file`**：创建成功后不再误报 `already exists`。
- **`mv_file`**：移动成功记 `info`，原来错记为 `error`。
- **并发安全**：多线程写同一个文件不会出现半行交错。
- **路径校验**：`name` / `folder_name` 拒绝 `/`、`\`、`..`，日志不会写到目录外。

刻意保留的行为：`mode='new'` 每次调用覆盖同名文件；隐藏副本始终追加。

## 项目结构

```
src/logfly/
├── __init__.py   公开接口（只做导出）
├── errors.py     ParameterError
├── options.py    'yes'/'no' 与固定取值的校验
├── clock.py      时间格式化与时间戳换算
├── sinks.py      把一行日志写到终端或文件
├── logger.py     路径解析 + 写入编排（核心）
└── tools.py      建文件/目录、移动文件、执行命令
tests/
└── test_logfly.py
```

## 运行测试

```bash
pytest
```

## 许可证

MIT
