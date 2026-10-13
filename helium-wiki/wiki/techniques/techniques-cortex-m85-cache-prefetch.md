---
id: techniques-cortex-m85-cache-prefetch
title: Use Cortex-M85 prefetch and transient hints to manage streaming cache traffic
type: techniques
architectures:
  - cortex-m85
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
  - hardware-dtcm-scatter-gather-banks
sources:
  - https://support.arm.com/documentation/107950/0100
aliases:
  - Cortex-M85 hardware data prefetch
  - M85 PLD PLDW hints
  - M85 transient cache attribute
  - Cortex-M85 streaming cache traffic
evidence_basis: Arm Cortex-M85 r1p0, Issue 01 cache prefetch, hint, and transient replacement behavior. Suggested use of transient attributes is an implementation inference from the source-reported replacement preference.
---

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
