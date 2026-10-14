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
  - instruction-scheduling
  - low-overhead-branch
  - helium
  - mve
  - floating-point
  - c
  - asm
confidence: source-reported
reproducibility: snippet
related:
  - techniques-arm-compiler-mve-target-configuration
  - techniques-cortex-m-branch-prediction
  - techniques-helium-low-overhead-loop-alignment
  - techniques-armv8m-cache-management
  - techniques-cortex-m-latency-aware-scheduling
  - techniques-helium-instruction-interleaving
sources:
  - https://developer.arm.com/community/arm-community-blogs/b/architectures-and-processors-blog/posts/armv8_2d00_m-based-processor-software-development-hints-and-tips
  - https://support.arm.com/documentation/102692/0101
  - https://github.com/arm-education/Arm-Helium-Technology/blob/main/HeliumTechnology_referencebook.pdf
aliases:
  - enable Helium at startup
  - enable low-overhead branch
  - Armv8.1-M runtime feature setup
  - CPACR CP10 CP11
  - Cortex-M55 scalar shift EPU timing
  - CP10 scalar shift latency
prerequisites:
  - Run from privileged startup code on a processor implementing the selected feature.
  - Configure the relevant Secure and Non-secure permissions when using TrustZone.
---

Armv8.1-M low-overhead branch and Helium support require runtime setup in addition to matching compiler target flags. Perform this during privileged startup before executing code that depends on the feature; CMSIS-CORE startup normally handles the low-overhead branch setting in `SystemInit()`. The scalar-shift timing guidance below is specific to Cortex-M55 r1p1, Issue 03, and does not establish corresponding Cortex-M85 timing.

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

## Distinguish hardware capability from access permission

For portable runtime dispatch, read the Media and VFP Feature Register 1 (`MVFR1`) to determine the implemented MVE level: the documented field distinguishes no MVE, integer-only MVE, and integer plus floating-point MVE. This runtime capability check is separate from the compiler's `__ARM_FEATURE_MVE` macro, which describes the build target. It is also separate from `CPACR` and, when TrustZone is used, `NSACR` permissions: detecting implemented hardware does not enable access for the current security and privilege state. [Arm Helium Technology: M-Profile Vector Extension (MVE) for Cortex-M Processors, Reference Book, PDF pp. 157–158]

The reference book's low-overhead loop-cache startup statement and cited CMSIS startup example are specific to Cortex-M55. Keep that implementation detail within M55 scope; use the applicable processor documentation and startup code for other Armv8.1-M implementations. Retain the required DSB and ISB barriers and current processor-specific setup guidance when changing startup code. [Arm Helium Technology: M-Profile Vector Extension (MVE) for Cortex-M Processors, Reference Book, PDF p. 158]

## Cortex-M55 r1p1 MVE scalar-shift timing

For the MVE integer scalar shifts listed in the Cortex-M55 r1p1 instruction table, `CPACR.CP10 != 0b00` selects execution in the EPU, with latency 2 and throughput 1 instruction per cycle. When `CPACR.CP10 == 0b00`, those scalar shifts execute in the DPU, with the parenthesized timing of latency 5 and throughput 1/4 instruction per cycle. The listed forms include `ASRL`, `LSLL`, `LSRL`, `SQRSHR`, `SQRSHRL`, `SQSHL`, `SQSHLL`, `SRSHR`, `SRSHRL`, `UQRSHL`, `UQRSHLL`, `UQSHL`, `UQSHLL`, `URSHR`, and `URSHRL`, with the immediate or register operands specified in Table 3-17. This is a scalar-shift fallback described by that table; do not generalize it to arbitrary vector instructions when CP10 is disabled. [Arm Cortex-M55 Processor Software Optimization Guide, r1p1, Issue 03, §3.11, Table 3-17 and note 3, p. 41]

The table's `CP10 != 0b00` condition distinguishes the timing path; it is not a grant of permission to every execution context. Keep the full-access `CP10` and `CP11` startup configuration above for intended Helium and floating-point use, and retain the Secure/Non-secure permission setup required by the system. The timing table does not recommend changing privilege, security, or power policy to obtain the EPU path. [§3.11, Table 3-17 and note 3, p. 41]
