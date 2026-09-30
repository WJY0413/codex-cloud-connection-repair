# Sanitized case: configurations existed, cloud setup chat could not start

## Observed setting

A Windows Codex Desktop build, `26.928.1915.0`, could show cloud environments but a setup chat failed to start. Repeated setup attempts left several environments with the same display name. An existing local HTTP/SOCKS proxy served other traffic.

The native cloud-host log repeatedly showed WebSocket open timeouts, close code 1006, and `initialized=false`. A missing-environment-ID file-read error also occurred, but the failed thread-start requests provided more direct evidence of the blocked stage.

## What changed the conclusion

1. `ready` records established environment configuration, not task execution.
2. Direct and proxy probes initially failed. Later the same proxy reached the target; no proxy configuration had been changed by the repair. Timing alone did not prove causation.
3. Independent HTTPS DNS lookups differed from the machine's result. Using a freshly checked address through the existing proxy completed TLS. This narrowed the problem but did not prove all native traffic would use that route.
4. Inspection of the installed build's relevant code indicated that the public cloud WebSocket path was not supplied the SOCKS proxy used for certain other paths. This was build-specific evidence, not a claim about all Codex versions.
5. A credential-free, TLS-preserving loopback relay test succeeded. After the user authorized the exact hosts and runtime change, that route was applied to the original client.

## Verified result

Without restarting Codex, the existing Desktop's next reconnect completed native initialization: `initialized=true`, `next=connected`, and retry count zero. The relay held a live connection, and native tools could list/read cloud chats.

This is evidence of **native cloud connectivity and read recovery**. A complete cloud workload was not executed as part of this repair, and a separate task-creation failure was not attributed to the local network without evidence. Duplicate environments were retained.

## What the first workaround did not solve

The initial relay used a manually verified address and a transient process. Its hosts entry persisted, so it was not reboot-safe or an unattended production fix. This repository intentionally does not distribute that machine-specific installer. Its reusable contribution is the diagnostic sequence, scoped recovery design, and verification/rollback criteria.

A reusable implementation must refresh endpoint resolution, account for process lifetime and reboot, and preserve unrelated configuration. Updating an application, changing its supported proxy settings, or a vendor fix may be a better long-term resolution for a different build.

All account IDs, environment IDs, private repository identifiers, local paths, credentials, raw logs, and machine-specific endpoints have been omitted.
