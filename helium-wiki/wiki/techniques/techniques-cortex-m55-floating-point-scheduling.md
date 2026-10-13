---
id: techniques-cortex-m55-floating-point-scheduling
title: Schedule Cortex-M55 floating-point instructions by precision and dependencies
type: techniques
architectures:
  - cortex-m55
tags:
  - instruction-scheduling
  - floating-point
  - helium
  - mve
  - asm
confidence: source-reported
reproducibility: concept
related:
  - languages-c-float16-half-precision
  - techniques-helium-instruction-interleaving
  - techniques-cortex-m55-latency-aware-scheduling
  - techniques-cortex-m55-memory-access-scheduling
sources:
  - https://support.arm.com/documentation/102692/0101
aliases:
  - Cortex-M55 floating-point scheduling
  - Cortex-M55 FP instruction timing
  - Cortex-M55 scalar and vector floating-point latency
  - Cortex-M55 VFMA versus VMLA latency
  - Cortex-M55 double precision latency
  - Cortex-M55 floating-point divide and square root
evidence_basis: Timing values and pipeline behavior are source-reported for Cortex-M55 r1p1, Issue 03. Scheduling implications preserve dependencies and numerical behavior; the guide provides no measured speedups.
---

For floating-point hot paths on Cortex-M55 r1p1, use the timing row for the operation and precision actually emitted, and account for dependent-result latency separately from throughput. The guide's scalar half/single/double timings differ, and its fused and chained multiply-accumulate instructions have different latency and rounding behavior. The values below are specific to Cortex-M55 r1p1, Issue 03; they are not M85 timings or end-to-end performance measurements. [Arm Cortex-M55 Processor Software Optimization Guide, r1p1, Issue 03, §3.1, p. 16; §3.9, Tables 3-15, pp. 32–34]

## Scalar floating-point timing by precision

In Table 3-15, the values in parentheses are the longer multiple-cycle double-precision values. Execution latency is the minimum delay for a dependent operation; throughput is the maximum instruction rate reported for the instruction group. [§3.1, p. 16; §3.9, Table 3-15 and note 1, pp. 32–33]

| Scalar operation | Half/single latency; throughput | Double latency; throughput |
| --- | --- | --- |
| `VADD`, `VSUB` | 2 cycles; 1 instruction/cycle | 15 cycles; 1/14 instruction/cycle |
| `VMUL`, `VNMUL` | 2 cycles; 1 instruction/cycle | 21 cycles; 1/20 instruction/cycle |
| `VFMA`, `VFNMA` | 2 cycles; 1 instruction/cycle | 24 cycles; 1/23 instruction/cycle |
| `VMLA`, `VNMLA` | 4 cycles; 1/3 instruction/cycle | 36 cycles; 1/35 instruction/cycle |

The guide describes `VMLA.F16` and `VMLA.F32` as a multiply followed serially by an add in E2, with full rounding after each operation in E3. A fused `VFMA` has a different rounding sequence. Where application accuracy, rounding, and exception behavior permit, the lower-latency fused form is a candidate to evaluate; it is not a numerically equivalent replacement in every program. Do not claim a speedup without measuring the actual workload. [§2.2, p. 15; §3.9, Table 3-15, pp. 32–33]

## Divide and square-root cases

| Operation and precision | Ordinary input latency; throughput | Zero, infinity, NaN, or invalid-operation row |
| --- | --- | --- |
| `VDIV` or `VSQRT`, half precision | 9 cycles; 1/8 instruction/cycle | 6 cycles; 1/5 instruction/cycle |
| `VDIV` or `VSQRT`, single precision | 16 cycles; 1/15 instruction/cycle | 6 cycles; 1/5 instruction/cycle |
| `VDIV` or `VSQRT`, double precision | 29 cycles; 1/28 instruction/cycle | 6 cycles; 1/5 instruction/cycle |

The table reports matching special-input rows for divide and square root. These are source timing cases, not a reason to change inputs or arithmetic semantics to seek a faster path. The guide says divide uses an iterative algorithm and blocks subsequent divide operations until it completes; it does not clearly state that square root blocks later divides in the same way, so do not extend that rule to square root. [§3.9, Table 3-15, pp. 32–34, note 3, p. 34]

## Respect EPU forwarding and MVE pipeline limits

The EPU can forward E2 and E3 results to following instructions of the same class. The guide does not support forwarding across floating-point to fixed-point classes or from vector to scalar floating-point instructions. When scheduling dependent EPU work, account for those class boundaries rather than assuming every result can feed the next operation without a stall. [§2.2, pp. 14–15]

Most listed MVE floating-point arithmetic, compare, convert, multiply, absolute-value, and negate operations use the F pipe and report latency 2 with throughput 1/2 instruction per cycle. MVE floating-point reductions (`VMAXNMV`, `VMAXNMAV`, `VMINNMV`, and `VMINNMAV`) instead report latency `(64 / esize) + 1` and throughput `esize / 64`; use the `esize` for the selected instruction variant. The reduction rows also point to the E2 SRF write-port hazard in §4.1.1, so include that constraint when assessing a reduction sequence. [§3.12, Table 3-18 and note 1, pp. 42–43]

The guide describes MVE as a two-beat-per-tick machine that can overlap up to two beatwise instructions when they use different EPU pipelines. Apply that rule with the table's pipeline assignments and dependencies: floating-point `VPT` uses the F pipe and cannot overlap with following I-pipe instructions because there is no F-to-I forwarding path. For general interleaving guidance and its limits, see [techniques-helium-instruction-interleaving](techniques-helium-instruction-interleaving.md). [§3.1, p. 16; §3.12, Table 3-18, p. 42 and note 2, p. 43]

These instruction timings and overlap rules help identify dependency and throughput constraints in a candidate schedule. Inspect the final instruction sequence and preserve its floating-point semantics; the guide does not report application-level gains from rearranging these operations.
