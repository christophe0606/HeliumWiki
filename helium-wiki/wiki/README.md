# Helium optimization concept map

Use this map to find optimization guidance for Cortex-M55 and Cortex-M85 by concept. Each row identifies a wiki page and summarizes what it covers. Paths are relative to `helium-wiki/`; the links open the corresponding pages.

These pages capture source-reported guidance from Arm's [software development hints and tips article](https://developer.arm.com/community/arm-community-blogs/b/architectures-and-processors-blog/posts/armv8_2d00_m-based-processor-software-development-hints-and-tips) and the [Arm Cortex-M55 Processor Software Optimization Guide](https://support.arm.com/documentation/102692/0101), Cortex-M55 r1p1, Issue 03. The guide's timing and hazard details apply to that M55 revision; they do not establish M85 timing. Check each page's processor, revision, and toolchain conditions before applying it. Instruction timings and scheduling implications do not establish measured application speedups.

## Compiler configuration and vectorization

| ID | Path | Quick description |
| --- | --- | --- |
| `techniques-arm-compiler-mve-target-configuration` | [wiki/techniques/techniques-arm-compiler-mve-target-configuration.md](techniques/techniques-arm-compiler-mve-target-configuration.md) | Match Arm Compiler CPU flags and feature tests to the target's implemented Helium and floating-point features. |
| `techniques-helium-auto-vectorization` | [wiki/techniques/techniques-helium-auto-vectorization.md](techniques/techniques-helium-auto-vectorization.md) | Use compiler diagnostics to identify loop obstacles and refactor C or C++ safely for Helium vectorization. |

## Runtime feature setup and power control

| ID | Path | Quick description |
| --- | --- | --- |
| `techniques-armv81m-feature-initialization` | [wiki/techniques/techniques-armv81m-feature-initialization.md](techniques/techniques-armv81m-feature-initialization.md) | Enable low-overhead branch and Helium access with TrustZone permissions, and account for CP10-dependent M55 scalar-shift timing. |
| `techniques-cortex-m55-epu-retention` | [wiki/techniques/techniques-cortex-m55-epu-retention.md](techniques/techniques-cortex-m55-epu-retention.md) | Balance EPU wake delays and power savings on Cortex-M55 revisions with automatic retention. |

## DSP library migration and numerical precision

| ID | Path | Quick description |
| --- | --- | --- |
| `patterns-cmsis-dsp-helium-migration` | [wiki/patterns/patterns-cmsis-dsp-helium-migration.md](patterns/patterns-cmsis-dsp-helium-migration.md) | Review CMSIS-DSP Helium initializers, coefficient storage, padding, and processing-buffer alignment. |
| `languages-c-float16-half-precision` | [wiki/languages/languages-c-float16-half-precision.md](languages/languages-c-float16-half-precision.md) | Use `_Float16` arithmetic and Helium half-precision data when numerical requirements and compiler support permit. |

## Memory placement and cache behavior

| ID | Path | Quick description |
| --- | --- | --- |
| `hardware-itcm-instruction-data-contention` | [wiki/hardware/hardware-itcm-instruction-data-contention.md](hardware/hardware-itcm-instruction-data-contention.md) | Place frequently read coefficients and literals to avoid competing with instruction fetches in ITCM. |
| `hardware-dtcm-scatter-gather-banks` | [wiki/hardware/hardware-dtcm-scatter-gather-banks.md](hardware/hardware-dtcm-scatter-gather-banks.md) | Arrange eligible accesses across DTCM banks and account for the M55 r1p1 same-bank vector-load penalty. |
| `techniques-armv8m-cache-management` | [wiki/techniques/techniques-armv8m-cache-management.md](techniques/techniques-armv8m-cache-management.md) | Apply Armv8-M cache enable and deactivation ordering and interpret revision-sensitive Cortex-M55 cache events. |
| `techniques-cortex-m55-memory-access-scheduling` | [wiki/techniques/techniques-cortex-m55-memory-access-scheduling.md](techniques/techniques-cortex-m55-memory-access-scheduling.md) | Schedule M55 scalar and MVE memory accesses using encoding-specific timing, gather forwarding, alignment, and overlap constraints. |

## Instruction selection, latency, and execution overlap

| ID | Path | Quick description |
| --- | --- | --- |
| `techniques-cortex-m55-latency-aware-scheduling` | [wiki/techniques/techniques-cortex-m55-latency-aware-scheduling.md](techniques/techniques-cortex-m55-latency-aware-scheduling.md) | Schedule M55 scalar instructions by dependency latency, encoding, shifted operands, stack-pointer updates, and divide costs. |
| `techniques-cortex-m55-thumb-dual-issue` | [wiki/techniques/techniques-cortex-m55-thumb-dual-issue.md](techniques/techniques-cortex-m55-thumb-dual-issue.md) | Select eligible M55 16-bit Thumb encodings while checking issue slots, operands, dependencies, and pairing restrictions. |
| `techniques-cortex-m55-floating-point-scheduling` | [wiki/techniques/techniques-cortex-m55-floating-point-scheduling.md](techniques/techniques-cortex-m55-floating-point-scheduling.md) | Schedule M55 scalar and MVE floating-point work by precision, fused-operation semantics, forwarding, and pipeline hazards. |
| `techniques-helium-instruction-interleaving` | [wiki/techniques/techniques-helium-instruction-interleaving.md](techniques/techniques-helium-instruction-interleaving.md) | Interleave Helium instruction types using M55 two-tick pipelines, forwarding classes, mixed-pipe ordering, and scalar-register write hazards. |

## Branch prediction and loop control

| ID | Path | Quick description |
| --- | --- | --- |
| `techniques-cortex-m-branch-prediction` | [wiki/techniques/techniques-cortex-m-branch-prediction.md](techniques/techniques-cortex-m-branch-prediction.md) | Select revision-specific prediction controls and interpret M55 branch, low-overhead-loop, and scalar/vector overlap timing. |
| `techniques-helium-low-overhead-loop-alignment` | [wiki/techniques/techniques-helium-low-overhead-loop-alignment.md](techniques/techniques-helium-low-overhead-loop-alignment.md) | Align actual low-overhead-loop targets to four-byte boundaries and verify padding in the final assembly. |

