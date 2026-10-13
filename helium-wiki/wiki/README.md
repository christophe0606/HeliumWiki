# Helium optimization concept map

Use this map to find optimization guidance for Cortex-M52, Cortex-M55, and Cortex-M85 by concept. Each row identifies a wiki page and summarizes what it covers. Paths are relative to `helium-wiki/`; the links open the corresponding pages.

Check each page's processor, revision, implemented features, and toolchain conditions before applying its guidance. Shared pages contain separate core-specific sections; instruction timing and resource constraints apply to the core identified in each section.

## Compiler configuration and vectorization

| ID | Path | Quick description |
| --- | --- | --- |
| `techniques-arm-compiler-mve-target-configuration` | [wiki/techniques/techniques-arm-compiler-mve-target-configuration.md](techniques/techniques-arm-compiler-mve-target-configuration.md) | Match Cortex-M55/M85 Arm Compiler CPU flags and feature tests to implemented Helium and floating-point features. |
| `techniques-helium-auto-vectorization` | [wiki/techniques/techniques-helium-auto-vectorization.md](techniques/techniques-helium-auto-vectorization.md) | Use Arm Compiler diagnostics to identify loop obstacles and refactor C or C++ for Cortex-M55/M85 Helium vectorization. |

## Runtime feature setup and power control

| ID | Path | Quick description |
| --- | --- | --- |
| `techniques-armv81m-feature-initialization` | [wiki/techniques/techniques-armv81m-feature-initialization.md](techniques/techniques-armv81m-feature-initialization.md) | Enable Cortex-M55/M85 low-overhead branch and Helium access, including TrustZone permissions and M55 CP10-dependent shift timing. |
| `techniques-cortex-m55-epu-retention` | [wiki/techniques/techniques-cortex-m55-epu-retention.md](techniques/techniques-cortex-m55-epu-retention.md) | Balance EPU wake delays and power savings on Cortex-M55 r0px/r1p0 systems using automatic retention. |

## DSP library migration and numerical precision

| ID | Path | Quick description |
| --- | --- | --- |
| `patterns-cmsis-dsp-helium-migration` | [wiki/patterns/patterns-cmsis-dsp-helium-migration.md](patterns/patterns-cmsis-dsp-helium-migration.md) | Review Cortex-M55/M85 CMSIS-DSP Helium initializers, coefficient storage, padding, and processing-buffer alignment. |
| `languages-c-float16-half-precision` | [wiki/languages/languages-c-float16-half-precision.md](languages/languages-c-float16-half-precision.md) | Use `_Float16` arithmetic and Cortex-M55/M85 Helium half-precision data when numerical requirements and compiler support permit. |

## Memory placement and cache behavior

| ID | Path | Quick description |
| --- | --- | --- |
| `hardware-itcm-instruction-data-contention` | [wiki/hardware/hardware-itcm-instruction-data-contention.md](hardware/hardware-itcm-instruction-data-contention.md) | Avoid instruction/data contention in Cortex-M55/M85 ITCM and evaluate M85 DTCM placement for frequently accessed constants. |
| `hardware-dtcm-scatter-gather-banks` | [wiki/hardware/hardware-dtcm-scatter-gather-banks.md](hardware/hardware-dtcm-scatter-gather-banks.md) | Arrange Cortex-M55/M85 DTCM accesses across banks, distinguish M55 vector-load penalties, and account for M85 L1 banks and DMA conflicts. |
| `techniques-armv8m-cache-management` | [wiki/techniques/techniques-armv8m-cache-management.md](techniques/techniques-armv8m-cache-management.md) | Apply Cortex-M55/M85 Armv8-M cache enable and deactivation ordering and interpret revision-sensitive M55 cache events. |
| `techniques-cortex-m-cache-prefetch` | [wiki/techniques/techniques-cortex-m-cache-prefetch.md](techniques/techniques-cortex-m-cache-prefetch.md) | Evaluate Cortex-M52 prefetch inclusion and PFCR control and Cortex-M85 stream coverage, explicit-prefetch costs, and transient hints. |
| `techniques-cortex-m-memory-access-scheduling` | [wiki/techniques/techniques-cortex-m-memory-access-scheduling.md](techniques/techniques-cortex-m-memory-access-scheduling.md) | Schedule Cortex-M52/M55 scalar, FP, and MVE transfers by each core's encodings, alignment, resources, memory waits, and overlap rules. |
| `techniques-cortex-m85-memory-access-scheduling` | [wiki/techniques/techniques-cortex-m85-memory-access-scheduling.md](techniques/techniques-cortex-m85-memory-access-scheduling.md) | Schedule Cortex-M85 scalar, FP, and MVE memory accesses by encoding, dependencies, store-data forwarding, alignment, and base updates. |

## Instruction selection, latency, and execution overlap

| ID | Path | Quick description |
| --- | --- | --- |
| `techniques-cortex-m-latency-aware-scheduling` | [wiki/techniques/techniques-cortex-m-latency-aware-scheduling.md](techniques/techniques-cortex-m-latency-aware-scheduling.md) | Schedule Cortex-M52/M55 scalar instructions using each core's dependency latency, encodings, shifted operands, SP effects, and divide costs. |
| `techniques-cortex-m85-latency-aware-scheduling` | [wiki/techniques/techniques-cortex-m85-latency-aware-scheduling.md](techniques/techniques-cortex-m85-latency-aware-scheduling.md) | Schedule Cortex-M85 scalar instructions by operand latency, issue-slot resources, encoding, divide costs, and producer/consumer classes. |
| `techniques-cortex-m-thumb-dual-issue` | [wiki/techniques/techniques-cortex-m-thumb-dual-issue.md](techniques/techniques-cortex-m-thumb-dual-issue.md) | Select eligible Cortex-M52/M55 16-bit Thumb encodings using each core's issue slots, operands, dependencies, and pairing restrictions. |
| `techniques-cortex-m-floating-point-scheduling` | [wiki/techniques/techniques-cortex-m-floating-point-scheduling.md](techniques/techniques-cortex-m-floating-point-scheduling.md) | Schedule Cortex-M52/M55 scalar and MVE FP using each core's precision, dependencies, forwarding, reductions, and fused-operation semantics. |
| `techniques-cortex-m85-floating-point-scheduling` | [wiki/techniques/techniques-cortex-m85-floating-point-scheduling.md](techniques/techniques-cortex-m85-floating-point-scheduling.md) | Schedule Cortex-M85 scalar and MVE FP by precision, operand dependencies, shared EPU resources, and fused-operation semantics. |
| `techniques-helium-instruction-interleaving` | [wiki/techniques/techniques-helium-instruction-interleaving.md](techniques/techniques-helium-instruction-interleaving.md) | Interleave Helium work using Cortex-M52 beatwise overlap, Cortex-M55 pipeline hazards, and Cortex-M85 issue groups and sequence rules. |

## Branch prediction and loop control

| ID | Path | Quick description |
| --- | --- | --- |
| `techniques-cortex-m-branch-prediction` | [wiki/techniques/techniques-cortex-m-branch-prediction.md](techniques/techniques-cortex-m-branch-prediction.md) | Use Cortex-M52 branch/loop timing and Cortex-M55/M85 prediction controls, timing, and core-specific overlap constraints. |
| `techniques-helium-low-overhead-loop-alignment` | [wiki/techniques/techniques-helium-low-overhead-loop-alignment.md](techniques/techniques-helium-low-overhead-loop-alignment.md) | Align Cortex-M55/M85 Helium low-overhead-loop targets to four-byte boundaries and verify padding in the final assembly. |

