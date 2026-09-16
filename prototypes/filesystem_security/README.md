# Filesystem security prototype

This directory is a pre-production security spike. It is intentionally outside
the Runtime package and is not a supported API.

## Question

Can V2 confinement and publication be implemented with Python's portable path
APIs, or is a native platform backend required?

## Finding

`NATIVE_PATH_BACKEND_REQUIRED`.

Python remains suitable for orchestration, policy, validation, and protocol
logic. Security-sensitive path operations must use native handles:

- Windows: directory/file handles, reparse inspection, file identity, and
  handle-relative NT open/Win32 rename operations;
- Linux: `openat2` where available, otherwise a tested descriptor-relative
  component walk;
- macOS: descriptor-relative component walk with no-follow behavior and explicit
  case/Unicode tests.

## Prototype boundary

The code here proves primitives and exercises hostile fixtures. It must not be
imported by production Runtime. Production mutations remain blocked until the
platform matrix, concurrency, crash recovery, and backend-choice gates pass.

## Current evidence status

- Windows local NTFS and GitHub-hosted Windows NTFS: exercised.
- GitHub-hosted Ubuntu ext4: exercised.
- GitHub-hosted macOS APFS: exercised.
- Network, SMB, NFS, FUSE, and unknown filesystems: unsupported for managed
  mutations in V2.0 unless separately qualified.

This status is evidence-scoped. A green test on one filesystem does not qualify
other filesystem types on the same operating system.
