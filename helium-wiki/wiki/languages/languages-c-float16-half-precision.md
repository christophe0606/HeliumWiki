---
id: languages-c-float16-half-precision
title: Use _Float16 for half-precision arithmetic and Helium vector data
type: languages
architectures:
  - armv8.1-m
  - cortex-m55
  - cortex-m85
tags:
  - half-precision
  - floating-point
  - helium
  - mve
  - c
  - cpp
confidence: source-reported
reproducibility: snippet
related:
  - techniques-arm-compiler-mve-target-configuration
  - techniques-helium-auto-vectorization
  - patterns-cmsis-dsp-helium-migration
  - techniques-cortex-m55-epu-retention
sources:
  - https://developer.arm.com/community/arm-community-blogs/b/architectures-and-processors-blog/posts/armv8_2d00_m-based-processor-software-development-hints-and-tips
aliases:
  - half precision floating point
  - IEEE binary16
  - _Float16 arithmetic
  - fp16 Helium
  - C half precision
---

Use IEEE binary16 (`_Float16`) for floating-point data or arithmetic on Armv8.1-M when its reduced precision and dynamic range fit the application. It halves storage per value versus single precision and allows twice as many Helium lane operations per vector, but that lane count does not guarantee a twofold application speedup; conversion, memory behavior, vectorization, and the workload still matter.

The article describes scalar half-precision arithmetic on M55/M85 when an FPU is implemented, and Helium half-precision vector operations when the floating-point vector feature is present. `_Float16` is an arithmetic type. ACLE `__fp16` is intended for storage and conversion, with arithmetic promoted to a wider type, so use `_Float16` when half-precision arithmetic is intended.

The source associates `_Float16` with the C11 extension ISO/IEC TS 18661-3:2015 and recommends selecting C11 for C projects with the `-std=c11` compiler option. It reports that Arm Compiler 6, LLVM, and GCC of the time also accepted the type in other language modes; compiler and C++ support remain toolchain-version dependent. Where supported, an `f16` suffix and explicit cast express binary16 constants and conversions:

```c
_Float16 x = 0.5f16;
_Float16 y = (_Float16)0.25;
_Float16 z = x * y;
printf("%f\n", (double)z);
```

The `printf` conversion promotes the value to `double` for `%f`. Do not confuse IEEE binary16 with bfloat16 (`__bf16`), which is a different 16-bit format; the article states that Armv8.1-M does not support bfloat16.
