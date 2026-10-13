---
id: techniques-arm-compiler-mve-target-configuration
title: Configure Arm Compiler targets for implemented Helium and floating-point features
type: techniques
architectures:
  - armv8.1-m
  - cortex-m55
  - cortex-m85
tags:
  - compiler-target-configuration
  - helium
  - mve
  - floating-point
  - c
  - cpp
confidence: source-reported
reproducibility: snippet
related:
  - techniques-helium-auto-vectorization
  - techniques-armv81m-feature-initialization
  - patterns-cmsis-dsp-helium-migration
  - languages-c-float16-half-precision
sources:
  - https://developer.arm.com/community/arm-community-blogs/b/architectures-and-processors-blog/posts/armv8_2d00_m-based-processor-software-development-hints-and-tips
aliases:
  - Arm Compiler MVE target flags
  - armclang Cortex-M55 feature selection
  - armclang Cortex-M85 feature selection
  - __ARM_FEATURE_MVE
prerequisites:
  - Know which Helium and floating-point features the target actually implements.
  - Keep compiler, linker, and disassembler CPU feature descriptions consistent.
---

Use these Arm Compiler 6 configuration examples when building for Cortex-M55 or Cortex-M85 with a particular combination of Helium (MVE) and floating-point features. Selecting features that the device does not implement can produce unsuitable code; architecture-only selection is also reported to miss processor-specific optimization.

The article recommends Arm Compiler 6.15 or later and says 6.14 supports Armv8.1-M but was less optimized. This is a historical recommendation from the article, not a current minimum-version statement. With `-mcpu`, the article says Cortex-M55/M85 default selections assume both Helium and FPU. Use the row matching the actual implementation:

| Processor | Configuration | `armclang -mcpu` | `armlink` / `fromelf --cpu` |
| --- | --- | --- | --- |
| Cortex-M55 | No Helium, no FPU | `-mcpu=cortex-m55+nomve+nofp` | `--cpu Cortex-M55.no_mve.no_fp` |
| Cortex-M55 | No Helium, with FPU | `-mcpu=cortex-m55+nomve` | `--cpu Cortex-M55.no_mve` |
| Cortex-M55 | Integer Helium, no FPU | `-mcpu=cortex-m55+nofp` | `--cpu Cortex-M55.no_fp` |
| Cortex-M55 | Integer Helium, scalar FPU | `-mcpu=cortex-m55+nomve.fp` | `--cpu Cortex-M55.no_mvefp` |
| Cortex-M55 | Full feature set | `-mcpu=cortex-m55` | `--cpu Cortex-M55` |
| Cortex-M85 | No Helium, no FPU | `-mcpu=cortex-m85+nomve+nofp` | `--cpu Cortex-M85.no_mve.no_fp` |
| Cortex-M85 | No Helium, with FPU | `-mcpu=cortex-m85+nomve` | `--cpu Cortex-M85.no_mve` |
| Cortex-M85 | Integer Helium, no FPU | `-mcpu=cortex-m85+nofp` | `--cpu Cortex-M85.no_fp` |
| Cortex-M85 | Full feature set | `-mcpu=cortex-m85` | `--cpu Cortex-M85` |

The article provides these architecture-level alternatives. They apply to Cortex-M55/M85, but using `-march` does not provide processor-specific optimizations:

| Configuration | `armclang -march` | `armlink` / `fromelf --cpu` |
| --- | --- | --- |
| No Helium, no FPU | `-march=armv8.1-m.main+dsp` | `--cpu 8.1-M.Main.no_mve.no_fp` |
| No Helium, with FPU | `-march=armv8.1-m.main+dsp+fp.dp` | `--cpu 8.1-M.Main.no_mve` |
| Integer Helium, no FPU | `-march=armv8.1-m.main+mve` | `--cpu 8.1-M.Main.no_fp` |
| Integer Helium, scalar FPU | `-march=armv8.1-m.main+mve+fp.dp` | `--cpu 8.1-M.Main.no_mvefp` |
| Full feature set | `-march=armv8.1-m.main+mve.fp+fp.dp` | `--cpu 8.1-M.Main` |

In these Arm Compiler options, `+nomve` suppresses Helium generation, and `+nofp` also implies `+nomve.fp`. The `+mve` architecture feature implies legacy `+dsp`. Keep the matching `--cpu` description on link and disassembly commands so tools interpret the feature set consistently. For example, a Helium-capable disassembly target can be selected with `fromelf -c --cpu=8.1-M.Main.mve.fp test.elf --output list.txt`. CDE disassembly additionally requires `-coprocN=cde` (where `N` is the coprocessor number); the article says CDE is unavailable on Cortex-M55/M85 revision 0.

ACLE C and C++ code can use `__ARM_FEATURE_MVE` to select an MVE-specific implementation. Its higher bit indicates MVE floating-point support, for example:

```c
#if (__ARM_FEATURE_MVE & 2)
  /* MVE floating-point implementation */
#endif
```

This is a compile-time feature test. It does not establish that runtime CP10/CP11 access has been enabled; startup configuration is covered by [techniques-armv81m-feature-initialization](techniques-armv81m-feature-initialization.md). The Arm Compiler flags and version advice here are source-specific and should not be treated as GCC/LLVM flags or a current toolchain recommendation.
