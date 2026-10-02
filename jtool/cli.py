"""jtool 命令行界面。

子命令:
    fmt       格式化输出 JSON
    get       按点路径取值，如 a.b.0
    keys      列出顶层所有 key
    validate  校验 JSON 是否合法

每个子命令都可以传文件路径，也可以从 stdin 管道读：
    cat data.json | python -m jtool fmt
"""
import argparse
import json
import sys
from pathlib import Path


def read_text(file):
    """读输入：给了文件就读文件，否则读 stdin。"""
    if file:
        return Path(file).read_text(encoding="utf-8")
    data = sys.stdin.read()
    if not data.strip():
        raise SystemExit("错误：没有输入。请传文件路径，或用管道把 JSON 传进来。")
    return data


def parse(text):
    """解析 JSON，失败时直接报错退出（exit 1）。"""
    try:
        return json.loads(text)
    except json.JSONDecodeError as e:
        raise SystemExit(f"JSON 解析失败：{e}")


def get_path(obj, dotted):
    """按点路径取值，数字段表示列表下标，如 ``a.b.0``。

    找不到时抛 KeyError，调用方负责转成友好的错误信息。
    """
    cur = obj
    for part in dotted.split("."):
        if isinstance(cur, list):
            try:
                idx = int(part)
            except ValueError:
                raise KeyError(f"列表下标必须是数字，得到 {part!r}")
            try:
                cur = cur[idx]
            except IndexError:
                raise KeyError(f"列表下标越界：{part}")
        elif isinstance(cur, dict):
            if part not in cur:
                raise KeyError(f"找不到 key：{part!r}")
            cur = cur[part]
        else:
            raise KeyError(f"无法在 {type(cur).__name__} 上继续取值：{part!r}")
    return cur


def fmt_value(value):
    """查询结果的打印：对象/数组转 JSON，标量直接打印。"""
    if isinstance(value, (dict, list)):
        return json.dumps(value, ensure_ascii=False, indent=2)
    return str(value)


def cmd_fmt(args):
    obj = parse(read_text(args.file))
    print(json.dumps(obj, ensure_ascii=False, indent=args.indent))


def cmd_get(args):
    obj = parse(read_text(args.file))
    try:
        value = get_path(obj, args.path)
    except KeyError as e:
        raise SystemExit(f"错误：{e}")
    print(fmt_value(value))


def cmd_keys(args):
    obj = parse(read_text(args.file))
    if not isinstance(obj, dict):
        raise SystemExit("错误：顶层不是对象，没有 keys 可列。")
    for k in obj:
        print(k)


def cmd_validate(args):
    text = read_text(args.file)
    try:
        json.loads(text)
    except json.JSONDecodeError as e:
        raise SystemExit(f"不合法：{e}")
    name = args.file or "stdin"
    print(f"OK：{name} 是合法 JSON")


def build_parser():
    p = argparse.ArgumentParser(
        prog="jtool",
        description="JSON 小工具：格式化、按路径查询、列 key、校验合法性",
    )
    sub = p.add_subparsers(dest="cmd", required=True, metavar="子命令")

    f = sub.add_parser("fmt", help="格式化输出 JSON")
    f.add_argument("file", nargs="?", help="JSON 文件，不传则从 stdin 读")
    f.add_argument("--indent", type=int, default=2, help="缩进空格数（默认 2）")
    f.set_defaults(func=cmd_fmt)

    g = sub.add_parser("get", help="按点路径取值，如 a.b.0")
    g.add_argument("path", help="点路径，如 config.servers.0.host")
    g.add_argument("file", nargs="?", help="JSON 文件，不传则从 stdin 读")
    g.set_defaults(func=cmd_get)

    k = sub.add_parser("keys", help="列出顶层所有 key")
    k.add_argument("file", nargs="?", help="JSON 文件，不传则从 stdin 读")
    k.set_defaults(func=cmd_keys)

    v = sub.add_parser("validate", help="校验 JSON 是否合法")
    v.add_argument("file", nargs="?", help="JSON 文件，不传则从 stdin 读")
    v.set_defaults(func=cmd_validate)

    return p


def main(argv=None):
    args = build_parser().parse_args(argv)
    args.func(args)


if __name__ == "__main__":
    main()
