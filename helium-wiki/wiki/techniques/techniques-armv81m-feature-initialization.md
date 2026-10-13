---
id: techniques-armv81m-feature-initialization
title: Enable low-overhead branch and Helium during Cortex-M startup
type: techniques
architectures:
  - armv8.1-m
  - cortex-m55
  - cortex-m85
tags:
  - processor-initialization
  - low-overhead-branch
  - helium
  - mve
  - floating-point
  - c
confidence: source-reported
reproducibility: snippet
related:
  - techniques-arm-compiler-mve-target-configuration
  - techniques-cortex-m-branch-prediction
  - techniques-helium-low-overhead-loop-alignment
  - techniques-armv8m-cache-management
sources:
  - https://developer.arm.com/community/arm-community-blogs/b/architectures-and-processors-blog/posts/armv8_2d00_m-based-processor-software-development-hints-and-tips
aliases:
  - enable Helium at startup
  - enable low-overhead branch
  - Armv8.1-M runtime feature setup
  - CPACR CP10 CP11
prerequisites:
  - Run from privileged startup code on a processor implementing the selected feature.
  - Configure the relevant Secure and Non-secure permissions when using TrustZone.
---

Armv8.1-M low-overhead branch and Helium support require runtime setup in addition to matching compiler target flags. Perform this during privileged startup before executing code that depends on the feature; CMSIS-CORE startup normally handles the low-overhead branch setting in `SystemInit()`.

The Loop and branch info cache used by the low-overhead branch extension is disabled after reset. Set the `CCR.LOB` bit to enable it. This hardware cache is separate from instruction and data caches. The control is banked by security state: Secure and Non-secure privileged software enable their respective copies, or Secure privileged software can set the Non-secure copy. After changing it, execute an ISB; the article's CMSIS example uses DSB followed by ISB:

```c
SCB->CCR |= SCB_CCR_LOB_Msk;
__DSB();
__ISB();
```

Helium instructions, like floating-point instructions, require coprocessors 10 and 11 to have full access in `CPACR`. Configure this before using either instruction set, then issue DSB and ISB:

```c
SCB->CPACR |= (3U << (10U * 2U)) | (3U << (11U * 2U));
__DSB();
__ISB();
```

For a TrustZone system, Secure privileged startup code also configures `NSACR` and `CPPWR` to establish whether Non-secure software can access Helium and floating-point features. Compiler feature selection alone does not grant these runtime permissions. This guidance requires privileged startup code and hardware that implements the relevant features.
