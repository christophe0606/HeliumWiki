---
id: patterns-helium-small-kernel-fusion
title: Fuse small producer and consumer DSP kernels
type: patterns
architectures:
  - armv8.1-m
  - cortex-m52
  - cortex-m55
  - cortex-m85
tags:
  - helium
  - mve
  - auto-vectorization
  - instruction-scheduling
confidence: source-reported
reproducibility: concept
related:
  - patterns-cmsis-dsp-helium-migration
  - techniques-helium-auto-vectorization
  - techniques-helium-instruction-interleaving
  - techniques-helium-matrix-kernel-layout
  - techniques-helium-vector-reductions
  - techniques-helium-fixed-point-arithmetic
sources:
  - https://github.com/Arm-Examples/Helium-Optimization/blob/bc9dfb67be64a2a5ee8e5325910a3f060a593863/Performance_analysis/ml-dsp-front-end-optimization-with-helium.md#L849-L867
  - https://github.com/Arm-Examples/Helium-Optimization/blob/bc9dfb67be64a2a5ee8e5325910a3f060a593863/Performance_analysis/ml-dsp-front-end-optimization-with-helium.md#L1337-L1371
  - https://github.com/Arm-Examples/Helium-Optimization/blob/bc9dfb67be64a2a5ee8e5325910a3f060a593863/General_optimizations/optimizing_c_functions.md#L81-L98
  - https://github.com/arm-education/Arm-Helium-Technology/blob/main/HeliumTechnology_referencebook.pdf
  - https://github.com/ARM-software/CMSIS-DSP/tree/main/Source/MatrixFunctions
  - https://github.com/ARM-software/CMSIS-DSP/tree/main/Source/BasicMathFunctions
aliases:
  - Helium loop fusion
  - eliminate short DSP temporary buffers
  - inline short CMSIS-DSP call chains
  - fuse matrix-vector output scaling after row reduction
prerequisites:
  - Profile the complete application to confirm that the call chain is worth changing.
  - Define numerical, aliasing, and boundary-count behavior before combining operations.
---

Use this pattern for profiled short DSP pipelines where call, stack, loop setup, or intermediate-buffer traffic is significant relative to useful work. Keep the public CMSIS-DSP sequence as a reference and validate any fused replacement against the application's numerical and buffer contracts.

## Find a suitable producer and consumer

First inspect whether successive library calls store an intermediate that the next operation immediately reloads, or whether several operations reuse the same input values. Link-time optimization or inlining may expose opportunities without changing the algorithm. If that is not sufficient, a fused kernel can retain loaded values in registers and perform several operations before storing final outputs.

The source case study gives complex conjugation followed by a complex dot product as an example of a short call chain with an immediately consumed temporary. Treat it only as a pattern: preserve real/imaginary ordering and conjugation sign, reduction precision and evaluation order, aliasing behavior, fixed-point scaling/saturation/rounding, and correct sample and tail counts. Do not copy the case-study loop mechanically.

## Check the cost of fusion

Fusion can remove intermediate stores, reloads, and repeated setup, but it can also raise register pressure, cause spills, increase code size, or change floating-point association. Compare the generated code and profile the complete application after the change. Keep the simpler library path when the fused implementation does not improve the actual workload or makes its contract harder to maintain. The source describes a CMSIS-DSP C++ fusion facility as experimental at the time of writing; check the selected public release before depending on that facility.

Loop partitioning is the opposite option: separating several tasks may expose simpler vectorizable loops, but it can add traversals and intermediate traffic. Fusion can remove that traffic while keeping more values live and increasing spill risk. Compare both layouts using the actual working set, generated code, and complete workload; neither splitting nor fusion is a universal winner. See [Helium loop vectorization](../techniques/techniques-helium-auto-vectorization.md) for iteration-count, dependency, and compiler-diagnostic checks. [Arm Helium Technology: M-Profile Vector Extension (MVE) for Cortex-M Processors, Reference Book, PDF p. 137]

## Finalize a matrix output after its row sum

When a completed matrix-vector row immediately feeds independent output bias or scaling, keep that row's scalar accumulator live, apply the required final operation once after all columns have contributed, and store the final output. This can avoid an intermediate result store and reload. Do not apply rounding, scaling, or saturation to each partial dot product unless that is the specified arithmetic; it changes the result.

Preserve the complete output contract: raw signed 32-bit sum or quantized output, bias width and order, multiplier and shift, rounding mode, saturation, and output signedness. Add final bias or scaling only when the caller requires it. Bound the accumulator including any fused bias, and account for live per-row metadata, aliasing, tails, and register pressure when checking generated code. See [Helium matrix kernel layout](../techniques/techniques-helium-matrix-kernel-layout.md), [Helium vector reductions](../techniques/techniques-helium-vector-reductions.md), and [Helium fixed-point arithmetic](../techniques/techniques-helium-fixed-point-arithmetic.md).

Check the selected public [CMSIS-DSP matrix](https://github.com/ARM-software/CMSIS-DSP/tree/main/Source/MatrixFunctions) or [basic math](https://github.com/ARM-software/CMSIS-DSP/tree/main/Source/BasicMathFunctions) routine for its full contract before treating it as a reference. A quantized NN kernel may include bias and requantization that a raw matrix-vector result does not; such a routine is not interchangeable solely because its inner products look similar.
