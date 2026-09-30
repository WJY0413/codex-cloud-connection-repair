# Codex Cloud Connection Repair

A reusable agent skill for diagnosing Codex Desktop cloud connection failures and verifying a narrowly scoped recovery.

**Status: v0.1.0 — a diagnostic skill and supervised repair playbook.** Includes read-only diagnostic helpers. It is not an unattended network installer or an official OpenAI project.

[中文说明](README.zh-CN.md) · [Skill](skills/codex-cloud-connection-repair/SKILL.md) · [Runbook](skills/codex-cloud-connection-repair/references/runbook.md) · [Case study](skills/codex-cloud-connection-repair/references/case-study.md)

## The problem it addresses

An environment can exist while its setup chat still cannot connect. A proxy can be configured while one native WebSocket path does not use it. A successful curl request can coexist with a failing Desktop session.

This skill separates those stages, compares direct and proxy routes, reads rotated logs, and requires verification in the original application. It also prevents retrying uncertain creates from becoming a collection of duplicate environments.

## Install and use

Copy the folder `skills/codex-cloud-connection-repair` into your agent's skills directory. For Codex, this is typically `~/.codex/skills/`; use your configured Codex home if it differs. Inspect the files before installing. Do not overwrite a locally modified skill without reviewing it.

Example prompt:

> Use $codex-cloud-connection-repair to investigate why my cloud setup chat cannot start. Preserve my current proxy, account, and running tasks. Verify the actual failing stage before proposing changes.

Automatic skill discovery is enabled by default. Invocation never grants permission to edit hosts, change proxies, enable TUN, restart processes, or delete cloud data.

## Included tools

`skills/codex-cloud-connection-repair/scripts/diagnose.py` supports:

- **logs:** summarize allowlisted native cloud connection state from all rotated logs for the selected Desktop PID.
- **probe:** compare unauthenticated HTTPS reachability directly and through an explicitly supplied loopback proxy, with optional freshly verified IPv4 override.

Requirements: Python 3.10+; curl for network probes. No Python packages are needed for the diagnostic helper or tests. Example commands are in the runbook. These helpers do not edit system settings, read authentication stores, or send task prompts.

## Validation and limits

- Unit tests cover rotated-log ordering, separate process instances, exclusion of sensitive log content, and probe argument/route validation.
- A Windows live incident verified that a scoped TCP relay restored native cloud initialization and cloud reads without restarting Desktop.
- End-to-end cloud workload execution and unattended relay lifecycle were **not** validated in that incident.
- Endpoint behavior varies by client version. Determine the current endpoint and transport; do not assume an old workaround applies.
- The optional hosts/relay procedure requires explicit authorization, rollback, and lifecycle planning. The repository deliberately does not ship the original fixed-IP background installer.

Run local tests:

```text
python -m unittest discover -s tests -v
```

An optional GitHub Actions matrix is provided in `examples/github-actions-test.yml`. To enable it in your repository, copy it to `.github/workflows/test.yml` using credentials allowed to manage workflows. CI is not enabled in this initial publication; validation was run locally on Windows.

## Sharing an issue

Describe the client build, failed stage, timestamp, redacted error, and direct/proxy comparison. Include the latest native connection state. Do not upload raw logs, tokens, cookies, private environment IDs, account state, hosts backups, or proxy subscription links. Even compact diagnostic output can contain hostnames/IPs; review it before posting.

MIT licensed. Contributions should include reproducible evidence and a clearly bounded change rather than a universal fix inferred from one case.
