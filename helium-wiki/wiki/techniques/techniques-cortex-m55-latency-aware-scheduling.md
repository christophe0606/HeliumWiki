---
id: techniques-cortex-m55-latency-aware-scheduling
title: Schedule scalar Cortex-M55 instructions using latency and dependency costs
type: techniques
architectures:
  - cortex-m55
tags:
  - instruction-scheduling
  - asm
confidence: source-reported
reproducibility: concept
related:
  - techniques-cortex-m55-thumb-dual-issue
  - techniques-helium-instruction-interleaving
  - techniques-cortex-m55-memory-access-scheduling
  - techniques-cortex-m55-floating-point-scheduling
sources:
  - https://support.arm.com/documentation/102692/0101
aliases:
  - Cortex-M55 scalar instruction scheduling
  - Cortex-M55 instruction latency
  - scalar Thumb scheduling
evidence_basis: Arm's Cortex-M55 pipeline description and instruction timing tables; timing figures are source-reported, while scheduling choices below are implications rather than measured speedups.
---

For hand-scheduled Thumb code or hot-path compiler output on Cortex-M55 r1p1, Issue 03, account for the actual instruction encoding and producer-to-consumer latency. A sequence of nominally simple instructions can still be limited by a dependent chain, a shifted operand, a stack-pointer update, or a long divide. The figures below cover scalar integer instructions; they do not transfer to Cortex-M85, floating-point, or MVE timing. [Arm Cortex-M55 Processor Software Optimization Guide, §2.2, pp. 11–15; §3.1, p. 16]

## Read the timing values as separate measures

The guide defines execution latency as the minimum delay observed by an operation that depends on an instruction group. Execution throughput is the maximum instruction rate for that group across the processor microarchitecture. A low latency does not imply the same throughput, and neither value by itself gives the cycle count of a loop. T1/T2 and other encoding variants have separate rows; use the row for the encoding and operand conditions present in the final code. [§3.1, p. 16]

The integer pipeline has four stages. Cortex-M55 is fully in order: a stall in decode or execution prevents later instructions from progressing. Scalar operands for most arithmetic are read in decode; simple arithmetic commonly completes in EX, while SIMD, saturating, multiply, and other complex operations use CX. Arithmetic results can be forwarded from EX and CX to decode. These facts make dependency latency relevant to ordering, but do not guarantee that arbitrary independent instructions will overlap or remove a stall. [§2.2, pp. 11–15]

## Source-reported scalar timing patterns

| Instruction class or condition | Timing reported by the guide | Scheduling use |
| --- | --- | --- |
| Many 32-bit Thumb basic arithmetic and logical forms | Commonly latency 1, throughput 1 instruction/cycle. Some rows show conditional parenthetical values. | Check the specific table row and note; do not treat every ALU encoding as identical. |
| 32-bit scalar SIMD, saturating, packed-halfword/SEL, and several extend-and-add forms | The listed groups commonly have latency 2, throughput 1. | Include the extra dependent-operation delay when comparing a chain against an equivalent sequence. |
| Note-tagged shifted-register ALU forms | The notes say a nonzero shift raises latency from 1 to 2 and gives throughput 1. Some table rows print additional parenthetical throughput alternatives. | Apply the condition to the listed encoding only. In particular, the ORN/ORR register row prints throughput `1(1/2)` while Note 2 describes nonzero shifts as throughput 1; the guide does not make the `1/2` condition clear, so verify that exact case rather than assigning it by inference. |
| Selected 32-bit ADD/SUB forms that write SP, and listed 16-bit ADD SP forms | Reusing EX for the stack-limit check can add a bubble; the affected rows report latency 2 and throughput 1/2. | Account for the row-specific cost. The guide also lists 32-bit immediate ADDW/SUBW SP forms at latency 1, throughput 1, so do not generalize the penalty to every SP update. Preserve the stack-limit check. |
| 16-bit Thumb instructions | Dual issue is limited to eligible encodings. Some immediate ADD and MOV-immediate forms reach throughput 2; many other 16-bit groups remain at throughput 1. | Narrow encoding alone does not mean dual issue; check the row's slot eligibility and operands. |
| 32-bit MUL and listed scalar multiply/accumulate groups; 16-bit MUL | Latency 2, throughput 1. The 16-bit MUL is dual-issue slot 0 only. | Leave the dependent-use distance in the critical path; observe the slot restriction when considering a 16-bit pair. |
| SDIV and UDIV | Operand-dependent latency from 2 to 12 cycles; an iterative divide blocks subsequent divide instructions until it finishes. | Assess actual numerator and denominator values on the application's critical path; do not assume a fixed divide cost. |

These values and conditions are summarized from the arithmetic/logical and move tables and their notes. In particular, the guide reports many basic 32-bit arithmetic/logical operations at 1/1, but has explicit exceptions and conditional entries; selected 16-bit ADD SP forms create a stack-limit-check bubble, while wide immediate SP forms have their own 1/1 rows. [§3.3, pp. 18–24; §3.4, pp. 24–25; §3.5, pp. 25–27]

For SDIV/UDIV, the guide defines `DIFF_SIGN` as the denominator's leading-sign-bit count minus the numerator's; for UDIV the counts are leading zeros. If `DIFF_SIGN < 0`, it reports latency 3 and throughput 1/2. If `DIFF_SIGN >= 0`, latency is `4 + ceil(DIFF_SIGN / 4)` and throughput is `1 / (3 + ceil(DIFF_SIGN / 4))`. Divide-by-zero is listed as latency 2 and throughput 1; that timing entry is a reference case, not a recommendation to divide by zero or a guarantee about exception configuration. Preserve the program's arithmetic and fault behavior when evaluating alternatives. [§3.5, pp. 25–27]

## Scheduling implications

When independent work is already available, consider placing it before the consumer of a longer-latency result, while preserving true dependencies and program behavior. Compare equivalent instruction sequences using their actual encodings, operand shifts, SP effects, multiply/divide behavior, and dual-issue eligibility. These are inferences from the guide's latency and pipeline descriptions; the guide does not report measured gains for such rearrangements. [§2.2, pp. 11–15; §3.1, p. 16; §§3.3–3.5, pp. 18–27]

Some other scalar timing rows are useful only for particular existing work: 16-bit MOV-immediate has throughput 2, while common 32-bit MOV/MOVT forms have throughput 1; MOV PC,Rm is single-issue and has a separate parenthetical timing. CLRM clears two registers per cycle; for `num_regs` registers, the guide gives `N = floor((num_regs + 1) / 2)`, latency `N + 1`, and throughput `1/N`. Consider CLRM when the program already needs to clear several scalar registers, not as a reason to clear extra state. [§3.4, pp. 24–25; §3.8, p. 31]

The same miscellaneous table says PLI acts as a NOP, so do not infer a prefetch benefit from it. PLD/PLDW rows report latency 1 and throughput 1, but the guide does not establish a useful prefetch distance or application speedup. 16-bit NOP and IT rows can reach throughput 2 and dual issue in either slot; adding NOPs is not a general optimization. [§3.8, p. 31]

## Limits

The table values describe instruction timing with required resources and data available; they are not end-to-end measurements. The pipeline overview says unaligned accesses are decomposed into aligned requests and stall the original instruction in EX, and the load/store unit stalls the DPU until read data is available. Check the complete hot path and target binary when memory or instruction-fetch behavior can affect the result. No measured speedups are supplied by this guide. [§2.2, pp. 12–15; §§3.1, 3.3–3.8, pp. 16–31]
