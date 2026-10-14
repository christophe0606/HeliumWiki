---
id: techniques-helium-memory-access-layout
title: Match Helium memory accesses to vector data layout
type: techniques
architectures:
  - armv8.1-m
tags:
  - helium
  - mve
  - vector-memory-layout
  - c
  - asm
confidence: source-reported
reproducibility: concept
related:
  - techniques-helium-vector-data-alignment
  - hardware-dtcm-scatter-gather-banks
  - techniques-cortex-m-memory-access-scheduling
  - techniques-cortex-m85-memory-access-scheduling
  - techniques-helium-predication-and-tail-handling
sources:
  - https://github.com/arm-education/Arm-Helium-Technology/blob/main/HeliumTechnology_referencebook.pdf
aliases:
  - Helium contiguous and gather accesses
  - MVE gather and scatter offsets
  - Helium interleaved channel loads
  - MVE VLD2 and VLD4 layouts
  - Helium vector memory layout
---

Use this guidance when choosing MVE load and store forms for sequential, irregular, widened, or interleaved data. Match address and element semantics to the layout so gather/scatter operations do not add unnecessary accesses, narrowing does not silently change numeric meaning, and multi-pattern channel transfers preserve the intended order and bounds.

## Match the access form to the address pattern

Use contiguous vector loads and stores when consecutive lanes correspond to consecutive elements in memory. Gather and scatter support lane-dependent addresses, but one gather may require distinct memory accesses for its active elements. Do not infer contiguous-access behavior from the fact that a gather or scatter is encoded as one vector instruction. Keep core-specific timing and bank behavior separate; see [Cortex-M memory-access scheduling](techniques-cortex-m-memory-access-scheduling.md) and [TCM scatter/gather bank guidance](../hardware/hardware-dtcm-scatter-gather-banks.md). [Arm Helium Technology: M-Profile Vector Extension (MVE) for Cortex-M Processors, Reference Book, PDF pp. 105–108]

Treat gather/scatter offsets as unsigned values bounded by the selected offset-lane representation. Distinguish unscaled byte offsets from forms that scale offsets by the accessed element size; a shifted word offset, for example, is scaled by the word size. A widening byte load into wider vector lanes can provide a wider offset representation, at the cost of fewer lanes per vector. Choose a width that covers the actual nonnegative offset range and verify the exact ACLE or assembly form. Do not rely on address-space wrap to manufacture negative offsets or treat that encoding as general C pointer permission. [Arm Helium Technology: M-Profile Vector Extension (MVE) for Cortex-M Processors, Reference Book, PDF pp. 107–108]

When widening a load, choose signed or unsigned extension to match the source values and subsequent arithmetic. A narrower store writes the selected output element width; it does not by itself apply the scaling, rounding, or saturation required by a numeric conversion. Perform the required shift or conversion explicitly, and preserve the algorithm's range and rounding contract. [Arm Helium Technology: M-Profile Vector Extension (MVE) for Cortex-M Processors, Reference Book, PDF pp. 105–106]

## Keep predication and writeback semantics distinct

False-predicated load lanes become zero, while false-predicated stores leave their destination memory unchanged. Address writeback is a separate scalar effect and can still update the base even when vector lanes are inactive. Check both lane effects and pointer effects when using predicated memory operations. For remaining tail-state and bounds guidance, see [Helium lane predicates and tail handling](techniques-helium-predication-and-tail-handling.md). [Arm Helium Technology: M-Profile Vector Extension (MVE) for Cortex-M Processors, Reference Book, PDF pp. 105–108]

## Treat interleaved channel transfers as complete groups

`VLD2`/`VLD4` and `VST2`/`VST4` deinterleave or interleave patterns across two or four vector registers. A pattern instruction handles only part of the complete transfer; one `VLD2` or `VLD4` pattern is not an independent even-lane or odd-lane load. Use the complete matching pattern group for the intended stride. ACLE aggregate intrinsics such as `vld2q` and `vld4q` represent that full multi-instruction operation, not a single partial pattern. [Arm Helium Technology: M-Profile Vector Extension (MVE) for Cortex-M Processors, Reference Book, PDF pp. 112–114, 142]

For interleaved stereo or ARGB data, deinterleave only when the computation benefits from separate channel vectors, and interleave again if the output contract requires the original layout. Verify the component order and alpha placement against the caller's format. Aggregate channel loads consume a complete vector block and are not automatically safe for an incomplete final block; use a correctly bounded tail path, such as scalar cleanup or an explicitly tail-safe operation. Keep this separate from alignment and allocation requirements; see [vector data alignment](techniques-helium-vector-data-alignment.md). [Arm Helium Technology: M-Profile Vector Extension (MVE) for Cortex-M Processors, Reference Book, PDF pp. 112–114, 199–200, 202]

## Evaluate gathers used for lane permutations

In some kernels, a gather with a suitable offset vector can form a needed lane order directly from memory and avoid a sequence of scalar-register transfers for reordering. Include offset creation or loading, additional memory traffic, live-register pressure, and the target's memory-bank behavior in the decision; gather is not universally better than register rearrangement. Consult the target-specific bank guidance and verify the full kernel's memory layout before choosing the form. [Arm Helium Technology: M-Profile Vector Extension (MVE) for Cortex-M Processors, Reference Book, PDF pp. 149–150, 209–210]
