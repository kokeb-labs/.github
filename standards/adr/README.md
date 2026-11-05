# Architecture decision records

Why the Kokeb Labs standard is what it is. Each record is one decision in the Context / Decision / Consequences
form, numbered in the order it was accepted. A record is never edited to change its decision; a new record
supersedes it, and the old one gets a `Superseded by ADR-NNNN` status.

| ADR | Decision | Status |
| --- | --- | --- |
| [0001](0001-error-model.md) | Drivers keep `<chip>::Error` and `Result<T>`; handlers map to `kb::Status` | Accepted |
| [0002](0002-lifecycle.md) | One lifecycle: I/O-free constructor, `Initialize()`, `EnsureInitialized()` | Accepted |
| [0003](0003-crtp-ports.md) | Drivers are templates on a CRTP port constrained by a concept | Accepted |
| [0004](0004-no-heap.md) | No heap in drivers; none after start-up anywhere | Accepted |
| [0005](0005-kb-hal-common.md) | A shared `kb-hal-common` repository; board HALs live with their products | Accepted |
| [0006](0006-freertos-1khz-tick.md) | FreeRTOS at 1 kHz everywhere; a delay waits at least the requested time | Accepted |
| [0007](0007-submodule-pinning-and-tags.md) | Drivers pinned in kb-core to release tags; `driver.yml`, `catalog/compat.yml` and release trains | Accepted |
| [0008](0008-naming.md) | One naming scheme, enforced by `clang-tidy` | Accepted |
| [0009](0009-licensing.md) | MIT for firmware and tooling; CERN-OHL-P-2.0 for hardware designs | Accepted |
| [0010](0010-cpp20.md) | C++20 in every repository | Accepted |
| [0011](0011-repository-root-layout.md) | The root holds only required and first-read files; tool configuration in `_config/`; platform code only in `examples/<platform>/` | Accepted |
| [0012](0012-unbranded-drivers.md) | Drivers carry no brand: `driver-<chip>`, `namespace <chip>`, `<chip>::<chip>` | Accepted |
| [0013](0013-kb-core-monorepo.md) | kb-core is one monorepo with four targets and one version | Accepted |
| [0014](0014-three-kinds-of-specific.md) | Chip-, MCU- and product-specific code each have one place | Accepted |
| [0015](0015-solo-maintainer-governance.md) | Governance for one maintainer, open to contributors | Accepted |

## Format

```markdown
# ADR-NNNN: <decision as a short sentence>

- Status: Proposed | Accepted | Superseded by ADR-NNNN
- Date: YYYY-MM-DD

## Context

What forced a decision: the problem, the constraints, the options considered.

## Decision

What we do, stated as rules.

## Consequences

What gets better, what gets worse, and what has to change in which repositories.
```

A new record is added in the same PR as the change to the standard it explains. It is proposed in a PR to
`kokeb-labs/.github` and stays open for comment for at least seven days unless it fixes a defect.

## Where the decisions came from

Records 0001 to 0011 were accepted on 3 November 2026, after a read-only review of the code the standard grew
from (drivers, libraries, HALs and products) against one checklist: API shape, port, errors, start-up, config,
memory and threading, naming, build, tests and docs. The review found the repository shell, docs and CI already
uniform, and the C++ contracts not: 5 error models, 6 start-up styles, about 8 spellings of the same port hooks,
two handler families, drifting HALs and about 45 error types.

When the standard was set up for Kokeb Labs on 5 November 2026, those records were rewritten for the new org
(names, licence, the kb-core layout), and records 0012 to 0015 were added. From then on, the rule at the top of
this page applies.

The order of work:

1. **Write it down**: this standard, the org clang configs, `kokeb-labs/driver-template` and `ci-tools`.
2. **kb-core skeleton**: `utils` with `kb::Status`, `rtos`, `interfaces` with `ToStatus()`, each its own target,
   with the MCU gate and `catalog/compat.yml`.
3. **Drivers**, in parallel, each released as `driver-<chip>` with its `driver.yml`, and each landing with its
   kb-core handler.
4. **kb-core handlers** on one family, with shared adapter bases.
5. **kb-hal-common**: the shared managers, facade base, bind interface, lints and an example board HAL;
   `board-hal-template` after it.
6. **The first release train**, then the STM32 compile job and bind.
