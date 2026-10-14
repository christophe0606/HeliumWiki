# Helium optimization concept map

Use this map to find optimization guidance for Cortex-M52, Cortex-M55, and Cortex-M85 by concept. Each row identifies a wiki page and summarizes what it covers. Paths are relative to `helium-wiki/`; the links open the corresponding pages.

Check each page's processor, revision, implemented features, and toolchain conditions before applying its guidance. Shared pages contain separate core-specific sections; instruction timing and resource constraints apply to the core identified in each section.

## Profiling and execution trace

| ID | Path | Quick description |
| --- | --- | --- |
| `techniques-profile-guided-helium-optimization` | [wiki/techniques/techniques-profile-guided-helium-optimization.md](techniques/techniques-profile-guided-helium-optimization.md) | Prioritize application hotspots, isolate hot loops, verify PMU event and counter conditions, and profile again after structural changes. |
| `techniques-helium-trace-analysis` | [wiki/techniques/techniques-helium-trace-analysis.md](techniques/techniques-helium-trace-analysis.md) | Capture bounded Cortex-M traces, match executable symbols, align comparable events, and interpret timestamp and sleep limitations. |

## Compiler configuration and MVE programming contracts

| ID | Path | Quick description |
| --- | --- | --- |
| `techniques-arm-compiler-mve-target-configuration` | [wiki/techniques/techniques-arm-compiler-mve-target-configuration.md](techniques/techniques-arm-compiler-mve-target-configuration.md) | Match Cortex-M52/M55/M85 Arm Compiler target flags and `__ARM_FEATURE_MVE` bitmap tests to implemented integer MVE, vector floating-point, and scalar floating-point features. |
| `techniques-helium-auto-vectorization` | [wiki/techniques/techniques-helium-auto-vectorization.md](techniques/techniques-helium-auto-vectorization.md) | Distinguish SLP, loop vectorization, and loop interleaving; use compiler diagnostics, loop layout, operand reuse, and numerical contracts to guide C/C++ changes. |
| `languages-arm-mve-intrinsics-and-assembly` | [wiki/languages/languages-arm-mve-intrinsics-and-assembly.md](languages/languages-arm-mve-intrinsics-and-assembly.md) | Guard ACLE intrinsic headers and namespaces, inspect generated code, and declare assembly operands and clobbers while preserving register, ABI, and ECI exception-continuation contracts. |

## Runtime feature setup and power control

| ID | Path | Quick description |
| --- | --- | --- |
| `techniques-armv81m-feature-initialization` | [wiki/techniques/techniques-armv81m-feature-initialization.md](techniques/techniques-armv81m-feature-initialization.md) | Separate `MVFR1` and model MVE capability from Cortex-M55/M85 startup permissions, TrustZone access, low-overhead branch setup, and M55 CP10-dependent shift timing. |
| `techniques-cortex-m55-epu-retention` | [wiki/techniques/techniques-cortex-m55-epu-retention.md](techniques/techniques-cortex-m55-epu-retention.md) | Balance EPU wake delays and power savings on Cortex-M55 r0px/r1p0 systems using automatic retention. |

## DSP and neural-network library integration

| ID | Path | Quick description |
| --- | --- | --- |
| `patterns-cmsis-dsp-helium-migration` | [wiki/patterns/patterns-cmsis-dsp-helium-migration.md](patterns/patterns-cmsis-dsp-helium-migration.md) | Integrate `arm_math.h` and compatible CMSIS-DSP builds; preserve release-specific Helium paths, FIR/DF1 state, block counts, FFT semantics, and public API contracts. |
| `patterns-cmsis-nn-mve-runtime-selection` | [wiki/patterns/patterns-cmsis-nn-mve-runtime-selection.md](patterns/patterns-cmsis-nn-mve-runtime-selection.md) | Verify Cortex-M55 runtime kernel selection, release-specific operator and tensor contracts, quantization, and deployment memory needs. |

## Numerical precision, fixed-point arithmetic, and reductions

| ID | Path | Quick description |
| --- | --- | --- |
| `languages-c-float16-half-precision` | [wiki/languages/languages-c-float16-half-precision.md](languages/languages-c-float16-half-precision.md) | Choose `_Float16` for suitable numerical ranges and working-set sizes, with compiler support and DSP lane layouts in view. |
| `techniques-helium-fixed-point-arithmetic` | [wiki/techniques/techniques-helium-fixed-point-arithmetic.md](techniques/techniques-helium-fixed-point-arithmetic.md) | Match Q formats, intermediate widths, top/bottom lanes, conversions, rounding, saturation, and quantized-operator semantics. |
| `techniques-helium-vector-reductions` | [wiki/techniques/techniques-helium-vector-reductions.md](techniques/techniques-helium-vector-reductions.md) | Match integer, floating-point, and complex Q31 reductions to scalar accumulator and widening semantics, ranges, identities, scaling, component pairing, tail masks, extrema indices, and numeric order. |

## DSP and matrix kernel layout and fusion

