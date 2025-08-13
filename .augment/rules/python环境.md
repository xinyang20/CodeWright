---
type: "agent_requested"
description: "python uv pip 包管理"
---
本项目使用uv包管理器，基础命令包括：uv init（初始化项目目录），uv venv <virtualenv_name>（创建虚拟环境），uv add <package_name>（添加第三方包）....其他命令可以通过context7-mcp查看。该项目禁用pip工具，不要使用pip安装或卸载第三方包。
uv包管理器支持本地代理，可以通过 `set HTTP_PROXY=http://127.0.0.1:15236` 和 `set HTTPS_PROXY=http://127.0.0.1:15236` 完成本地代理设置。
注意，启动该项目的python程序时，需要使用 `uv python <filename>` 进行启动，避免无用系统环境导致程序启动失败。