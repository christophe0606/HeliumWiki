---
id: techniques-helium-vector-reductions
title: Select Helium reductions and accumulator formats
type: techniques
architectures:
  - armv8.1-m
tags:
  - helium
  - mve
  - vector-reduction
  - floating-point
  - c
  - asm
confidence: source-reported
reproducibility: concept
related:
  - techniques-helium-fixed-point-arithmetic
  - techniques-helium-predication-and-tail-handling
  - languages-c-float16-half-precision
  - techniques-helium-auto-vectorization
sources:
  - https://github.com/arm-education/Arm-Helium-Technology/blob/main/HeliumTechnology_referencebook.pdf
aliases:
  - Helium integer reductions
  - MVE dot product accumulation
  - Helium vector sum and extrema
  - MVE argmax and argmin
  - MVE floating-point reduction
---

Use these reduction choices when a Helium kernel combines lane results into a scalar sum, dot product, extremum, or index. Matching the reduction form to accumulator width, initialization, signedness, tail mask, and numeric order prevents scalar overflow and incorrect results from inactive lanes or changed floating-point association.

## Reduce integer sums and products into scalar accumulators

Use architectural integer across-vector sums or dot-product instructions when their operand widths and result semantics fit the kernel. These operations place the scalar result in general-purpose registers, reducing pressure on MVE's eight vector registers. `VADDV` returns an integer across-vector sum to a scalar register; `VADDLV` provides a 64-bit result for 32-bit input lanes. For dot products, `VMLAV` produces a 32-bit scalar result and `VMLALV` provides a long result for supported 16- or 32-bit inputs. [Arm Helium Technology: M-Profile Vector Extension (MVE) for Cortex-M Processors, Reference Book, PDF pp. 59, 61, 85–86]

Choose the accumulator width from a worst-case bound on the full sum or product accumulation, including input signedness, maximum product magnitude, number of terms, scaling, and any incoming accumulator. A non-accumulating form replaces the scalar result with the reduction of the current vector operands; the `A` form adds to the existing scalar accumulator. For a multi-vector reduction, initialize the accumulator to the correct identity and use the accumulating form for subsequent groups so earlier partial sums are retained. Use a wider operation when a 32-bit result cannot hold the proven range; handle a partial final vector so invalid lanes contribute nothing. [Arm Helium Technology: M-Profile Vector Extension (MVE) for Cortex-M Processors, Reference Book, PDF pp. 61, 84–88]

For Q31 dot products, the rounding-high long form `VRMLALDAVH` has a distinct result contract: it accumulates into a 72-bit value, rounds, then returns the selected high 64 bits. Its optional scalar accumulator is shifted before being added into that wider representation. This is not an ordinary full-precision sum of products; retain the scaling and output format expected by the selected library function. [Arm Helium Technology: M-Profile Vector Extension (MVE) for Cortex-M Processors, Reference Book, PDF pp. 86–87]

## Preserve floating-point accumulation order and tail behavior

For floating-point dot products, accumulate products into lane-wise vector partial sums and then combine those lane sums in a final scalar reduction. Integer across-vector sum instructions do not provide the corresponding F16 or F32 reduction; use an explicit lane-combination sequence or a supported library helper. A pairwise F16 vector-reversal/addition tree can avoid extracting every lane individually, but it changes the order of additions. Validate the resulting rounding error against the application's tolerance; do not assume reordering leaves the final floating-point value unchanged. [Arm Helium Technology: M-Profile Vector Extension (MVE) for Cortex-M Processors, Reference Book, PDF pp. 86, 138, 146–148]

Use a predicate-aware reduction for an incomplete vector so inactive lanes do not enter the result. If a later operation reduces an intermediate vector, do not leave inactive lanes undefined and then include them in an unmasked reduction; use a supported predicate form or provide valid neutral values before reduction. Check both the arithmetic tail and any tail memory access, as described in [Helium lane predicates and tail handling](techniques-helium-predication-and-tail-handling.md). [Arm Helium Technology: M-Profile Vector Extension (MVE) for Cortex-M Processors, Reference Book, PDF pp. 145–148]

## Seed extrema and retain matching indices

Across-vector integer min/max operations compare the lane extremum with the incoming scalar value and update it only when the vector result is more extreme. Initialize with an identity that is valid for the selected signedness and operation, or seed from a valid input element. Absolute min/max variants compare absolute signed-lane magnitudes as unsigned values and treat the scalar accumulator as unsigned; do not use a signed seed contract for those forms. The book describes the floating-point number-min/max variants as following its cited IEEE 754 behavior for quiet NaNs, including returning the number when paired with a quiet NaN; confirm that behavior matches the application's required NaN contract. [Arm Helium Technology: M-Profile Vector Extension (MVE) for Cortex-M Processors, Reference Book, PDF pp. 71–73]

An argmax or argmin requires both the selected value and its matching index. Carry and update those lane vectors with the same comparison predicate, then reduce the values while preserving the selected index mapping. Define equal-value tie behavior explicitly: strict versus inclusive comparisons can select different matching indices. A final extrema reduction alone returns a value, not its index. [Arm Helium Technology: M-Profile Vector Extension (MVE) for Cortex-M Processors, Reference Book, PDF p. 191]

For a peak-bin search over a partial final vector, apply the valid-lane condition to both the value comparisons and the paired index selection, including the final selection that produces the reported bin. Invalid tail lanes must not supply either the winning value or its index. Preserve the tie rule across vector groups; a value-only maximum does not recover the index after the association has been lost. [Arm Helium Technology: M-Profile Vector Extension (MVE) for Cortex-M Processors, Reference Book, PDF p. 191]
