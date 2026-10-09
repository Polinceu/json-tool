# json-tool（jtool）

一个小巧的 JSON 命令行工具：格式化、按路径查询、列顶层 key、校验合法性。
只用 Python 标准库，没有第三方依赖。

## 功能

| 子命令     | 说明                             |
| ---------- | -------------------------------- |
| `fmt`      | 格式化输出 JSON（`--indent` 调缩进） |
| `get`      | 按点路径取值，如 `a.b.0`         |
| `keys`     | 列出顶层所有 key                 |
| `validate` | 校验 JSON 是否合法               |

每个子命令都可以传文件路径，也可以从 stdin 管道读。

## 安装

```bash
cd json-tool
python -m jtool --help
```

## 使用示例

```bash
# 1. 格式化文件（中文不会被转义成 \uXXXX）
$ python -m jtool fmt config.json

# 2. 从管道读
$ cat config.json | python -m jtool fmt --indent 4

# 3. 按路径取深层的值
$ python -m jtool get servers.0.host config.json
db.internal

# 4. 从管道查
$ echo '{"a": {"b": [10, 20]}}' | python -m jtool get a.b.1
20

# 5. 列出顶层 key
$ python -m jtool keys config.json
name
servers
debug

# 6. 校验合法性（合法 exit 0，不合法 exit 1）
$ python -m jtool validate config.json
OK：config.json 是合法 JSON

$ python -m jtool validate broken.json
不合法：Expecting property name enclosed in double quotes: line 1 column 3 (char 2)
```

路径规则：点分隔，数字段表示列表下标，比如 `servers.0.host`
表示取 `servers` 数组第 0 个元素的 `host` 字段。

## 跑测试

```bash
python -m unittest discover -s tests -v
```

## 常见问题

- **中文会被转义成 \uXXXX 吗？** 不会，输出统一用 `ensure_ascii=False`，中文直接显示。
- **get 的路径怎么写？** 点分隔，数字段表示列表下标，比如 `servers.0.host`。
- **大文件能处理吗？** 一次性读入内存，几十 MB 没问题，更大的建议用 jq。
