---
id: techniques-helium-fft-butterflies
title: Map CFFT and RFFT butterflies to Helium complex operations
type: techniques
architectures:
  - armv8.1-m
  - cortex-m55
tags:
  - helium
  - mve
  - floating-point
  - fft-butterfly-vectorization
  - instruction-scheduling
  - c
  - asm
confidence: source-reported
reproducibility: concept
related:
  - techniques-helium-instruction-interleaving
  - hardware-dtcm-scatter-gather-banks
  - languages-c-float16-half-precision
  - techniques-profile-guided-helium-optimization
sources:
  - https://github.com/ARM-software/CMSIS-DSP/blob/v1.18.0/Source/TransformFunctions/arm_cfft_f32.c
  - https://github.com/ARM-software/CMSIS-DSP/blob/v1.18.0/Source/TransformFunctions/arm_cfft_f16.c
  - https://github.com/ARM-software/CMSIS-DSP/blob/v1.18.0/Source/TransformFunctions/arm_rfft_fast_f32.c
  - https://github.com/ARM-software/CMSIS-DSP/blob/v1.18.0/Source/TransformFunctions/arm_bitreversal.c
  - https://github.com/ARM-software/CMSIS-DSP/blob/v1.18.0/PrivateInclude/arm_vec_fft.h
  - https://github.com/Arm-Examples/Helium-Optimization/blob/bc9dfb67be64a2a5ee8e5325910a3f060a593863/Performance_analysis/ml-dsp-front-end-optimization-with-helium.md#L1372-L1480
aliases:
  - Helium FFT butterflies
  - MVE complex butterfly vectorization
  - CFFT radix 2 radix 4 MVE
  - RFFT recombination Helium
  - M55 FFT software pipelining workflow
evidence_basis: "CMSIS-DSP v1.18.0 source links corroborate FFT butterfly layouts, complex operations, and permutation details."
---

Use these layouts when implementing MVE complex FFT kernels or the CFFT portion of a real FFT. In CMSIS-DSP v1.18.0, the [F32 CFFT](https://github.com/ARM-software/CMSIS-DSP/blob/v1.18.0/Source/TransformFunctions/arm_cfft_f32.c) and [F16 CFFT](https://github.com/ARM-software/CMSIS-DSP/blob/v1.18.0/Source/TransformFunctions/arm_cfft_f16.c) sources implement radix butterfly paths, while the private FFT helper header defines complex-operation macros and MVE bit-reversal helpers. These links describe release-specific implementation details.

## Radix-2 complex pairs

An interleaved complex vector stores real and imaginary components in adjacent lanes. A float32x4_t vector can therefore carry two complex values, and a float16x8_t vector can carry four. For a twiddled radix-2 branch, form the sum and difference vectors, load twiddle values in the layout required by the loop, then apply the complex product to the difference branch. Verify lane order and gather offsets against the selected data layout and intrinsic definitions.

The CMSIS-DSP v1.18.0 private [arm_vec_fft.h complex macros](https://github.com/ARM-software/CMSIS-DSP/blob/v1.18.0/PrivateInclude/arm_vec_fft.h) define the three floating-point operations used here:

~~~c
#define MVE_CMPLX_ADD_A_ixB(A, B)           vcaddq_rot90(A,B)
#define MVE_CMPLX_SUB_A_ixB(A,B)            vcaddq_rot270(A,B)
#define MVE_CMPLX_MULT_FLT_Conj_AxB(A,B)    vcmlaq_rot270(vcmulq(A, B), A, B)
~~~

The header also contains a non-conjugated complex-multiply macro. These are private implementation macros guarded for the library's MVE build, not public callable APIs. The released CFFT files show their use in concrete kernels; consult the exact release and compiler intrinsic interface before copying a kernel schedule.

## Radix-4 main loop and final stage

For radix 4, form vector sums and differences for input pairs A/C and B/D. The first output combines the two sums without a twiddle; the other branches combine differences, apply the required plus or minus i rotation, and multiply by their twiddle vectors. The public F32 and F16 CFFT sources implement radix butterfly stages using vector inputs and twiddle data. Preserve the branch and rotation order when adapting their layout.

In the final vector stage, the public [F32 CFFT](https://github.com/ARM-software/CMSIS-DSP/blob/v1.18.0/Source/TransformFunctions/arm_cfft_f32.c) and [F16 CFFT](https://github.com/ARM-software/CMSIS-DSP/blob/v1.18.0/Source/TransformFunctions/arm_cfft_f16.c) implementations gather irregular lane positions, form butterfly sums and differences without loading twiddle vectors, then scatter the results. Treat this organization as specific to these released kernels; verify the selected transform, data layout, and direction before adapting it.

The public [MVE bit-reversal helpers](https://github.com/ARM-software/CMSIS-DSP/blob/v1.18.0/PrivateInclude/arm_vec_fft.h) implement in-place permutation using a bit-reversal table with vector gather and scatter operations. Their helper names are internal implementation details; do not treat them as public APIs. The [CFFT entry points](https://github.com/ARM-software/CMSIS-DSP/blob/v1.18.0/Source/TransformFunctions/arm_cfft_f32.c) select bit reversal according to the function's bitReverseFlag, so follow that release's documented flag and transform contract.

An out-of-place bit-reversal design can gather values in permutation order into a separate destination buffer, while an in-place design uses a permutation table and swaps/scatters within the working buffer. The out-of-place approach needs additional destination storage; the in-place approach avoids that second buffer but has different access and permutation costs. CMSIS-DSP v1.18.0 provides the in-place MVE helper as a public-source example; this comparison describes a general storage trade-off, not a second CMSIS API or a universal speed ranking.

## RFFT recombination

The public [CMSIS-DSP v1.18.0 fast F32 RFFT](https://github.com/ARM-software/CMSIS-DSP/blob/v1.18.0/Source/TransformFunctions/arm_rfft_fast_f32.c) performs a CFFT and then extracts the real spectrum by traversing one complex half forward and the other backward, conjugating as needed, and combining the pair with real-FFT twiddle factors. This is the implementation basis for the lane-layout pattern; endpoint packing, scaling, and direction handling are part of the function's full implementation and must be preserved when adapting it.

## Consider software pipelining only for a profiled hot loop

For a profiled Cortex-M55 FFT inner loop, inspect adjacent operations that compete for the same execution resources or depend on each other's results. Software pipelining may overlap independent work from neighboring iterations, but requires a valid prologue and epilogue, correct loop bounds and tail handling, and enough registers to hold staged values without spills.

Use static scheduling analysis to form a hypothesis, then inspect the generated instructions and verify the complete kernel on the intended processor. Do not treat the source's assembly alternatives or simulator analysis as a guaranteed improvement. When substituting a CMSIS-DSP FFT function, preserve the selected API's data representation, ordering, scaling, direction, and boundary behavior.
