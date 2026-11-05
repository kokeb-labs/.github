# Security policy

## Reporting a vulnerability

Report vulnerabilities privately through a GitHub security advisory:

1. Open the affected repository on GitHub.
2. Go to **Security** > **Advisories** > **Report a vulnerability**.
3. Describe the issue, the affected repository and tag or commit, the MCU and board if relevant, and the steps to
   reproduce.

Do not open a public issue, pull request or discussion for a suspected vulnerability.

If you are not sure which repository is affected, report it against the lowest layer you can identify (the driver
rather than the core that uses it). We move it if needed.

## Scope

In scope:

- Chip drivers (`driver-*`), `kb-core`, `kb-hal-common`, `pincfg` and the templates.
- CI and build tooling (`ci-tools`, `espidf-tools`) and the GitHub Actions workflows in every repository, for
  example a secret exposed to a pull request from a fork, or untrusted input reaching a privileged job.
- Code that handles keys, firmware images or updates: secure-element integration, image signing and verification,
  update and rollback paths.

Out of scope: vulnerabilities in third-party code we depend on (ESP-IDF, FreeRTOS, ThreadX, STM32 HAL and similar).
Report those upstream, and tell us too if our use of that code makes the problem exploitable.

## What to expect

- We acknowledge a report within 3 business days.
- We confirm or reject it, share an assessment and a fix plan, and keep you updated in the advisory.
- The fix ships in a tagged release. The advisory is published once that release is out. Reporters are credited if
  they want to be.

## Supported versions

Only the latest release of each repository receives security fixes. Projects that pin an older release should move
to the fixed one.
