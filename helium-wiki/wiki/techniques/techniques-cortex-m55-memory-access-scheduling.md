---
id: techniques-cortex-m55-memory-access-scheduling
title: Schedule Cortex-M55 memory accesses using encoding and forwarding rules
type: techniques
architectures:
  - cortex-m55
tags:
  - instruction-scheduling
  - data-placement
  - buffer-alignment
  - helium
  - mve
  - data-tcm
  - asm
confidence: source-reported
reproducibility: concept
related:
  - hardware-dtcm-scatter-gather-banks
  - hardware-itcm-instruction-data-contention
  - techniques-helium-instruction-interleaving
  - techniques-cortex-m55-latency-aware-scheduling
sources:
  - https://support.arm.com/documentation/102692/0101
aliases:
  - Cortex-M55 gather forwarding penalty
  - Cortex-M55 multi-register transfer timing
  - MVE memory throughput
  - Cortex-M55 scatter gather scheduling
  - Cortex-M55 memory access latency
evidence_basis: Instruction timings and hazards are source-reported for Cortex-M55 r1p1, Issue 03. Layout and scheduling advice is an implementation implication; the guide reports no workload speedup.
---

When scheduling loads and stores on Cortex-M55 r1p1, distinguish instruction latency, transfer throughput, and waits for memory data. The guide reports different values for scalar multiple transfers, contiguous MVE accesses, and gather/scatter encodings; alignment, forwarding, pipeline use, and actual memory response can add constraints. The timings below are specific to Cortex-M55 r1p1, Issue 03, and are not measurements of an application's memory system. [Arm Cortex-M55 Processor Software Optimization Guide, r1p1, Issue 03, §2.2, pp. 13–15; §3.1, p. 16]

## Scalar load and store timing

The ordinary scalar load rows (including the listed narrow and wide `LDR` forms) report latency 2 and throughput 1 instruction per cycle. `LDRD` has the same timing. Ordinary scalar stores and `STRD` also report latency 2 and throughput 1. These are instruction-table figures; a read can still wait for data in the memory system. [§3.6, Tables 3-9–3-10, pp. 27–29; §3.7, Tables 3-11–3-12, pp. 29–30]

For the listed load-multiple and store-multiple instructions, the tables report latency `N + 1` and throughput `1/N`. The associated note says Cortex-M55 supports two 32-bit accesses per cycle and defines `N = floor((num_regs + 1) / 2)`. The load rows include `LDM`, `LDMIA`, `LDMFD`, `LDMDB`, and `LDMEA`; the store rows include `STM`, `STMIA`, `STMEA`, `STMDB`, and `STMFD`. The 16-bit load table also lists `POP`, and the 16-bit store table lists `PUSH`. Apply the formula to the transfer rows as printed; it is not a general promise that every transfer will proceed at that rate regardless of memory response or other hazards. [§3.6, Tables 3-9–3-10 and note 1, pp. 27–29; §3.7, Tables 3-11–3-12 and note 1, pp. 29–31]

The FP load rows list `VLDR` T1–T3 at latency 2 and throughput 1. The store rows distinguish `VSTR` T2/T3 at latency 1 and throughput 1 from T1 at latency 2 and throughput 1. Check the form actually emitted; these encoding rows do not establish that the forms are interchangeable. [§3.9, Table 3-15, pp. 32–33]

The FP multiple-transfer rows require extra care. Table 3-15 prints latency `(N/2) + 1` and throughput `1/((N/2) + 1)` for `VLDM`, `VLLDM`, and `VSCCLRM` (T1), and the same figures for `VLSTM` and `VSTM` (T1). Its note 2 says Cortex-M55 supports two 32-bit accesses per cycle and defines `N` for **single-precision store-multiple** instructions as `floor((num_regs + 1) / 2)` and for **double-precision store-multiple** instructions as `num_regs`, while the table also includes load and context instructions. Preserve the formula and scope as printed; the note does not define how to reinterpret `N` for every listed load row. Do not silently replace the formula or extend the store-specific definition to those loads. [§3.9, Table 3-15, pp. 32–33; note 2, p. 34]

