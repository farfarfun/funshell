# 更新日志

## [未发布]

### 修复

- `kill.py` 的 `kill_process` 日志误用 stdlib logging 的 `%s` 占位符，farlog（loguru）
  不支持该语法，参数被静默丢弃；改为 `{}` 占位符。
- 修正 `kill.py` 模块 docstring 示例中不存在的 `scripts.find_port` 导入路径，改为
  实际可用的 `funshell.kill`/`funshell` 导入。
- 为 CLI 入口 `main()` 补充中文 docstring。

### 新增

- 将 `ruff` 纳入 `[dependency-groups] dev`，使 lint/format 检查可通过 `uv run` 复现。

### 变更

- 不再跟踪并忽略 `uv.lock`；该文件仅反映 1.0.23 发布时的历史状态。
- README 改为中文，补充 Python ">=3.10" 版本要求与 `lsof`/`ss` 系统依赖说明；
  `pyproject.toml` 与 GitHub 仓库 description 同步补充端口/进程查询与终止能力说明；
  新增 `find_by_name` 按完整命令行匹配、可能匹配到自身进程的使用提示。

## [1.0.23] - 2026-09-21

### 新增

- 增加可复现的 `uv.lock` 依赖锁定文件。

### 修复

- 修正 README 示例导入路径，并让进程终止 API 正确报告失败结果。

### 变更

- 使用 Python 3.10 内置泛型写法，补齐测试依赖版本下限。

### 废弃

- 无。
