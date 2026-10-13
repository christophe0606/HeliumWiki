---
id: techniques-helium-instruction-interleaving
title: Interleave different Helium instruction types to overlap execution
type: techniques
architectures:
  - cortex-m55
  - cortex-m85
tags:
  - instruction-scheduling
  - helium
  - mve
  - asm
confidence: source-reported
reproducibility: concept
related:
  - techniques-helium-auto-vectorization
  - techniques-helium-low-overhead-loop-alignment
  - techniques-cortex-m55-latency-aware-scheduling
  - techniques-cortex-m55-floating-point-scheduling
  - techniques-cortex-m55-memory-access-scheduling
  - hardware-dtcm-scatter-gather-banks
sources:
  - https://developer.arm.com/community/arm-community-blogs/b/architectures-and-processors-blog/posts/armv8_2d00_m-based-processor-software-development-hints-and-tips
  - https://support.arm.com/documentation/102692/0101
aliases:
  - Helium instruction scheduling
  - MVE instruction interleaving
  - instruction overlap
  - assembly scheduling
  - Cortex-M55 MVE two-tick overlap
  - M55 E2 E3 SRF write hazards
  - Cortex-M55 I F LS SY pipeline scheduling
---

In hand-optimized Helium assembly for M55 or M85, a run of one instruction type may leave opportunities to overlap execution unused. Interleave different types of Helium instructions in the sequence so the processor can work on their execution concurrently.

Preserve true data dependencies when changing the order, and inspect the resulting code for the target processor. The article gives this qualitative scheduling guideline only: it supplies no instruction-pair schedule, latency table, or measured speedup, so there is no universal ordering to apply mechanically.

## Cortex-M55 r1p1 two-tick scheduling model

For Cortex-M55 r1p1 (Arm Cortex-M55 Processor Software Optimization Guide r1p1, Issue 03), a 128-bit MVE vector instruction is processed as two 64-bit micro-operations called ticks; each tick executes two 32-bit beats. Tick 1 of an older instruction can execute alongside tick 0 of a newer instruction, and the timing tables describe overlap for up to two beatwise MVE instructions. The timing tables define latency as the minimum delay seen by a dependent operation and throughput as the maximum instruction rate for a group; neither is an application loop cycle count. [§2.2, pp. 11–15; §3.1, p. 16; §4.1, p. 46]

Use the utilized-pipeline labels from the exact instruction row: `I` is the Integer Vector pipe, `F` the Floating Point pipe, `LS` the Load/Store pipe, and `SY` the System Registers pipe. MVE instructions are decoded in E0, and the EPU runs in lock-step with the DPU. E0 checks resource use and data availability; if a hazard stalls E0, the overlap does not happen. In general, the older instruction's tick 1 and the newer instruction's tick 0 must use different pipes. [§2.2, pp. 14–15; §3.1, p. 16; §4.1, p. 46]

### Use each encoding's pipeline assignment

| Instruction examples | Source-reported pipeline and timing | Scheduling meaning |
| --- | --- | --- |
| Many integer vector arithmetic, bitwise, shift, move, duplicate, negate, and select groups | Usually `I`; many listed groups have latency 1 and throughput 1/2. | Integer-vector instructions do not all share the same pipe; check exceptions below. |
| Integer vector compare (`VCMP`, including its VPT forms) and integer vector multiply groups | `F`; multiply rows include latency 2 and throughput 1/2. | Integer data type alone does not imply `I`. |
| Floating-point vector arithmetic and multiply groups | `F`; listed common arithmetic and multiply rows include latency 2 and throughput 1/2. | Check forwarding and following-instruction restrictions for FP compare/VPT rows. |
| Scalar-lane `VMOV` from a general-purpose register to a vector lane | `I/F`; the note says issue to `I` if available, otherwise to `F`; latency 1, throughput 1. | Its pipe can depend on availability, so do not assume a fixed pipe when scheduling a following operation. |
| Scalar-lane `VMOV` from a vector lane to a general-purpose register | `F`; latency 1, throughput 1; the table points to the E2 SRF write-port hazard. | Account for its scalar-register write stage as well as its pipe. |
| Continuous vector loads and stores, `VLD2`/`VLD4`, and `VST2`/`VST4` | `LS`. Continuous loads/stores commonly have latency 1, throughput 1/2; `VLD2`/`VLD4` have latency 2, throughput 1/2. | A memory instruction's actual form determines its pipe and timing. |
| Some gather-load and scatter-store variants | `I & LS` for the listed encodings, including gather-load `T5`/`T6` and scatter-store `T5`/`T6`. | These forms use two pipes; use only the mixed-pipe ordering rule that the guide gives for the gather-load rows. |
| `VCTP`, vector system-register transfers, `VMRS`/`VMSR`, `VPNOT`, and `VPST` | `SY`; latency 1, throughput 1. | The guide explicitly says instructions using `SY` can overlap with themselves, an exception to the general different-pipe rule. |
| `VABAV` | `I & F`; latency 5, throughput 1/4. Its first cycle is in `I`, second in `F`. | Follow the specific mixed-pipe ordering note below. |

These are representative groups, not a replacement for the latency-table row: utilization can differ by instruction variant. The guide also gives element-size-dependent timings for reductions and mixed-pipe memory variants. [§3.10, Tables 3-16, pp. 34–40; §3.11, Table 3-17, pp. 40–41; §3.12, Table 3-18, pp. 42–43; §3.13, Table 3-19, pp. 43–44; §§3.14–3.15, Tables 3-20–3-21, pp. 44–45]

### Scalar instructions that may overlap

