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
  - instruction-scheduling
  - asm
  - processor-initialization
  - c
confidence: source-reported
reproducibility: snippet
related:
  - techniques-armv81m-feature-initialization
  - techniques-cortex-m55-latency-aware-scheduling
  - techniques-cortex-m55-thumb-dual-issue
  - techniques-helium-low-overhead-loop-alignment
sources:
  - https://developer.arm.com/community/arm-community-blogs/b/architectures-and-processors-blog/posts/armv8_2d00_m-based-processor-software-development-hints-and-tips
  - https://support.arm.com/documentation/102692/0101
aliases:
  - Cortex-M85 CCR BP
  - Cortex-M55 r1 static branch prediction
  - ACTLR DISLOBR
  - Cortex-M55 branch latency
  - Cortex-M55 low-overhead loop timing
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

## Cortex-M55 r1p1 branch and loop timing

The Cortex-M55 r1p1, Issue 03 guide provides the following instruction timing rows. Latency is the minimum delay observed by a dependent operation, while throughput is the maximum instruction rate for that group; neither is a direct measure of an optimized loop's total cycle cost. These timing figures apply to the documented M55 revision and do not establish M85 branch timing. [Arm Cortex-M55 Processor Software Optimization Guide, §3.1, p. 16; §3.2, pp. 17–18]

| Instruction group or condition | Source-reported latency and throughput | Interpretation |
| --- | --- | --- |
| 32-bit Branch Future family (`BF`, `BFCSEL`, `BFL`, `BFLX`, `BFX`) | Latency 1, throughput 1; the listed family acts as a NOP. | The row does not establish a branch-prediction benefit for these instructions. |
| 32-bit immediate `B` | Table entries show latency `1(2)` and throughput `1(1/2)`. For the backward-branch condition in Note 2, subsequent branches are predicted taken and latency reduces to 0 when the branch is implied. | The zero-latency statement is conditional; it does not make every backward branch free. Preserve the exact encoding and sequence condition when applying it. |
| 32-bit immediate `BL` | Latency 2, throughput 1/2. | Keep this row distinct from the immediate `B` entries. |
| Low-overhead loop setup/count instructions `DLS`, `DLSTP`, `LCTP` | Latency 1, throughput 1. | These are individual instruction timings, not per-iteration overhead claims. |
| Low-overhead loop end instructions `LE`, `LETP` | Latency 3, throughput 1/3. | Do not interpret the table entry as three extra cycles on every optimized-loop iteration. |
| While-loop instructions `WLS`, `WLSTP` | Table entries show latency `1(3)`, throughput `1(1/3)`. If the while loop is not executed, the branch causes a 3-cycle latency penalty. | The 3-cycle penalty is specifically stated for the not-executed case. |
| 16-bit immediate `B` (`T2`) | Latency `1(2)`, throughput 2, dual-issue field `11`. The backward-branch note describes the conditional zero-latency case above. | Dual issue and the conditional branch prediction are separate table properties; check the actual encoding and context. |
| 16-bit register branches | `BX (T1)`: latency 2, throughput 1, dual-issue field `11`. `CBZ`/`CBNZ`: 3, 1, `00`. `BXNS`: 3, 1, `00`. `BLX`/`BLXNS`: 3, 1, `01`. | These are distinct encodings and dual-issue classes. The guide's note says a branch exchange using LR has reduced latency through late forwarding; apply it only to the applicable LR form. |

The following row is also printed in Table 3-2: “Branch, register (with destination LR)” `BX (T1)`, latency `3(2)`, throughput 1, dual-issue field `11`, Note 3. Note 3 has unclear wording about a conditional branch being dual-issued “as the first instruction in a pair” only if the first instruction is an unconditional immediate `B (T2)`. Keep the parenthetical row value and note scoped to the guide's wording; do not turn the sentence into a branch-pairing recipe. [§3.2, Tables 3-1 and 3-2, pp. 17–18]

## Limited overlap with MVE instructions

The guide says MVE instructions execute as two 64-bit micro-operations (“ticks”). Whether a following instruction overlaps the older instruction's second tick is decided in E0 and depends on resources and data availability; an E0 hazard stall prevents overlap. For Cortex-M55, the listed scalar classes that may overlap the preceding vector instruction's second tick include immediate branches (`B`, `BL`, `CB[N]Z`), low-overhead-loop instructions, and Branch Future instructions (which are NOPs). This describes possible overlap, not a guarantee for every loop body. [§4.1, p. 46]

The guide lists constraints on this overlap: an arithmetic instruction cannot overlap a vector load/store that writes back its base to a scalar register; an instruction that checks the stack limit does not overlap; a scalar cannot overlap a vector instruction carrying an implicit `LE` (the last instruction in a low-overhead loop); and scalar/vector dependencies make overlap unlikely. Apply these conditions before inferring loop timing from the instruction tables. [§4.1, p. 46]