## MVE load encodings

| Load encoding group | Reported latency | Reported throughput | Pipeline and qualification |
| --- | --- | --- | --- |
| Contiguous `VLDRB`, `VLDRH`, `VLDRW` T1, T2, T5, T6, T7 | 1 | 1/2 instruction/cycle | LS pipe |
| Contiguous `VLD2`, `VLD4` T1 | 2 | 1/2 instruction/cycle | LS pipe |
| Gather `VLDRB/H/W/D (vector)` T1–T4 | `(64 / esize) + 1` | `esize / 64` | LS pipe; `esize` is the variant's element size (8, 16, or 32 bits). T1 has an additional forwarding note described below. |
| Gather T5 | `1(2)` | 1/2 instruction/cycle | I and LS pipes; the condition for the parenthesized latency is not explained by the table note. |
| Gather T6 | 2 | 1/4 instruction/cycle | I and LS pipes |

The T1 gather note says gather loads cannot read forwarded data, so the **preceding instruction's latency** receives an additional 4 cycles when its result feeds that gather. The T2–T4 rows carry the element-size note but not this +4 forwarding note; do not transfer the T1 penalty to those encodings. [§3.14, Table 3-20 and notes 1–2, p. 44]

For the T5 and T6 gather rows, the guide says the first cycle uses LS and the second uses I. For full overlap, it says the older instruction should use a non-LS pipe and the younger instruction a non-I pipe. Table 3-20 prints T5 latency as `1(2)`, but note 3 explains the pipeline order, not the condition for that parenthesized value. Preserve the table's notation and treat its condition as unspecified here rather than assigning it to an assumed case. [§3.14, Table 3-20 and note 3, p. 44]

## MVE store and scatter rows

The scatter-store rows for `VSTRB/H/W/D (vector)` T1–T4 report latency 1, throughput `esize / 64`, and the LS pipe. T5 reports latency 2 and throughput 1/2; T6 reports latency 2 and throughput 1/4, both using I and LS. The contiguous `VSTRB/H/W` T1/T2 rows report latency 1 and throughput 1/2 in LS; T5/T6/T7 rows have the same reported timing. `VST2` and `VST4` T1 also report latency 1 and throughput 1/2 in LS. [§3.15, Table 3-21 and notes 1–2, p. 45]

For the store rows covered by notes 1 and 2, the guide says that when stored data depends on a preceding instruction, the preceding instruction's latency is not affected. This is a specific producer-latency statement; it does not mean the store has no pipeline, memory, ordering, or throughput constraints. Keep the data dependency and other applicable hazards when evaluating a schedule. [§3.15, Table 3-21 and notes 1–2, p. 45]

## Alignment, memory waits, and overlap hazards

The load/store address stage decomposes an unaligned access into constituent aligned requests; while those subrequests execute, the original instruction stalls in DPU EX. The read-data stage stalls the DPU until cache or TCM data is available, and a cache miss can require an M-AXI access. Device-memory accesses cannot be speculative and occur later, after the instruction is committed. These behaviors do not supply a single fixed cycle cost for every unaligned or delayed read. As an implementation implication, prefer natural alignment and contiguous access where the data format and program semantics permit, then measure the actual memory path. [§2.2, pp. 14–15]

MVE overlap is decided using resource and data availability. In particular, arithmetic instructions cannot overlap with vector loads or stores that write back the base address to a scalar register; a dependency between a scalar and vector instruction also makes overlap unlikely. Do not infer that otherwise independent operations will overlap just because they use different pipelines. [§4.1, p. 46]

For the separate one-cycle same-bank vector-load penalty in M55 r1p1 TCM, see [hardware-dtcm-scatter-gather-banks](../hardware/hardware-dtcm-scatter-gather-banks.md). General MVE interleaving limits are covered by [techniques-helium-instruction-interleaving](techniques-helium-instruction-interleaving.md). Confirm the emitted encoding, addresses, dependencies, and memory placement before changing a hot path; preserve access and ordering semantics. The guide does not report measured gains from these schedule or layout changes.
