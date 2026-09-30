# Codex 云连接诊断与定向修复

这是一个可复用的 agent skill，用于定位“云环境能看见，但设置聊天无法开始”等问题，并验证最小范围的修复。

**首版 v0.1.0：诊断脚本 + 受控修复手册，不是自动修改网络的一键安装器。** 本项目非 OpenAI 官方项目。

## 能做什么

- 区分环境已登记、代理可达、云 WebSocket 已初始化、云请求成功、实际任务执行成功。
- 对比直连与当前代理，避免把本地端口存在误判为目标可达。
- 读取同一进程的轮转日志，避免旧日志造成错误结论。
- 创建结果不确定时先回读，避免反复新建同名环境。
- 在确认适用并获得授权后，指导单域名转发等有限范围修复，要求回滚和运行生命周期说明。

## 安装

将 `skills/codex-cloud-connection-repair` 整个目录复制到自己的技能目录，例如 `~/.codex/skills/`。安装前检查内容；已有同名技能时先比较修改，不要直接覆盖。

使用示例：

> 使用 $codex-cloud-connection-repair 排查云设置聊天无法开始的问题，保留现有代理、账户和任务，先验证故障层，再做已授权的最小修复。

技能默认允许自动匹配；调用技能不等于授权改 hosts、开启 TUN、重启进程或删除云环境。

## 已验证与未验证

实际 Windows 案例中，单域名 TCP 转发使原 Desktop 在不重启的情况下恢复云 WebSocket 初始化，并成功读取云聊天。该案例没有完成云任务执行验收，也没有验证无人值守或重启后的持续运行。

原始修复脚本包含固定 IP 和临时后台进程，不能直接作为通用安装器发布。本仓库提供可复用的证据标准、只读诊断工具与修复流程。若采用 hosts + 转发方案，必须先解决目标解析、退出清理、重启和撤销问题。

## 文件入口

- [SKILL.md](skills/codex-cloud-connection-repair/SKILL.md)：代理执行入口。
- [修复手册](skills/codex-cloud-connection-repair/references/runbook.md)：判断、命令、授权和回滚。
- [脱敏案例](skills/codex-cloud-connection-repair/references/case-study.md)：成功依据和限制。
- [中文速览](skills/codex-cloud-connection-repair/skill_overview_zh.html)：本地浏览器可直接打开。

诊断脚本需要 Python 3.10+，网络测试另需 curl；不需要安装 Python 依赖。不要将原始日志、凭据、账户状态、环境 ID、hosts 备份或代理订阅链接上传到 issue。

运行测试：`python -m unittest discover -s tests -v`。首版已在 Windows 本地验证；`examples/github-actions-test.yml` 是可选 CI 示例，尚未启用。需要时，用具备工作流管理权限的凭据将它复制到 `.github/workflows/test.yml`。
