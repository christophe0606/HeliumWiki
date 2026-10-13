---
id: techniques-cortex-m-branch-prediction
title: Enable branch prediction using the control specific to each Cortex-M revision
type: techniques
architectures:
  - cortex-m55
  - cortex-m85
tags:
  - branch-prediction
  - low-overhead-branch
  - processor-initialization
  - c
confidence: source-reported
reproducibility: snippet
related:
  - techniques-armv81m-feature-initialization
  - techniques-helium-low-overhead-loop-alignment
sources:
  - https://developer.arm.com/community/arm-community-blogs/b/architectures-and-processors-blog/posts/armv8_2d00_m-based-processor-software-development-hints-and-tips
aliases:
  - Cortex-M85 CCR BP
  - Cortex-M55 r1 static branch prediction
  - ACTLR DISLOBR
prerequisites:
  - Identify the Cortex-M core and revision before changing prediction controls.
  - Make register changes from suitable privileged initialization code.
---

Branch-prediction controls differ between Cortex-M85 and Cortex-M55 revisions. Use the control that applies to the exact core and revision; the settings below are source-reported and should not be generalized across revisions.

The article says branch prediction is disabled by default on Cortex-M85. Enable it by setting `CCR.BP` and then synchronizing instruction execution with DSB and ISB. With CMSIS-CORE, the example is:

```c
SCB->CCR |= SCB_CCR_BP_Msk;
__DSB();
__ISB();
```

Cortex-M55 r1 supports limited static branch prediction by reusing low-overhead branch hardware, which the article says may help in a few cases. On r1p0, it is disabled by default and can be enabled by clearing bit 5 (`DISLOBR`) in `ACTLR`. On r1p1, that bit is cleared by default. This is distinct from Cortex-M85's `CCR.BP` control, and the article makes no corresponding claim for Cortex-M55 r0.

Check the core revision and the intended low-overhead branch behavior before changing `ACTLR`; do not assume that enabling this limited M55 behavior has the same effect as setting M85 `CCR.BP`. See [techniques-armv81m-feature-initialization](techniques-armv81m-feature-initialization.md) for the separate low-overhead branch enablement setting.
