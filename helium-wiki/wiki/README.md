# Helium optimization concept map

Use this map to find optimization guidance for Cortex-M55 and Cortex-M85 by concept. Each row identifies a wiki page and summarizes what it covers. Paths are relative to `helium-wiki/`; the links open the corresponding pages.

These pages capture source-reported guidance from Arm's [software development hints and tips article](https://developer.arm.com/community/arm-community-blogs/b/architectures-and-processors-blog/posts/armv8_2d00_m-based-processor-software-development-hints-and-tips). Check each page's processor, revision, and toolchain conditions before applying it; the guidance does not establish measured application speedups.

## Compiler configuration and vectorization

| ID | Path | Quick description |
| --- | --- | --- |
| `techniques-arm-compiler-mve-target-configuration` | [wiki/techniques/techniques-arm-compiler-mve-target-configuration.md](techniques/techniques-arm-compiler-mve-target-configuration.md) | Match Arm Compiler CPU flags and feature tests to the target's implemented Helium and floating-point features. |
| `techniques-helium-auto-vectorization` | [wiki/techniques/techniques-helium-auto-vectorization.md](techniques/techniques-helium-auto-vectorization.md) | Use compiler diagnostics to identify loop obstacles and refactor C or C++ safely for Helium vectorization. |

## Runtime feature setup and power control

| ID | Path | Quick description |
| --- | --- | --- |
| `techniques-armv81m-feature-initialization` | [wiki/techniques/techniques-armv81m-feature-initialization.md](techniques/techniques-armv81m-feature-initialization.md) | Enable low-overhead branch and Helium access during privileged startup, including TrustZone permissions. |
| `techniques-cortex-m-branch-prediction` | [wiki/techniques/techniques-cortex-m-branch-prediction.md](techniques/techniques-cortex-m-branch-prediction.md) | Select branch-prediction controls for Cortex-M85 or the applicable Cortex-M55 revision. |
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
| `hardware-dtcm-scatter-gather-banks` | [wiki/hardware/hardware-dtcm-scatter-gather-banks.md](hardware/hardware-dtcm-scatter-gather-banks.md) | Arrange eligible scatter/gather accesses across DTCM banks to allow concurrent data accesses. |
| `techniques-armv8m-cache-management` | [wiki/techniques/techniques-armv8m-cache-management.md](techniques/techniques-armv8m-cache-management.md) | Apply Armv8-M cache enable and deactivation ordering and interpret revision-sensitive Cortex-M55 cache events. |

## Assembly scheduling and loop alignment

| ID | Path | Quick description |
| --- | --- | --- |
| `techniques-helium-instruction-interleaving` | [wiki/techniques/techniques-helium-instruction-interleaving.md](techniques/techniques-helium-instruction-interleaving.md) | Interleave different Helium instruction types while preserving dependencies to expose execution overlap. |
| `techniques-helium-low-overhead-loop-alignment` | [wiki/techniques/techniques-helium-low-overhead-loop-alignment.md](techniques/techniques-helium-low-overhead-loop-alignment.md) | Align actual low-overhead-loop targets to four-byte boundaries and verify padding in the final assembly. |