| ID | Path | Quick description |
| --- | --- | --- |
| `techniques-helium-fir-tap-blocking` | [wiki/techniques/techniques-helium-fir-tap-blocking.md](techniques/techniques-helium-fir-tap-blocking.md) | Study Cortex-M55 FIR lane mappings, coefficient reuse, block-linear history, sample/tap tails, and convolution boundary contracts. |
| `techniques-helium-fft-butterflies` | [wiki/techniques/techniques-helium-fft-butterflies.md](techniques/techniques-helium-fft-butterflies.md) | Map complex FFT butterflies and permutations to Helium lanes while preserving signs, scaling, output layout, and peak-index association. |
| `techniques-helium-df1-biquad-vectorization` | [wiki/techniques/techniques-helium-df1-biquad-vectorization.md](techniques/techniques-helium-df1-biquad-vectorization.md) | Study Cortex-M55 DF1 recurrence expansion, floating-point coefficient layouts, Q31 feedback scheduling, and numerical checks. |
| `techniques-helium-matrix-kernel-layout` | [wiki/techniques/techniques-helium-matrix-kernel-layout.md](techniques/techniques-helium-matrix-kernel-layout.md) | Reuse inputs across output rows, amortize packing or partial im2col, and map bounded transpose blocks without overwriting unread inputs. |
| `patterns-helium-small-kernel-fusion` | [wiki/patterns/patterns-helium-small-kernel-fusion.md](patterns/patterns-helium-small-kernel-fusion.md) | Combine short producer/consumer kernels to reuse operands and remove intermediates while preserving numerical, aliasing, and tail contracts. |

## Multiword and carryless polynomial arithmetic

| ID | Path | Quick description |
| --- | --- | --- |
| `techniques-helium-multiword-carry-arithmetic` | [wiki/techniques/techniques-helium-multiword-carry-arithmetic.md](techniques/techniques-helium-multiword-carry-arithmetic.md) | Preserve limb order, FPSCR carry state, partial-vector arithmetic, and whole-vector carry shifts in multiword integer operations. |
| `techniques-helium-polynomial-multiplication` | [wiki/techniques/techniques-helium-polynomial-multiplication.md](techniques/techniques-helium-polynomial-multiplication.md) | Assemble raw carryless products with XOR, bounded gathers, lane predicates, and target-specific schedules within register and ABI limits. |

## Vector memory layout, alignment, and circular traversal

| ID | Path | Quick description |
| --- | --- | --- |
| `techniques-helium-memory-access-layout` | [wiki/techniques/techniques-helium-memory-access-layout.md](techniques/techniques-helium-memory-access-layout.md) | Keep typed-pointer elements and byte counts distinct when choosing contiguous, gather/scatter, widening, and complete interleaved transfers with bounded tails. |
| `techniques-helium-vector-data-alignment` | [wiki/techniques/techniques-helium-vector-data-alignment.md](techniques/techniques-helium-vector-data-alignment.md) | Separate vector alignment requirements from bus and cache-line performance choices, allocation bounds, padding, and tail handling. |
| `patterns-helium-circular-buffer-addressing` | [wiki/patterns/patterns-helium-circular-buffer-addressing.md](patterns/patterns-helium-circular-buffer-addressing.md) | Generate bounded wrapped offsets for ring-buffer gathers and compare per-sample circular updates with block-linear FIR state. |

## Memory placement and buffer lifetimes

| ID | Path | Quick description |
| --- | --- | --- |
| `hardware-itcm-instruction-data-contention` | [wiki/hardware/hardware-itcm-instruction-data-contention.md](hardware/hardware-itcm-instruction-data-contention.md) | Avoid instruction/data contention in Cortex-M55/M85 ITCM and evaluate M85 DTCM placement for frequently accessed constants. |
| `hardware-dtcm-scatter-gather-banks` | [wiki/hardware/hardware-dtcm-scatter-gather-banks.md](hardware/hardware-dtcm-scatter-gather-banks.md) | Arrange M55/M85 bank accesses, distinguish gather/load conflicts from M55 store-to-read hazards, and account for M85 L1/DMA contention. |
| `patterns-sequential-buffer-overlays` | [wiki/patterns/patterns-sequential-buffer-overlays.md](patterns/patterns-sequential-buffer-overlays.md) | Reuse DSP/NN workspace only across disjoint lifetimes, preserving unread inputs, recurrent state, and asynchronous consumers. |

## DMA pipelines, ownership, and cache visibility

| ID | Path | Quick description |
| --- | --- | --- |
| `patterns-helium-dtcm-dma-pipeline` | [wiki/patterns/patterns-helium-dtcm-dma-pipeline.md](patterns/patterns-helium-dtcm-dma-pipeline.md) | Prioritize critical TCM working sets and stage streaming data with explicit CPU/DMA ownership, reachability checks, and conditional overlap. |
| `techniques-cache-dma-buffer-visibility` | [wiki/techniques/techniques-cache-dma-buffer-visibility.md](techniques/techniques-cache-dma-buffer-visibility.md) | Choose cache policy and clean CPU-written output at DMA ownership boundaries with the required visibility, ordering, and synchronization. |

