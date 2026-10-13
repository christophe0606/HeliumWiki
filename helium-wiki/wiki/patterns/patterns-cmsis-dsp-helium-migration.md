---
id: patterns-cmsis-dsp-helium-migration
title: Migrate CMSIS-DSP applications to Helium library paths and aligned buffers
type: patterns
architectures:
  - cortex-m55
  - cortex-m85
tags:
  - cmsis-dsp-migration
  - buffer-alignment
  - helium
  - mve
  - c
  - cpp
confidence: source-reported
reproducibility: concept
related:
  - techniques-arm-compiler-mve-target-configuration
  - techniques-helium-auto-vectorization
  - hardware-itcm-instruction-data-contention
  - hardware-dtcm-scatter-gather-banks
  - languages-c-float16-half-precision
  - techniques-helium-fir-tap-blocking
  - techniques-helium-df1-biquad-vectorization
sources:
  - https://developer.arm.com/community/arm-community-blogs/b/architectures-and-processors-blog/posts/armv8_2d00_m-based-processor-software-development-hints-and-tips
  - https://github.com/ARM-software/CMSIS-DSP/blob/v1.18.0/Source/FilteringFunctions/arm_fir_f32.c
  - https://github.com/ARM-software/CMSIS-DSP/blob/v1.18.0/Source/FilteringFunctions/arm_fir_q15.c
  - https://github.com/ARM-software/CMSIS-DSP/blob/v1.18.0/Source/FilteringFunctions/arm_fir_q31.c
  - https://github.com/ARM-software/CMSIS-DSP/blob/v1.18.0/Source/FilteringFunctions/arm_biquad_cascade_df1_init_f32.c
  - https://github.com/ARM-software/CMSIS-DSP/blob/v1.18.0/Source/FilteringFunctions/arm_biquad_cascade_df1_init_f16.c
aliases:
  - CMSIS-DSP MVE porting
  - CMSIS-DSP Cortex-M55 migration
  - CMSIS-DSP aligned buffers
  - Helium biquad initialization
prerequisites:
  - Build the CMSIS-DSP source for the processor's actual feature configuration.
  - Check the documentation for the specific CMSIS-DSP release and function before changing buffer sizes or padding.
---

When moving a CMSIS-DSP application to Cortex-M55 or Cortex-M85 with Helium, most application calls may remain usable, but some MVE-specific initialization, coefficient storage, and buffer alignment details need review. The article describes CMSIS-DSP releases as source-only because processor configurability makes shipping every binary variant impractical.

For the Arm Compiler 6 library build, the article recommends `-Ofast` for performance. This is an article-specific recommendation, and `-Ofast` can change floating-point semantics; confirm that those changes meet the application's numerical requirements.

For the MVE biquad DF1 path, replace the non-Helium initializer with the MVE-specific initializer and provide its modified-coefficient buffer:

| Non-Helium initializer | MVE initializer | Additional storage |
| --- | --- | --- |
| `arm_biquad_cascade_df1_init_f32` | `arm_biquad_cascade_df1_mve_init_f32` | `pCoeffsMod`, sized to `32*numStages` `float32_t` elements |

Some Helium FIR functions may require padding the coefficient array. The article does not give a universal padding formula: use the requirements for the exact function and CMSIS-DSP release in its matching documentation. Review older applications for calls on the deprecated-function list and update affected calls as appropriate.

For filter-processing buffers, the article recommends at least 64-bit (8-byte) alignment and says 128-bit (16-byte) alignment is better. Treat this as alignment guidance, and preserve any separate storage and size requirements of the selected function.

## Coefficient layout in the public MVE implementations

The release-pinned [CMSIS-DSP F32 FIR implementation](https://github.com/ARM-software/CMSIS-DSP/blob/v1.18.0/Source/FilteringFunctions/arm_fir_f32.c), [Q15 FIR implementation](https://github.com/ARM-software/CMSIS-DSP/blob/v1.18.0/Source/FilteringFunctions/arm_fir_q15.c), and [Q31 FIR implementation](https://github.com/ARM-software/CMSIS-DSP/blob/v1.18.0/Source/FilteringFunctions/arm_fir_q31.c) show their own state and coefficient handling. Do not infer a current function's allocation contract from a generic FIR schematic: use the selected release's function documentation for state length, padding, coefficient order, and scratch requirements.

For MVE DF1, the public [F32 initializer](https://github.com/ARM-software/CMSIS-DSP/blob/v1.18.0/Source/FilteringFunctions/arm_biquad_cascade_df1_init_f32.c) uses a static internal helper to expand a 4 by 8 recurrence coefficient array and transpose it into the modified-coefficient structure. The public [F16 initializer](https://github.com/ARM-software/CMSIS-DSP/blob/v1.18.0/Source/FilteringFunctions/arm_biquad_cascade_df1_init_f16.c) similarly expands an 8 by 12 array and transposes it. The helpers named `generateCoefsFastBiquadF32` and `generateCoefsFastBiquadF16` are static functions inside those implementation files, not public callable APIs. The F32 and F16 MVE initializer functions are public entry points in the release sources; use the matching declarations and structure types for that release. The modified layout is an implementation detail, so do not infer a universal F16 allocation size from the temporary array dimensions.

See [Helium DF1 biquad vectorization](../techniques/techniques-helium-df1-biquad-vectorization.md) for the public coefficient-expansion references and numerical validation guidance. For FIR tap scheduling and the scratch-pass tradeoff, see [Helium FIR tap blocking](../techniques/techniques-helium-fir-tap-blocking.md).