The guide lists scalar classes that are allowed to overlap tick 1 of the preceding vector instruction: immediate branches (`B`, `BL`, `CB[N]Z`), low-overhead-loop instructions, Branch Future instructions (which are NOPs), and integer arithmetic. From the integer-arithmetic class, it excludes divide, every `CSEL` form, MVE scalar shifts, and PC-modifying instructions. Loads and stores can also overlap, except load/store multiple and PC-modifying forms. “Allowed” is conditional on hazards and does not guarantee overlap in a particular sequence. [§4.1, p. 46]

The guide also names limits: arithmetic cannot overlap a vector load/store that writes its base back to a scalar register; an instruction that checks the stack limit does not overlap; a scalar cannot overlap a vector instruction carrying an implicit `LE` (the final instruction in a low-overhead loop); and a scalar/vector dependency makes overlap unlikely. A floating-point VPT row separately warns that it cannot overlap a following `I`-pipe instruction because there is no `F`-to-`I` forwarding. [§4.1, p. 46; §3.12, Table 3-18, pp. 42–43]

For EPU data dependencies, results from E2 and E3 can be forwarded to following instructions of the same class. Forwarding is not supported between different classes, including floating-point to fixed-point operations and vector to scalar floating-point operations. Resource overlap and data forwarding are separate checks: a different-pipe pair can still be blocked by a dependency. [§2.2, p. 14]

### Preserve the mixed-pipeline ordering notes

For `VABAV`, the first cycle uses `I` and the second uses `F`. The guide says fully overlapped execution requires the older instruction to use a non-`I` pipe and the younger instruction to use a non-`F` pipe. For gather-load `T5`/`T6` rows using `I & LS`, the first cycle is in `LS` and the second in `I`; the corresponding condition is older instruction on a non-`LS` pipe and younger instruction on a non-`I` pipe. These are specific ordering rules for the noted instruction groups, not a general recipe for all mixed-pipe instructions. [§3.10, Table 3-16, p. 40; §3.14, Table 3-20, p. 44]

The gather-load and store footnotes are not interchangeable: the exact forwarding and dependency effects are listed below. In particular, do not transfer the gather-load latency penalty to stores or other gather encodings. [§3.14, Table 3-20, p. 44; §3.15, Table 3-21, p. 45]

The memory rows distinguish several encodings that look similar at source level:

| MVE memory form | Source-reported timing and pipeline |
| --- | --- |
| Gather load `T1` | Latency `(64 / esize) + 1`, throughput `esize / 64`, `LS`; its note adds 4 cycles to the preceding instruction latency because this form cannot read forwarded data. |
| Gather load `T2`–`T4` | Latency `(64 / esize) + 1`, throughput `esize / 64`, `LS`. |
| Gather load `T5` | Latency `1(2)`, throughput 1/2, `I & LS`; first cycle `LS`, second `I`. |
| Gather load `T6` | Latency 2, throughput 1/4, `I & LS`; first cycle `LS`, second `I`. |
| Scatter store `T1`–`T4` | Latency 1, throughput `esize / 64`, `LS`. |
| Scatter store `T5` / `T6` | Latency 2, throughput 1/2 / 1/4 respectively, `I & LS`. |

The store rows state that dependent store data does not change the preceding instruction's latency. The gather-load pair ordering note applies to `T5`/`T6`; the store table does not give the same LS-then-I ordering rule for its `I & LS` variants. [§3.14, Table 3-20, p. 44; §3.15, Table 3-21, p. 45]

### Avoid same-stage scalar-register write conflicts

Two instructions that write the Scalar Register File (SRF) in E2 cannot overlap each other in E2; the same applies to two E3 SRF writers. The latency tables point to E2 for vector-lane-to-general-register `VMOV` and floating-point min/max reductions, and to E3 for integer reductions and indexed duplicate operations. When a listed instruction carries the E2 or E3 note, retain that restriction even if its utilized pipeline differs from its neighbor's. [§4.1.1–4.1.2, p. 47; §3.11, Table 3-17, pp. 40–41; §3.12, Table 3-18, pp. 42–43; §3.10, Table 3-16, pp. 34, 37, 40]

For the listed integer and floating-point vector min/max reductions, the table gives latency `(64 / esize) + 1` and throughput `esize / 64`. Use only the element sizes supported by the selected instruction variant: the formula gives latency 9 and throughput 1/8 for an 8-bit variant, 5 and 1/4 for a 16-bit variant, and 3 and 1/2 for a 32-bit variant. This does not imply that every reduction supports all three sizes. The integer arithmetic-to-scalar row separately prints latency `3(2)` and throughput 1/2; its footnote points to the E3 write hazard but does not explain the parenthetical latency value. Preserve that ambiguity instead of assigning a condition to the `2`. [§3.10, Table 3-16, pp. 34, 40–41; §3.12, Table 3-18, pp. 42–43]

The MVE scalar-shift rows report latency `2(5)` and throughput `1(1/4)`. Their note says that with `CPACR.CP10 != 0b00`, execution uses the EPU with shorter latency and higher throughput; when `CPACR.CP10 == 0b00`, execution uses the DPU and the longer latency/lower throughput appear in parentheses. MVE scalar shifts are also excluded from the scalar/vector overlap list. [§3.11, Table 3-17, p. 41; §4.1, p. 46]

As a scheduling implication, classify the exact assembled instructions by pipe, write stage, forwarding class, and variant before interleaving them. Then preserve dependencies and the explicit mixed-pipe ordering notes, and verify overlap in the target workload. The guide reports architectural timing and hazard conditions, not measured speedups from a particular reordered sequence.
