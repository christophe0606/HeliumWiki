---
id: techniques-cortex-m-data-prefetch-and-cache-hints
title: Evaluate Cortex-M hardware data prefetch and core-specific cache hints
type: techniques
architectures:
  - cortex-m52
  - cortex-m85
  - cortex-m55
tags:
  - cache
  - cache-management
  - instruction-scheduling
  - data-placement
  - asm
confidence: source-reported
reproducibility: concept
related:
  - techniques-armv8m-cache-management
  - techniques-cortex-m85-memory-access-scheduling
  - techniques-cortex-m-memory-access-scheduling
  - hardware-dtcm-scatter-gather-banks
  - patterns-helium-dtcm-dma-pipeline
sources:
  - https://support.arm.com/documentation/107950/0100
  - https://support.arm.com/documentation/107730/0003
  - https://github.com/Arm-Examples/Helium-Optimization/blob/bc9dfb67be64a2a5ee8e5325910a3f060a593863/General_optimizations/processor_specific.md#L40-L45
  - https://github.com/Arm-Examples/Helium-Optimization/blob/bc9dfb67be64a2a5ee8e5325910a3f060a593863/Memory/Software_optimization_for_memory_constrained_devices.md#L105-L115
aliases:
  - Cortex-M85 hardware data prefetch
  - M85 PLD PLDW hints
  - M85 transient cache attribute
  - Cortex-M85 streaming cache traffic
  - Cortex-M52 hardware data prefetch
  - Cortex-M52 PREFETCH and PFCR
  - Cortex-M55 linear-stream data prefetch
  - Cortex-M52 PREFETCH availability by revision
evidence_basis: M52 r0p3 reports conditional hardware-prefetch inclusion and PFCR control; M85 r1p0 reports separate stream coverage, hint, and transient replacement behavior. Any cache-use advice is core-scoped and source-reported or explicitly identified as inference.
---

Use this page when checking data-prefetch support or cache hints on Cortex-M52, Cortex-M55, or Cortex-M85. The M52 r0p3 and M85 r1p0 sections follow their processor guides; the M55 section follows the repository's processor-specific article. Prefetcher inclusion, stream coverage, hint semantics, and replacement behavior differ by core and system configuration, so follow the matching section. The guides provide no measured workload speedups.

## Cortex-M85 r1p0, Issue 01

For streaming data on Cortex-M85 r1p0, first determine whether the configured L1 data cache and hardware prefetcher cover the access pattern. Data-cache misses stall the pipeline, but the guide reports no measured prefetch speedup. Its documented hardware coverage is limited to constant-stride streams and has an 8 KB boundary, so irregular gathers and other patterns need separate evaluation. [Arm Cortex-M85 Processor Software Optimization Guide, r1p0, Issue 01 (26 April 2023), section 2.2, page 12; section 4.7, page 45]

## Understand hardware data-prefetch coverage

When the processor is configured with an L1 data cache, its hardware data prefetcher detects misses in streaming data-access patterns. It recognizes constant strides in the forward or backward direction within two cache lines of observed miss addresses. Hardware prefetch does not cross aligned 8 KB boundaries. The guide does not specify cache-line size, so retain the scope in cache lines rather than converting it to bytes. [section 4.7, page 45]

Do not assume this behavior covers arbitrary irregular gathers, every stride, TCM-resident data, or an access that crosses the aligned 8 KB boundary. A cache miss can still stall the pipeline, and the guide supplies no measured improvement attributable to hardware prefetch. [sections 2.2 and 4.7, pages 12 and 45]

## Use explicit prefetch hints selectively

`PLD` and `PLDW` create data-cache line fills with read-allocation and write-allocation behavior, respectively. Their hint-table rows list throughput 1 and issue field `11`; the guide does not give a load-result latency for them. `PLI` behaves as a NOP on this processor, so do not use it as an effective instruction-cache prefetch. [section 3.8, page 28; section 4.8, page 45]

The guide advises against explicit software prefetch when hardware prefetch already covers the access pattern, because `PLD`/`PLDW` consume pipeline bandwidth. For a pattern outside the hardware prefetch scope, a software hint can be an experiment, but the guide specifies neither a best prefetch distance nor an expected speedup. Measure the actual workload before retaining such hints. [section 4.8, page 45]