## Cache control, streaming, and prefetch

| ID | Path | Quick description |
| --- | --- | --- |
| `techniques-armv8m-cache-management` | [wiki/techniques/techniques-armv8m-cache-management.md](techniques/techniques-armv8m-cache-management.md) | Apply Cortex-M55/M85 Armv8-M cache enable and deactivation ordering and interpret revision-sensitive M55 cache events. |
| `techniques-cortex-m-data-prefetch-and-cache-hints` | [wiki/techniques/techniques-cortex-m-data-prefetch-and-cache-hints.md](techniques/techniques-cortex-m-data-prefetch-and-cache-hints.md) | Evaluate M52 prefetch inclusion, M55 linear-stream placement, and M85 stream coverage, explicit-prefetch costs, and transient hints. |

## Instruction selection, memory scheduling, and execution overlap

| ID | Path | Quick description |
| --- | --- | --- |
| `techniques-cortex-m-latency-aware-scheduling` | [wiki/techniques/techniques-cortex-m-latency-aware-scheduling.md](techniques/techniques-cortex-m-latency-aware-scheduling.md) | Schedule Cortex-M52/M55 scalar instructions using each core's dependency latency, encodings, shifted operands, SP effects, and divide costs. |
| `techniques-cortex-m85-latency-aware-scheduling` | [wiki/techniques/techniques-cortex-m85-latency-aware-scheduling.md](techniques/techniques-cortex-m85-latency-aware-scheduling.md) | Schedule Cortex-M85 scalar instructions by operand latency, issue-slot resources, encoding, divide costs, and producer/consumer classes. |
| `techniques-cortex-m-thumb-dual-issue` | [wiki/techniques/techniques-cortex-m-thumb-dual-issue.md](techniques/techniques-cortex-m-thumb-dual-issue.md) | Select eligible Cortex-M52/M55 16-bit Thumb encodings using each core's issue slots, operands, dependencies, and pairing restrictions. |
| `techniques-cortex-m-floating-point-scheduling` | [wiki/techniques/techniques-cortex-m-floating-point-scheduling.md](techniques/techniques-cortex-m-floating-point-scheduling.md) | Schedule Cortex-M52/M55 scalar and MVE FP using each core's precision, dependencies, forwarding, reductions, and fused-operation semantics. |
| `techniques-cortex-m85-floating-point-scheduling` | [wiki/techniques/techniques-cortex-m85-floating-point-scheduling.md](techniques/techniques-cortex-m85-floating-point-scheduling.md) | Schedule Cortex-M85 scalar and MVE FP by precision, operand dependencies, shared EPU resources, and fused-operation semantics. |
| `techniques-cortex-m-memory-access-scheduling` | [wiki/techniques/techniques-cortex-m-memory-access-scheduling.md](techniques/techniques-cortex-m-memory-access-scheduling.md) | Schedule Cortex-M52/M55 scalar, FP, and MVE transfers by encoding, alignment, overlap rules, and independent-buffer store-to-read placement. |
| `techniques-cortex-m85-memory-access-scheduling` | [wiki/techniques/techniques-cortex-m85-memory-access-scheduling.md](techniques/techniques-cortex-m85-memory-access-scheduling.md) | Schedule Cortex-M85 scalar, FP, and MVE memory accesses by encoding, dependencies, store-data forwarding, alignment, and base updates. |
| `techniques-helium-instruction-interleaving` | [wiki/techniques/techniques-helium-instruction-interleaving.md](techniques/techniques-helium-instruction-interleaving.md) | Interleave Helium work using conditional dependent load/MAC beatwise overlap, M52 overlap rules, M55 pipeline hazards and operand reuse, and M85 issue-group rules. |

## Branch prediction, loop control, and lane predicates

| ID | Path | Quick description |
| --- | --- | --- |
| `techniques-cortex-m-branch-prediction` | [wiki/techniques/techniques-cortex-m-branch-prediction.md](techniques/techniques-cortex-m-branch-prediction.md) | Use Cortex-M52 branch/loop timing and Cortex-M55/M85 prediction controls, timing, and core-specific overlap constraints. |
| `techniques-helium-low-overhead-loop-alignment` | [wiki/techniques/techniques-helium-low-overhead-loop-alignment.md](techniques/techniques-helium-low-overhead-loop-alignment.md) | Align Cortex-M55/M85 Helium low-overhead-loop targets to four-byte boundaries and verify padding in the final assembly. |
| `techniques-helium-predication-and-tail-handling` | [wiki/techniques/techniques-helium-predication-and-tail-handling.md](techniques/techniques-helium-predication-and-tail-handling.md) | Translate complex samples into scalar-component tail counts; match loop counts, predicate widths, inactive lanes, memory bounds, scalar effects, and early-exit tail-state cleanup. |
