---
id: techniques-helium-fir-tap-blocking
title: Block FIR taps and preload coefficients for Helium load/MAC overlap
type: techniques
architectures:
  - armv8.1-m
  - cortex-m55
tags:
  - helium
  - mve
  - instruction-scheduling
  - fir-tap-blocking
  - c
  - asm
confidence: source-reported
reproducibility: concept
related:
  - techniques-helium-instruction-interleaving
  - patterns-cmsis-dsp-helium-migration
  - languages-c-float16-half-precision
sources:
  - https://github.com/ARM-software/CMSIS-DSP/blob/v1.18.0/Source/FilteringFunctions/arm_fir_f32.c
  - https://github.com/ARM-software/CMSIS-DSP/blob/v1.18.0/Source/FilteringFunctions/arm_fir_q15.c
  - https://github.com/ARM-software/CMSIS-DSP/blob/v1.18.0/Source/FilteringFunctions/arm_fir_q31.c
aliases:
  - Helium FIR tap blocking
  - MVE FIR coefficient preload
  - FIR load MAC overlap
  - FIR scratch partial outputs
evidence_basis: "CMSIS-DSP v1.18.0 source links corroborate FIR lane mappings, tap grouping, accumulation, and state handling."
---

Use this page when experimenting with tap grouping and load/compute scheduling in a Helium FIR. The CMSIS-DSP v1.18.0 sources provide public implementation examples for [F32 FIR](https://github.com/ARM-software/CMSIS-DSP/blob/v1.18.0/Source/FilteringFunctions/arm_fir_f32.c), [Q15 FIR](https://github.com/ARM-software/CMSIS-DSP/blob/v1.18.0/Source/FilteringFunctions/arm_fir_q15.c), and [Q31 FIR](https://github.com/ARM-software/CMSIS-DSP/blob/v1.18.0/Source/FilteringFunctions/arm_fir_q31.c). These release-pinned sources support the implementation facts below.

## Map lanes to samples and coefficients

The F32 MVE implementation forms vector outputs from successive sample windows and uses scalar tap values in its short-tap kernels; its loop organization varies with tap count. The Q15 implementation loads groups of eight coefficients and applies vector dot-product accumulations to overlapping sample windows for several outputs. Q31 paths use groups of four coefficients and vector multiply-accumulate/reduction operations. These public release examples show why coefficient placement and sample-load scheduling depend on data type and tap count; they do not prescribe a single register allocation for every hand-written kernel. See the linked F32, Q15, and Q31 source files for their state handling, accumulation, and output conversion.

As an implementation pattern, a four-output F32 schedule can retain a small group of scalar taps in general-purpose registers while loading overlapping sample windows and accumulating vector results. A fixed-point schedule can instead load coefficient vectors and use dot-product/reduction operations. Capacity arithmetic for seven resident tap vectors after reserving one vector for samples is up to 28 Q31, 56 Q15, or 112 8-bit values by lane count; this is a register-capacity estimate, not a CMSIS allocation rule. The public Q15 implementation uses 64-bit accumulators and applies a datatype-specific conversion and saturation path; Q31 also uses wide accumulation with its own output conversion. For long filters, process taps in groups if the schedule cannot keep every coefficient vector resident, preserving the selected function's accumulation order and fixed-point behavior.

## Choose a long-filter tap loop

For filters longer than the resident coefficient group, compare two loop organizations:

- Process the whole input block with one tap group, store partial outputs in scratch, then make another block pass for the next tap group and accumulate into those partial outputs. This keeps each load/compute sequence long but adds scratch storage and its store, reload, and add traffic.
- Add an inner loop over successive tap groups. This avoids the full-block scratch-pass organization but shortens each sequence of loads and multiply-accumulates.

Choose using block size, tap count, scratch cost, accumulation order, and target-specific evaluation. Keep the intended numerical behavior when changing the loop structure.

## Source limitations

The release-pinned CMSIS-DSP sources establish implementation examples, not mandatory register assignments or guaranteed performance. Consult the selected release's function documentation for FIR state size, coefficient order, padding, and fixed-point scaling. See [CMSIS-DSP Helium migration](../patterns/patterns-cmsis-dsp-helium-migration.md) for release-specific initialization guidance.
