# Limitations

This is a compact portfolio prototype, not a production execution platform or an enterprise/customer system.

- The runner is a **plan builder only**. It neither invokes Docker nor executes task commands. No untrusted code has been run by this project as part of this repository's tests.
- Docker command flags are requested policy, not a verified sandbox. Docker isolation has not been independently verified; behavior depends on daemon, host, kernel, image, configuration, and version.
- The task timeout is carried in the returned plan; an eventual caller must enforce it. Planning does not implement cancellation, output capture, log redaction, or cleanup.
- Diff intake validates structural framing and relative paths only. It does not prove a change is correct, safe, applicable, non-malicious, or semantically equivalent, and it does not apply patches. It supports conventional unified diff sections, not every Git diff extension or binary patch format.
- SHA-256 manifests identify file content at scan time. They are not signed attestations; they do not prevent time-of-check/time-of-use races, detect metadata changes, or protect against a compromised interpreter/host. Symlinks and special files are rejected rather than followed.
- The supplied image reference is syntactically constrained but not pinned, fetched, scanned, or verified.
- No network, credential, filesystem, audit, multi-tenant, or production deployment controls are supplied beyond the requested flags in the proposed command.
- A successful local pytest run demonstrates only that the included tests pass in that environment; it is not a security certification or compatibility guarantee.

Independent review and deployment-specific controls are required before any execution service is built around these primitives.
