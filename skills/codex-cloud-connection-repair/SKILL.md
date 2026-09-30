---
name: codex-cloud-connection-repair
description: Diagnose Codex Desktop cloud connection failures using native logs and direct-versus-proxy tests, then select and verify a narrowly scoped recovery. Use for cloud setup chats that cannot start, durable-host WebSocket timeouts, or environment creation with uncertain results.
---

# Codex cloud connection repair

Restore the user's intended cloud workflow with evidence from the affected Desktop session. Environment visibility, HTTP reachability, WebSocket initialization, and successful task execution are separate acceptance levels.

## Diagnose before changing anything

1. Record the failing action, exact error, client build, and approximate time. Read the current project instructions, existing incident notes, and relevant current logs. Coordinate with an existing repair owner rather than starting conflicting changes.
2. Check whether the action already created an environment or task. A timeout is an unknown outcome, not proof that creation failed. Keep exact IDs; equal names do not identify duplicates safely. Local catalog caches are evidence of a prior read, not a fresh server read.
3. Select the current Desktop process and all its rotated log segments. Use `scripts/diagnose.py logs --directory <day-directory> --pid <desktop-pid>`. Do not keep tailing a filled `-0.log` after `-1.log` becomes active. Interpret the latest transition; a historical success does not prove current health.
4. Verify the actual cloud endpoint from current logs, supported documentation, or the installed client's relevant code. Do not apply a previous build's endpoint/proxy behavior universally. Inspect only relevant snippets; never dump credentials or entire private state files.
5. Compare the target through the existing proxy and without it with `scripts/diagnose.py probe`. HTTP statuses, including 401/403, can demonstrate TLS/HTTP reachability but do not establish authentication or business success. Compare DNS using independent HTTPS resolvers when needed. A configured proxy port, TCP CONNECT 200, or HTTP 200 alone is insufficient.

For decision rules and commands, read [the runbook](references/runbook.md). For the tested boundary of the originating case, read [the sanitized case study](references/case-study.md).

## Choose the smallest justified recovery

- If the proxy cannot reach the endpoint, investigate its route, resolver, and upstream first. Changing Codex settings cannot repair that path.
- If proxy reachability works but the affected Desktop path fails, inspect that path's proxy support and correlate connection attempts. Shell proxy variables are not evidence about an already-running Desktop process.
- If supported live settings can correct the path, prefer those. Respect the user's restart restrictions. Do not restart, patch application bundles, inject code, disable TLS checks, or broaden network routing as an assumed part of diagnosis.
- A loopback TCP relay with a single-domain hosts mapping is a **conditional workaround**, not a default fix. Use only after confirming this failure mode and obtaining authorization for the exact hosts/network changes. Preserve end-to-end TLS, bind only to loopback, and forward only to the verified target through the existing proxy.
- Before applying such a workaround, prepare and inspect the exact change, original-byte backup, conflict checks, bounded rollback, and process/reboot lifecycle. A hosts mapping must not remain pointed at a stopped relay. Resolve the target afresh through a trusted path; do not copy an IP from this case. No unattended installer is included in this release.

Existing approval remains valid within its scope. A DNS-only approval is not blanket approval for TUN, authentication changes, publication, or deleting cloud environments.

## Verify and finish

1. Verify the changed setting and live listener, preserving TLS certificate validation.
2. Observe the **original** Desktop's latest cloud transition and actual request results. `initialized=true`, `next=connected`, and a successful native cloud read confirm a higher level than a standalone curl probe.
3. Resume the original task when authorized; prefer an existing environment/task over creating another test copy. Do not claim full recovery until that action succeeds. If another owner is testing business execution, report the network result and leave its scope intact.
4. Roll back a failed change. Preserve unrelated edits when restoring a shared file; remove only the owned marked block. Report rollback failures as failures, not cleanup success.
5. Deliver: cause supported by evidence; exact scope changed; verification level reached; remaining limits; shutdown/reboot behavior; and a tested or reviewed rollback path. Keep raw logs, private IDs, proxy credentials, account data, and machine paths out of public artifacts.

Stop unchanged retries once the same failure recurs without new evidence. A reproducible limitation is more useful than accumulating proxy variables, unrelated Git commits, extra environments, or increasingly broad network changes.
