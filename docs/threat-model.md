# Threat model

## Scope and intended use

This project provides input-validation and bookkeeping primitives for an experimental coding-agent workflow. It accepts task configuration, unified-diff text, and filesystem trees, and it can construct a deterministic Docker CLI argument vector for a pre-existing Git worktree. It does not execute tasks, apply patches, create worktrees, start containers, or establish a security boundary.

## Assets and trust assumptions

Potentially sensitive assets include host files, credentials, network services, container runtime access, and the integrity of the checked-out source tree. Task JSON, diff text, and worktree files must be treated as untrusted. The project code and Python interpreter are assumed to be installed from a trusted source, but this assumption is not enforced. A downstream orchestration layer, Docker daemon, kernel, host, image, and registry are outside this repository's control.

## Controls implemented here

- **Configuration:** strict field allowlist and required fields; bounded task ID, description, argument count/length, timeout, and diff-size limit; commands remain separate argv items and reject NUL bytes.
- **Diff intake:** UTF-8 byte limit, mandatory `a/` and `b/` relative path forms (or `/dev/null`), traversal/backslash/NUL rejection, bounded section/hunk counts, hunk-count checks, and metadata-only result. No patch utility is called.
- **Integrity:** recursively hashes regular files with SHA-256, sorts paths for repeatable output, rejects symlinks and special files, and compares expected/current paths and digests.
- **Execution planning:** validates policy values and Docker image reference; produces stable argv ordering rather than a shell string; requests network isolation, read-only root/worktree, reduced privilege, and basic resource limits. Planning performs no subprocess call.

## Out of scope / residual risks

This code does not defend against bugs in the interpreter or OS, filesystem races between validation and later use, malicious repositories or Docker images, daemon compromise, kernel/container escapes, resource exhaustion outside requested Docker controls, dependency supply-chain attacks, denial of service within configured upper bounds, or a downstream consumer that ignores the plan's timeout and policy. A read-only bind mount protects the host worktree from ordinary writes through that mount but does not itself establish isolation. Docker flags may be unsupported, interpreted differently by versions, or overridden externally. They have **not been independently tested or verified as an isolation boundary**.

A production deployment would need independent security review, pinned and verified images, host/daemon hardening, race-resistant file handling, monitoring, policy enforcement and testing on supported runtimes. No deployment is represented here.
