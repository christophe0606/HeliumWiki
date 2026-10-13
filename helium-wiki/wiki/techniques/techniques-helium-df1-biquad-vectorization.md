---
id: techniques-helium-df1-biquad-vectorization
title: Vectorize DF1 biquad recurrences with Helium coefficient layouts
type: techniques
architectures:
  - armv8.1-m
  - cortex-m55
tags:
  - helium
  - mve
  - floating-point
  - biquad-recurrence-vectorization
  - instruction-scheduling
  - c
  - asm
confidence: source-reported
reproducibility: concept
related:
  - patterns-cmsis-dsp-helium-migration
  - techniques-helium-instruction-interleaving
  - languages-c-float16-half-precision
sources:
  - https://github.com/ARM-software/CMSIS-DSP/blob/v1.18.0/Source/FilteringFunctions/arm_biquad_cascade_df1_init_f32.c
  - https://github.com/ARM-software/CMSIS-DSP/blob/v1.18.0/Source/FilteringFunctions/arm_biquad_cascade_df1_init_f16.c
  - https://github.com/ARM-software/CMSIS-DSP/blob/v1.18.0/Source/FilteringFunctions/arm_biquad_cascade_df1_f32.c
  - https://github.com/ARM-software/CMSIS-DSP/blob/v1.18.0/Source/FilteringFunctions/arm_biquad_cascade_df1_f16.c
  - https://github.com/ARM-software/CMSIS-DSP/blob/v1.18.0/Source/FilteringFunctions/arm_biquad_cascade_df1_q31.c
aliases:
  - Helium DF1 biquad vectorization
  - MVE recursive biquad coefficient layout
  - DF1 recurrence SIMD expansion
evidence_basis: "CMSIS-DSP v1.18.0 source links corroborate recurrence expansion, coefficient layouts, and processing details."
---

Use this when a direct-form-I biquad's recursive dependencies limit SIMD work across samples. The CMSIS-DSP v1.18.0 public [F32 initializer](https://github.com/ARM-software/CMSIS-DSP/blob/v1.18.0/Source/FilteringFunctions/arm_biquad_cascade_df1_init_f32.c) and [F16 initializer](https://github.com/ARM-software/CMSIS-DSP/blob/v1.18.0/Source/FilteringFunctions/arm_biquad_cascade_df1_init_f16.c) expand recurrence coefficients for MVE processing; the matching [F32 kernel](https://github.com/ARM-software/CMSIS-DSP/blob/v1.18.0/Source/FilteringFunctions/arm_biquad_cascade_df1_f32.c) and [F16 kernel](https://github.com/ARM-software/CMSIS-DSP/blob/v1.18.0/Source/FilteringFunctions/arm_biquad_cascade_df1_f16.c) consume those layouts. The released initialization code is the source-backed basis for the layout described here.

The DF1 recurrence is y[i] = a1*y[i-1] + a2*y[i-2] + b0*x[i] + b1*x[i-1] + b2*x[i-2]. Substituting earlier outputs into later equations exposes multiply-accumulate work while preserving the recurrence's dependency chain. For four F32 outputs, the expanded terms span six input positions, x[i-2] through x[i+3], plus the two initial output-history values y[i-2] and y[i-1]. The F32 initializer builds a 4 by 8 coefficient array, advances it through four recurrence rows, and transposes it into the modified-coefficient structure. For eight F16 outputs, the span is ten input positions, x[i-2] through x[i+7], plus the same two initial output states; the F16 initializer builds an 8 by 12 array and advances it through eight recurrence rows before transposing it. These dimensions and recurrence updates are visible in the public [F32 initializer](https://github.com/ARM-software/CMSIS-DSP/blob/v1.18.0/Source/FilteringFunctions/arm_biquad_cascade_df1_init_f32.c) and [F16 initializer](https://github.com/ARM-software/CMSIS-DSP/blob/v1.18.0/Source/FilteringFunctions/arm_biquad_cascade_df1_init_f16.c).

The processing kernels handle four F32 outputs or eight F16 outputs per vector group and carry two prior input and two prior output values into the next group. They load expanded coefficient vectors from the modified-coefficient array during the group, interleaving those loads with the vector multiply/FMA sequence; keeping fewer coefficient vectors live can reduce register pressure at the cost of coefficient-load traffic. The static coefficient generators are implementation helpers, not public callable APIs; use the public MVE initializer for the selected release.

Reassociation and fused multiply-accumulate operations can produce different rounding from a scalar operation order. Compare output error against the application's tolerance, particularly across cascaded stages and long blocks. Treat the modified coefficient layout as release-specific rather than as a general buffer format.

## Q31 feedback and scaling

The public [CMSIS-DSP v1.18.0 Q31 DF1 source](https://github.com/ARM-software/CMSIS-DSP/blob/v1.18.0/Source/FilteringFunctions/arm_biquad_cascade_df1_q31.c) uses an `int64_t` accumulator with vector dot-product and feedback accumulation, applies the configured shift, then extracts the high 32-bit result. It computes dependent outputs in sequence: after the first result, it places that value in the feedback state before calculating the next output, then carries both outputs into the following pair. Its staged coefficient vectors are `{b2,b1,b0,0}` and `{0,b2,b1,b0}` for input terms, and `{0,0,a2,a1}` and `{0,0,a1,a2}` for feedback terms. The MVE loop is unrolled to process four outputs, with results written in pairs. Preserve the selected release's Q31 scaling, accumulator, and feedback semantics; do not infer rounding or saturation behavior from another datatype.

## Public coefficient expansion details

The public F32 and F16 initializer sources contain the recurrence expansion and transpose directly: the F32 temporary coefficient array is [4][8], while the F16 temporary is [8][12]. Their generated vectors represent substituted recurrence terms for consecutive outputs and include feedback contributions. Re-derive any executable layout from the exact scalar recurrence and the selected release's initialization code; do not rely on independently transcribed coefficient rows or assume the private layout is stable across versions.

For current CMSIS-DSP initialization and modified-coefficient storage, see [CMSIS-DSP Helium migration](../patterns/patterns-cmsis-dsp-helium-migration.md).
