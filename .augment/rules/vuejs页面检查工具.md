---
type: "agent_requested"
description: "vuejs前端检查工具（不要使用curl测试vuejs前端）"
---
由于vuejs使用js渲染前端，直接通过curl检查只能得到底层html的代码，无法看见真实前端页面结构。
可以使用playwright-mcp工具，通过其中的工具：截图、描述等操作检查真实前端页面。
所有涉及vue前端的检查都要使用该mcp。