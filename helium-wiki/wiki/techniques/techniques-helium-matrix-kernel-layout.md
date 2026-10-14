---
id: techniques-helium-matrix-kernel-layout
title: Reuse operands and map matrix layouts to Helium accesses
type: techniques
architectures:
  - armv8.1-m
tags:
  - helium
  - mve
  - matrix-kernel-layout
  - c
  - asm
confidence: source-reported
reproducibility: concept
related:
  - techniques-helium-memory-access-layout
  - techniques-helium-vector-reductions
  - techniques-helium-auto-vectorization
  - patterns-cmsis-dsp-helium-migration
sources:
  - https://github.com/arm-education/Arm-Helium-Technology/blob/main/HeliumTechnology_referencebook.pdf
  - https://github.com/ARM-software/CMSIS-DSP/tree/v1.18.0/Source/MatrixFunctions
aliases:
  - MVE matrix row blocking
  - Helium matrix-vector row reuse
  - Helium matrix transpose layout
  - MVE 4x4 transpose VLD4
  - MVE 3x3 transpose scatter store
prerequisites:
  - Confirm matrix dimensions, row/column layout, element type, numeric scaling, and source/destination overlap requirements.
  - Check the selected CMSIS-DSP release for a matching public matrix routine before maintaining a custom kernel.
---

Use this guidance when a small Helium matrix kernel is limited by repeated input loads or by a mismatch between matrix layout and vector accesses. Map the row-major storage to contiguous or structured vector operations, while preserving the kernel's accumulator, tail, and aliasing contracts.

## Reuse vector inputs across independent rows

For an integer matrix-vector kernel with a matching scalar-result reduction, load a vector segment once and apply it to several independent matrix rows, keeping a separate scalar accumulator for each output row. This reuses the same input data across row calculations, but the number of rows processed together is a register and numeric-range decision: account for live matrix vectors, shared input vectors, accumulator width and bounds, and the actual memory path. Handle a row count that does not fill a complete row block and a column count that does not fill a vector separately. The book's four-row example illustrates reuse; it does not establish a universally optimal row blocking factor. [Arm Helium Technology: M-Profile Vector Extension (MVE) for Cortex-M Processors, Reference Book, PDF pp. 183–185]

For a quantized NN matrix kernel, reuse each loaded input vector across independent output-row dot products and interleave independent matrix loads and multiply-accumulates when the selected target permits it. Keep row accumulators within the chosen kernel's width and range, and preserve its input offsets, bias handling, row and column tails, and final output scaling. The book's load/MAC schedule is an implementation example; confirm dependencies and generated code on the target rather than assuming a universal schedule. [Arm Helium Technology: M-Profile Vector Extension (MVE) for Cortex-M Processors, Reference Book, PDF p. 221]

Floating-point row blocks also need independent accumulators for each output. Lane-wise partial sums require a final reduction, and changing their association must fit the numerical contract; see [Helium vector reductions](techniques-helium-vector-reductions.md).

## Preserve contiguous traversal or amortize packing

Keep the innermost traversal over contiguous row elements where the layout permits it. In matrix-matrix work, one operand may otherwise be visited by columns with a strided access pattern; consider tiling or packing that operand into a more contiguous working layout only when later reuse justifies the extra copy, storage, and setup. The useful tile depends on the memory hierarchy and active working set, so compare the complete access pattern rather than assuming a packed copy is always beneficial. [Arm Helium Technology: M-Profile Vector Extension (MVE) for Cortex-M Processors, Reference Book, PDF p. 175]

For convolution, HWC can make each pixel's channel values contiguous for a particular patch-generation and load pattern. Match the layout and any weight reordering to the selected operator's exact dimension and stride contract; do not impose HWC on unrelated NN operators. [Arm Helium Technology: M-Profile Vector Extension (MVE) for Cortex-M Processors, Reference Book, PDF pp. 221, 227–228]

When a full convolution im2col expansion would exceed the scratch budget, expand a small reusable group of patches and interleave patch generation with matrix computation. Choose the group size from scratch demand, input reuse, and the selected matrix kernel's contract. The book's two-column grouping is one historical example, not a universal block size. [Arm Helium Technology: M-Profile Vector Extension (MVE) for Cortex-M Processors, Reference Book, PDF pp. 220–221]

## Map complete fixed-size transpose blocks to vector memory operations

For a complete row-major 4×4 block of 32-bit elements, a VLD4 deinterleave can place each original matrix column into a vector; four contiguous vector stores then write those columns as rows of the transposed output. Treat an aggregate ACLE VLD4 intrinsic as the complete four-pattern transfer it represents, not as one isolated pattern instruction. Use this form only when the full block is valid and the source, destination, and output stride match the intended layout; arrange a separate bounded path for incomplete blocks. [Arm Helium Technology: M-Profile Vector Extension (MVE) for Cortex-M Processors, Reference Book, PDF pp. 185–186]

For a row-major 3×3 matrix of 32-bit elements, two contiguous four-element loads cover the first eight values; scatter stores can place them at their transposed output positions, with the ninth value handled separately. Confirm whether the chosen scatter form interprets offsets as byte offsets or scaled element offsets, and keep offsets within the intended destination object. This describes an out-of-place mapping; it does not by itself make overlapping input and output safe. [Arm Helium Technology: M-Profile Vector Extension (MVE) for Cortex-M Processors, Reference Book, PDF p. 186]

## Select fixed-size routines by their complete contract

Small fixed-dimension routines can use a different implementation from a generic matrix loop. Before selecting a library specialization or writing a dedicated kernel, match the exact dimensions and layout, element type and signedness, accumulator range, fixed-point scaling and final saturation or rounding, and any row or column remainder handling. Check the selected public CMSIS-DSP release for the function and its documented input/output overlap requirements; do not infer a current library contract from a historical example. [Arm Helium Technology: M-Profile Vector Extension (MVE) for Cortex-M Processors, Reference Book, PDF pp. 185–186; CMSIS-DSP v1.18.0 MatrixFunctions]

## Protect unread values when buffers overlap

The transpose layouts above assume distinct source and destination storage. For an in-place transpose or any overlapping buffers, preserve every input value until it has been read. Prove that the selected load/store order does not overwrite an unread element, or stage the complete affected tile in temporary storage; do not infer arbitrary in-place safety from an out-of-place gather/scatter or VLD4 example. [Arm Helium Technology: M-Profile Vector Extension (MVE) for Cortex-M Processors, Reference Book, PDF pp. 185–186]
