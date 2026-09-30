# Diagnosis and recovery runbook

## Evidence ladder

| Observation | Establishes | Does not establish |
| --- | --- | --- |
| Environment listed / `ready` | Configuration was recorded in the queried source | Current connectivity or successful execution |
| Proxy listener running | A local process accepts connections | Reachability of the specific cloud endpoint |
| Proxy CONNECT 200 | Proxy accepted the tunnel request | Target TLS handshake or WebSocket upgrade |
| Verified TLS plus HTTP response | That test route reached an HTTP peer for the domain | Account access, WebSocket authentication, or task execution |
| Original Desktop `initialized=true` / `connected` | Native cloud transport initialized at that time | Success of a later task |
| Native cloud read succeeds | Authenticated read/control path works for that request | Create/execute permissions or workload health |
| Original task returns its expected result | End-to-end success for that action | General stability across restarts and future releases |

## Portable helper

Python 3.10+ is required. Network probes also require `curl` (`curl.exe` on Windows). The helper only reads logs or sends unauthenticated HEAD requests; it does not edit system settings or read tokens.

```text
python scripts/diagnose.py logs --directory <directory-containing-the-day-log-files> --pid <desktop-pid>
python scripts/diagnose.py probe --url https://<observed-cloud-host>/ --proxy http://127.0.0.1:<port>
```

Run from the skill directory, or use the script's absolute path. Windows Desktop logs have been observed under `%LOCALAPPDATA%\Codex\Logs\YYYY\MM\DD`; confirm the active path for the installed build. The logs command reads `.log` files directly in the specified directory, handles rotation, and groups state transitions by Desktop PID. Do not pass a general home or browser-data directory.

An optional `--target-ip <freshly-verified-public-IPv4>` applies curl's connection override to **both** routes while preserving the original URL, TLS SNI, and certificate checks. This can distinguish DNS/domain-route behavior from reachability of a verified address. Independently verify the address immediately before using it. Never use `-k` / `--insecure` to make a failing test pass.

The probe disables curl's config-file loading and explicitly selects the route. It rejects URL credentials, query strings, and non-loopback proxy endpoints. A curl exit code of zero is transport completion, not a successful cloud task. Probe JSON has no bodies, cookies, headers, raw stderr, or credentials. It does include the requested hostname and resolved addresses: review even compact output before sharing it.

## Interpreting common patterns

| Comparison | Next investigation |
| --- | --- |
| Direct fails, existing proxy succeeds | Does the native failing code path actually use that proxy? |
| Proxy fails for both target and control hostname | Proxy process, listener, upstream, or network issue |
| Proxy works for control but not target | Target-specific route, DNS, service, or filtering |
| Verified target IP works while domain route fails | Resolver or domain-based route; not automatically proven DNS poisoning |
| HTTP works, WebSocket initialization fails | Actual upgrade/authentication path, proxy behavior, and build-specific transport |
| Connection recovers but task creation fails | Task/environment/permission/backend stage; do not assume the network explains it |

A helper's environment variables may differ from Desktop's. Likewise, Node and Electron network paths can use different proxy mechanisms. Read current implementation evidence if necessary; configuration text alone cannot prove the native route.

## Conditional no-restart workaround

Use this only when the evidence specifically supports a native direct path that cannot reach the service, while the user's existing proxy can. It is an advanced, manually reviewed recovery, not an unattended installation procedure.

```text
Original Desktop TLS connection
  -> exact-domain hosts mapping to a dedicated loopback address
  -> loopback-only opaque TCP relay
  -> existing local HTTP CONNECT proxy
  -> freshly verified service address
```

The relay never terminates TLS. The original client verifies the cloud certificate and performs its own authentication. Do not install a CA, intercept tokens, log payloads, or expose the listener on `0.0.0.0`.

Before changing the hosts file:

1. Get authorization for the exact domain, hosts edit, relay process, and expected lifetime. Explain that every local app resolving that domain may be affected. Respect stricter local rules.
2. Verify the existing proxy and target; check the intended loopback port for conflicts. Preserve any existing mapping instead of overwriting it blindly.
3. Prepare a backup of the exact hosts bytes and a uniquely marked block. Detect concurrent changes before writing. Store private backups outside the public repository.
4. Start the scoped relay and verify its TLS-preserving route before directing the real client to it. Keep long-lived connections open; a short test deadline must not silently cut off production WebSockets.
5. Apply only the marked block with the required system privileges. Refresh resolution using an approved OS mechanism; let the existing Desktop reconnect.
6. Use a bounded validation window with automatic rollback on failure. Commit the workaround only after native initialization and a relevant native request succeed.
7. Define cleanup on process exit and reboot **before leaving it active**. Do not leave a persistent hosts override dependent on a transient process. If managed startup/cleanup is not explicitly authorized and implemented, classify the workaround as supervised and remove it before ending supervision or rebooting.

Rollback should remove only the exact owned block from the current file, retain later unrelated edits, refresh DNS, and stop only the dedicated relay. Do not restore a whole stale hosts backup over concurrent edits. Verify resolution and listener state afterward. Restarting or killing Codex is not part of this workaround.

## Duplicate environment records

Read back before retrying creation. Compare immutable environment IDs, repository/ref, version, ownership, and task references. A duplicate name is insufficient grounds for deletion. If one failed attempt created a configuration but failed to start its chat, preserve the configuration and repair the failed stage. Delete only explicitly authorized, specifically identified records after checking dependencies.

## Useful public reports

These are independent user reports, not vendor confirmation that every failure has the same cause:

- [Windows system proxy versus WebSocket behavior, #29958](https://github.com/openai/codex/issues/29958)
- [Remote Control proxy timeout with build-dependent results, #38768](https://github.com/openai/codex/issues/38768)
- [Windows Desktop WebSocket timeout after an update, #48627](https://github.com/openai/codex/issues/48627)

Do not copy third-party launchers, settings, or credentials from issue comments as an automatic repair. Check applicability to the installed build and the failed transport.
