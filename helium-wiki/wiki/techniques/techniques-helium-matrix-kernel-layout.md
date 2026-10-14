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
  - techniques-helium-instruction-interleaving
  - techniques-helium-predication-and-tail-handling
  - techniques-helium-low-overhead-loop-alignment
  - techniques-cortex-m-data-prefetch-and-cache-hints
  - patterns-helium-dtcm-dma-pipeline
  - hardware-dtcm-scatter-gather-banks
  - languages-arm-mve-intrinsics-and-assembly
  - patterns-cmsis-dsp-helium-migration
sources:
  - https://github.com/arm-education/Arm-Helium-Technology/blob/main/HeliumTechnology_referencebook.pdf
  - https://github.com/ARM-software/CMSIS-DSP/tree/v1.18.0/Source/MatrixFunctions
  - https://github.com/ARM-software/CMSIS-DSP/blob/v1.18.0/Source/MatrixFunctions/arm_mat_vec_mult_q15.c
  - https://arm-software.github.io/acle/mve_intrinsics/mve.html
aliases:
  - MVE matrix row blocking
  - Helium matrix-vector row reuse
  - Helium matrix transpose layout
  - MVE 4x4 transpose VLD4
  - MVE 3x3 transpose scatter store
  - Helium s8 by s16 matrix-vector dot product
  - MVE packed matrix row-block traversal
  - Helium matrix-vector block-interleaved weights
prerequisites:
  - Confirm matrix dimensions, row/column layout, element type, numeric scaling, and source/destination overlap requirements.
  - Check the selected CMSIS-DSP release for a matching public matrix routine before maintaining a custom kernel.
---

Use this guidance when a small Helium matrix kernel is limited by repeated input loads or by a mismatch between matrix layout and vector accesses. Map the row-major storage to contiguous or structured vector operations, while preserving the kernel's accumulator, tail, and aliasing contracts.

## Map mixed signed-width matrix-vector dots to eight lanes

For a raw signed 8-bit matrix times signed 16-bit vector with signed 32-bit row outputs, preserve the contract y[r] = sum over c of sign_extend16(W[r,c]) * x[c]. This operation is matrix-vector multiplication. Keep it distinct from a quantized neural-network kernel that also applies input offsets, bias, requantization, rounding, or output saturation.

An MVE signed halfword dot step uses eight lanes: load eight s16 input values and load eight s8 weights with sign extension into s16 lanes. The step consumes 16 input bytes and 8 weight bytes, and the narrow matrix stays packed in memory instead of requiring a full expanded copy. Signed extension is required to preserve negative weights. ACLE names the 32-bit scalar dot accumulator vmladavaq_s16 (instruction VMLADAVA.S16); its long counterpart is vmlaldavaq_s16 (VMLALDAVA.S16) for a 64-bit scalar accumulator. These are horizontal dot reductions into a scalar accumulator. Bound the complete row sum and intermediate range before choosing 32-bit accumulation; use a wider accumulator when necessary, and check that the final result meets the declared output range. [Arm MVE Intrinsics Reference](https://arm-software.github.io/acle/mve_intrinsics/mve.html)

For each column block, load the input segment once, then reuse it while updating separate accumulators for a group of independent output rows. Keep the row remainder and column remainder as separate cases. For a short final column block, use bounded predicated loads plus inactive zero lanes or scalar cleanup; do not read beyond either object. Handle zero rows without touching output and, when the defined empty-column sum is used, write zero for each existing row. See [Helium lane predicates and tail handling](techniques-helium-predication-and-tail-handling.md) for predicate and loop-tail contracts.

Choose the row-group size from the live vector set, independent row accumulators, scalar pointer and loop state, and accumulator range. A larger group can improve input reuse and reduce row-pointer work, but can also increase register pressure and spills. Interleave independent loads and dot operations only when the target permits it, then inspect compiler output and the loop backedge on the selected core. Treat a schedule as target-specific; do not infer a universal unroll factor or performance result. See [Helium instruction interleaving](techniques-helium-instruction-interleaving.md), [MVE ACLE and assembly contracts](../languages/languages-arm-mve-intrinsics-and-assembly.md), and [Helium auto-vectorization](techniques-helium-auto-vectorization.md).

## Traverse packed row blocks as one weight stream

For a row group g, column block b, local row r, and lane k, define the packed weight order as P[g,b,r,k] = W[gU+r, bB+k], where B is the number of weights consumed by one dot step and k ranges from 0 to B-1. Flatten in the order g, b, r, k; with the eight-lane signed-halfword dot step above, B = 8. Thus one column block stores the eight weight bytes for row 0, then row 1, through the valid rows in the group; the next block follows those row segments. Reuse the same input segment across those row segments. A packed-weight pointer can advance through this stream instead of maintaining a separate matrix pointer for every row. If storage reserves slots for an incomplete final row group, allocate those slots explicitly and never load an invalid row.

This is row-block interleaving and traversal reordering; the logical operation remains y = W x. If the packed storage uses 16-byte weight blocks, traverse each storage block as two corresponding eight-lane dot steps; B remains the number of weights consumed by one dot step.

A linear weight stream may simplify base-pointer state and improve sequential locality, including when weights reside in DTCM; it is not only a prefetch transformation. Evaluate placement and the actual cache or TCM path, and consider a DMA-to-DTCM pipeline where the system and reuse justify it. Pack static weights offline, or amortize online packing over enough calls to cover its transform work, scratch storage, and maintained layout contract. See [Cortex-M data prefetch and cache hints](techniques-cortex-m-data-prefetch-and-cache-hints.md), [DTCM and DMA pipeline](../patterns/patterns-helium-dtcm-dma-pipeline.md), and [DTCM bank access guidance](../hardware/hardware-dtcm-scatter-gather-banks.md).

The public CMSIS-DSP [Q15 matrix-vector implementation](https://github.com/ARM-software/CMSIS-DSP/blob/v1.18.0/Source/MatrixFunctions/arm_mat_vec_mult_q15.c) illustrates reusing one input vector across independent row accumulators. Its arithmetic contract is Q15-by-Q15 with 64-bit accumulation and a shifted, saturated Q15 output, so it is a row-reuse reference only; it is not an implementation of the raw signed 8-by-16 to signed 32-bit operation described here.

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
