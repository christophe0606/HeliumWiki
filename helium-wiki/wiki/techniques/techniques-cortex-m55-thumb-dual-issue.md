---
id: techniques-cortex-m55-thumb-dual-issue
title: Use eligible 16-bit Thumb encodings for Cortex-M55 dual issue
type: techniques
architectures:
  - cortex-m55
tags:
  - instruction-scheduling
  - asm
confidence: source-reported
reproducibility: concept
related:
  - techniques-cortex-m55-latency-aware-scheduling
  - techniques-cortex-m-branch-prediction
sources:
  - https://support.arm.com/documentation/102692/0101
aliases:
  - Cortex-M55 Thumb dual issue
  - Cortex-M55 16-bit instruction pairing
  - Cortex-M55 Thumb instruction slots
evidence_basis: Arm's Cortex-M55 r1p1, Issue 03 instruction tables report the encodings eligible for limited dual issue. Recommendations to inspect and select eligible encodings are implementation implications; no speedup is measured.
---

When reviewing a Cortex-M55 r1p1 hot path, consider whether equivalent operations can use 16-bit Thumb encodings that the core can dual-issue. Cortex-M55 has limited dual issue for eligible 16-bit instructions: its fetch unit reads 32-bit words containing either one 32-bit instruction or two 16-bit instructions, and the fetch-data stage can issue one 32-bit instruction or up to two 16-bit instructions. The tables identify slot eligibility by instruction group and list important exceptions. This is an instruction-selection opportunity, not a guarantee that arbitrary adjacent narrow instructions will issue together. [Arm Cortex-M55 Processor Software Optimization Guide, r1p1, Issue 03, §2.2, pp. 12–13; §3.1, p. 16]

## Read the slot and timing fields together

The guide defines execution latency as the minimum delay for an operation that depends on an instruction group, and execution throughput as the maximum instruction rate for that group across the processor microarchitecture. They describe different limits. In the dual-issue column, `01` means the instruction is eligible from slot 0, `11` means it is eligible from either slot, and `00` means it is not dual-issuable. A slot value does not override the row's latency, throughput, notes, dependencies, or applicable instruction-pair rules. [§3.1, p. 16]

Representative 16-bit instruction groups in the tables include:

| Table eligibility | Representative instructions | Qualification |
| --- | --- | --- |
| `11` (either slot) | Immediate ADD and SUB forms, immediate CMP, immediate MOV, sign- and zero-extension (`SXTB`, `SXTH`, `UXTB`, `UXTH`), `NOP`, and `IT` | The applicable row reports throughput 2 for these groups. The SP-based ADD rows are exceptions: some have latency 2 and throughput 1/2 because an SP result is recycled for the stack-limit check. |
| `01` (slot 0 only) | Register ALU operations such as `AND`, `BIC`, `CMP`, `EOR`, and `ORR`; register MOV/MVN forms; `MUL`; single loads and stores | These rows generally report throughput 1. `ADD (register) (T2)` is marked `01(00)`: its note says it does not dual-issue when `Rd=PC` or `Rm=PC`. |
| `00` (no dual issue) | `CMN (register) (T1)`, `CBZ`/`CBNZ`, load/store-multiple operations, `PUSH`, and `POP` | The corresponding rows mark these instructions as not dual-issuable; multiple-register rows also report their own `N`-dependent throughput. |

These are examples, not a complete pairing recipe. Use the exact table row for the emitted encoding, operands, and instruction effects. In particular, do not infer eligibility for every 16-bit instruction from its width alone. [§3.2, Tables 3-1–3-2, pp. 17–18; §3.3, Table 3-4, pp. 23–24; §3.4, Table 3-6, p. 25; §3.5, Table 3-8, p. 27; §§3.6–3.8, Tables 3-10–3-14, pp. 29–31]

## Preserve row-specific restrictions

- **SP updates:** The 16-bit `ADD SP` rows with the stack-limit-check note incur a pipeline bubble, with latency 2 and throughput 1/2. Do not replace an SP update with another form on the assumption that every narrow ADD is throughput 2; use the exact row and preserve stack behavior. [§3.3, Table 3-4 and note 2, p. 24]
- **PC operands:** The register ADD and MOV rows carry PC-specific restrictions. The guide says `ADD (register) (T2)` cannot dual-issue when `Rd` or `Rm` is PC; it separately says `MOV PC, Rm` can only be single-issued. [§3.3, Table 3-4 and note 1, p. 24; §3.4, Table 3-6 and note 1, p. 25]
- **Branches:** `CBZ` and `CBNZ` are marked `00`, while 16-bit immediate `B (T2)` is marked `11`; the table also reports branch latency behavior for backward branches. Note 3 on p. 18 is internally unclear: it describes a conditional branch as the first instruction in a pair, then says the first instruction must be an unconditional immediate `B (T2)`. Treat that wording as unresolved and do not derive a branch-pair recipe from it. [§3.2, Table 3-2, pp. 17–18]
- **Dependencies and scheduling:** The decode stage reads operands for most instructions and contains hazard logic; the guide also describes forwarding into decode. Thus table eligibility alone does not establish that a particular dependent pair can issue together. Check the actual instruction sequence and applicable architectural pairing rules. [§2.2, p. 13; §3.1, p. 16]
- **Multiple-register transfers:** The listed 16-bit LDM/POP and store-multiple rows are not dual-issuable. The guide gives `N = floor((num_regs + 1) / 2)` and throughput `1/N` for these groups. [§3.6, Table 3-10, p. 29; §3.7, Table 3-12, p. 30]
- **NOP and IT:** Their 16-bit table rows are marked `11` with throughput 2, but this does not make inserting NOPs a useful general optimization. [§3.8, Table 3-14, p. 31]

For implementation work, inspect the assembled hot path to confirm which Thumb widths and operands the compiler emitted, then check whether the eligible instructions actually form legal pairs. Any expected throughput benefit is an inference from the guide's tables and must be measured on the target workload; the guide supplies no measured speedup for this instruction-selection strategy. The timing tables describe instruction behavior and do not by themselves establish end-to-end performance. [§2.2, pp. 12–13; §3.1, p. 16]
