---
id: techniques-helium-vector-data-alignment
title: Align vector data for the target memory path
type: techniques
architectures:
  - cortex-m55
  - cortex-m85
tags:
  - buffer-alignment
  - data-placement
  - helium
  - mve
confidence: source-reported
reproducibility: concept
related:
  - patterns-cmsis-dsp-helium-migration
  - techniques-cortex-m-memory-access-scheduling
  - techniques-cortex-m85-memory-access-scheduling
  - hardware-dtcm-scatter-gather-banks
sources:
  - https://github.com/Arm-Examples/Helium-Optimization/blob/bc9dfb67be64a2a5ee8e5325910a3f060a593863/General_optimizations/processor_specific.md#L19-L28
aliases:
  - MVE buffer alignment
  - Cortex-M vector data layout
prerequisites:
  - Check the selected instruction, library API, ABI, memory region, and processor documentation for actual alignment requirements.
---

Use this guidance when arranging vector buffers for MVE loads and stores on Cortex-M55 or Cortex-M85 systems. Required alignment depends on the specific instruction, library API, compiler contract, and target; the source's broad word-alignment statement should not be treated as a universal fault rule for every Helium access.

## Correctness requirements versus performance alignment

Separate correctness requirements from performance choices. Satisfy the documented alignment required by the selected access and library contract first. Then, where data is in uncached main memory, compare the actual transfer width and starting address: a vector access that crosses the relevant bus transfer boundary may require additional transfers. For cacheable memory, consider whether the access spans cache lines and whether vector-size alignment reduces split-line accesses. These effects depend on the core, memory path, cache configuration, access width, and actual buffer address.

## Keep alignment, allocation, and tails distinct

Alignment does not make an out-of-range vector access valid. Keep allocation size, padding, and tail handling separate: every lane must be masked, cleaned up, or otherwise kept within the object bounds according to the API contract. Check linker placement and runtime addresses when alignment is intended to affect a physical memory path. See the [CMSIS-DSP migration and buffer contracts](../patterns/patterns-cmsis-dsp-helium-migration.md) and the [Cortex-M memory-access scheduling guidance](techniques-cortex-m-memory-access-scheduling.md) for core-specific access details.