## Interpret transient as a clean-line replacement preference

The transient memory attribute is implemented as a data-side replacement hint: when replacing clean L1 D-cache lines, the implementation prefers to retain non-transient data over transient data. This documents a preference, not a guarantee of no allocation, immediate eviction, cache bypass, a coherency behavior, or an effect on dirty lines. [section 4.9, page 45]

As an implementation inference from that replacement preference, if platform memory-attribute setup supports it and transient data would compete with reusable clean cache data, consider marking that data transient. The guide excerpt gives no register encoding or setup sequence for the attribute, and the hint does not guarantee a particular cache outcome. [section 4.9, page 45]

These recommendations are scoped to Cortex-M85 r1p0, Issue 01 and the documented cache configuration. Cache-line size, software-prefetch distance, and measured performance effects are not provided by this guide; evaluate them on the target rather than filling in missing values. See [Armv8-M cache management](techniques-armv8m-cache-management.md) for cache activation and maintenance guidance. [sections 2.2, 3.8, and 4.7-4.9, pages 12, 28, and 45]


## Cortex-M52 r0p3, Issue 03

The M52 guide describes a hardware data prefetcher that monitors line-fill addresses for streaming patterns, predicts where later fills may occur, and attempts to fetch data from the system into the D-cache before use. The guide says this can hide load latency, but reports no measured workload speedup. Check the actual SoC configuration before assuming the feature is present: PREFETCH determines inclusion and is applicable only when D-CACHE is present and the main interface is configured for M-AXI/AXI. When included, software can control the prefetcher through the Prefetcher Control Register (PFCR); the guide refers to the Cortex-M52 Technical Reference Manual for PFCR details. It does not provide PFCR bit values, defaults, or an initialization sequence. [Arm China Cortex®-M52 Processor Software Optimization Guide, document 107730_0003_03_en, §4.2, p. 46]

The M52 guide lists PLI at latency 1 and throughput 1 and says it acts as a NOP. It lists PLD/PLDW at latency 1 and throughput 1, but does not specify M52 read/write-allocation semantics, a useful software-prefetch distance, or a measured benefit. Do not import M85 hint semantics or advice against software prefetch into M52. [§3.8, p. 30]

The M52 guide does not document the M85 constant-stride detection range, two-cache-line observation window, 8 KB boundary, transient replacement hint, or a blanket prohibition on software prefetch. Keep those details in the M85 section only. The revision appendix says the r0p3 release added §4.2 and cites page 45, while the actual hardware-prefetcher section is on page 46; citations here use the section's actual page. [Appendix A, p. 47; §4.2, p. 46]

For memory-transfer timing on M52, see [Cortex-M52 and Cortex-M55 memory-access scheduling](techniques-cortex-m-memory-access-scheduling.md).

## Cortex-M55 linear streams and memory placement

The processor-specific source describes Cortex-M55 recognition of constant strides of -2, -1, +1, or +2 in data-array units. It does not specify the element size for those units, so do not translate them into byte strides, neighboring prefetch targets, or a fixed cache-line distance. Consult the matching core TRM for prefetch control details and check the actual access pattern before relying on hardware prefetch.

When a kernel uses several streams, evaluate whether the stream intended for cache prefetch remains in cacheable main memory while other streams use an appropriate TCM or noncacheable region. This is a workload experiment, not a general placement rule: TCM capacity, DMA reachability, cache behavior, and memory ownership still apply. Sequential cached access may work well without copying every input to DTCM, so compare the actual memory paths and working set before consuming scarce TCM.

Keep the M52 revision-specific information already recorded above. The memory article says M52 revision 0 lacks data prefetch, while the M52 r0p3 guide records conditional `PREFETCH` inclusion. Check the device's exact revision and integration against its matching documentation; these sources do not justify a blanket claim about every M52 implementation. The M85 next-line and transient-hint behavior remains in the M85 sections and should not be inferred for M55. See [TCM workspaces and DMA pipelines](../patterns/patterns-helium-dtcm-dma-pipeline.md) when deciding which buffers should occupy TCM.
