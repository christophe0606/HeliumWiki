---
id: techniques-helium-auto-vectorization
title: Use vectorization diagnostics to refactor C and C++ loops for Helium
type: techniques
architectures:
  - armv8.1-m
  - cortex-m55
  - cortex-m85
  - cortex-m52
tags:
  - auto-vectorization
  - helium
  - mve
  - low-overhead-branch
  - c
  - cpp
confidence: source-reported
reproducibility: snippet
related:
  - techniques-arm-compiler-mve-target-configuration
  - techniques-armv81m-feature-initialization
  - techniques-helium-low-overhead-loop-alignment
  - techniques-helium-instruction-interleaving
  - languages-c-float16-half-precision
  - patterns-helium-small-kernel-fusion
sources:
  - https://developer.arm.com/community/arm-community-blogs/b/architectures-and-processors-blog/posts/armv8_2d00_m-based-processor-software-development-hints-and-tips
  - https://github.com/Arm-Examples/Helium-Optimization/blob/bc9dfb67be64a2a5ee8e5325910a3f060a593863/General_optimizations/optimizing_c_functions.md#L24-L116
  - https://github.com/Arm-Examples/Helium-Optimization/blob/bc9dfb67be64a2a5ee8e5325910a3f060a593863/Performance_analysis/ml-dsp-front-end-optimization-with-helium.md#L759-L822
  - https://github.com/Arm-Examples/Helium-Optimization/blob/bc9dfb67be64a2a5ee8e5325910a3f060a593863/Performance_analysis/ml-dsp-front-end-optimization-with-helium.md#L1019-L1227
  - https://github.com/arm-education/Arm-Helium-Technology/blob/main/HeliumTechnology_referencebook.pdf
  - https://github.com/ARM-software/CMSIS-DSP/tree/v1.18.0/Source/FilteringFunctions
aliases:
  - Helium auto-vectorization
  - MVE loop vectorization
  - armclang vectorization remarks
  - restrict and vectorization
  - MVE loop layout and data reuse
  - Helium vectorization quality inspection
prerequisites:
  - Compile for a target configuration that implements the intended Helium features.
  - Preserve the program's behavior when changing loop structure or pointer contracts.
---

Use these source-level checks when C or C++ loops are not being vectorized for Helium. The article describes compiler opportunities and obstacles, not guaranteed transformations or speedups; inspect compiler remarks and preserve the original semantics when refactoring.

For Arm Compiler 6, the article says auto-vectorization is enabled at `-O2`, and recommends `-Ofast` for stronger performance optimization. `-Ofast` can change floating-point semantics, so use it only when the application's numerical requirements permit those changes. The article-specific optimization advice should not be read as a universal recommendation for other compilers. Arm Compiler 6 provides `-fvectorize` and `-fno-vectorize` controls. Request loop-vectorization success, analysis, and missed remarks with:

```text
-Rpass=loop-vectorize -Rpass-analysis=loop-vectorize -Rpass-missed=loop-vectorize
```

Use the reported reason to guide source changes. The article identifies these patterns as hard or impossible to vectorize in its context:

- Dependencies between different loop iterations.
- `break` clauses or complex conditions.
- Trip counts that are unknown when the loop begins.
- Operations that cannot be vectorized, such as memory barriers.
- Double-precision floating-point processing for Helium; the article notes that low-overhead branch may still be used in such loops.

Where semantics allow, simplify conditions, make iteration independence visible, and arrange for the trip count to be known before entry. Remove legacy manual loop unrolling when it prevents the compiler from recognizing a vectorization opportunity. Use `restrict` only when the pointed-to objects truly do not alias for the relevant accesses; it is a non-aliasing promise to the compiler, not a hint that can safely be added speculatively.

Recheck the diagnostics after each change and validate the resulting numerical behavior, especially if changing optimization level or aliasing declarations. See [techniques-arm-compiler-mve-target-configuration](techniques-arm-compiler-mve-target-configuration.md) for target feature selection.

Use successful, missed, and analysis vectorization remarks together: success identifies a transformed loop, missed remarks explain where vectorization did not occur, and analysis remarks can point to statements blocking it. Then inspect the generated hot loop for scalar work, conversions, lane movement, unsupported operations, spills, and tail handling. A success remark alone does not show that the resulting loop has an efficient instruction sequence. [Arm Helium Technology: M-Profile Vector Extension (MVE) for Cortex-M Processors, Reference Book, PDF p. 135]

Do not use `restrict` or an independence pragma to conceal a real loop-carried dependency. A recurrence in which an iteration consumes a value produced by an earlier iteration must retain that ordering. A reduction is a separate case: the compiler may use partial vector accumulators and combine them later, but reordered floating-point additions can change the result. Confirm that the reduction is recognized and validate its numerical error against the application's tolerance. [Arm Helium Technology: M-Profile Vector Extension (MVE) for Cortex-M Processors, Reference Book, PDF pp. 137–138]

A small helper called from a hot loop can hide operations from the vectorizer. Where inlining preserves behavior and exposes useful work, let the compiler inline it or use a compiler-specific control only after confirming that the call boundary blocks vectorization. The book's `always_inline` suggestion is specific to its compiler context, not a universal requirement; inspect the compiler decision, code growth, and register pressure. [Arm Helium Technology: M-Profile Vector Extension (MVE) for Cortex-M Processors, Reference Book, PDF pp. 138–139]

## Choose loop layout and reuse deliberately

Start by identifying which iterations are independent and can occupy vector lanes. For multidimensional data, compare loop orders and tiles so the inner loop walks contiguous elements when possible. A gather-heavy layout can still be useful when loaded values are reused across enough work; alternatively, pack a strided region once if later reuse amortizes the copy.

Make the iteration count and termination conditions visible when the behavior permits, while preserving the zero-length case and integer overflow or wrap behavior. Splitting a loop that performs several tasks can expose simpler vectorizable passes, but adds traversals and may require intermediate loads, stores, or storage. Compare that cost with fusion and operand reuse for the real working set; the appropriate layout depends on generated code and data reuse. Treat unsigned counters and count-down loops as source-specific heuristics rather than rewriting a loop without checking its termination semantics. [Arm Helium Technology: M-Profile Vector Extension (MVE) for Cortex-M Processors, Reference Book, PDF pp. 136–137]

Unroll only when it exposes independent work or reuses a loaded value. Check the generated code for increased register pressure, spills, code growth, and whether the compiler still recognizes the vector loop. MVE low-overhead loop support already reduces loop-control work, so unrolling by itself is not evidence of a better implementation. Handle incomplete vectors with predication or a correct scalar cleanup, and keep every access within the valid object bounds. A temporary contiguous copy is also safe only when its copy and storage costs are justified by reuse.

When porting a DSP kernel from another vector architecture, remap the lane organization and count simultaneously live values instead of carrying over its unrolling or radix mechanically. MVE has eight Q vector registers; a high-radix schedule can exceed that working set and spill vectors to memory. Check the compiler output and consider a library implementation or a lower-radix layout when register pressure dominates. [Arm Helium Technology: M-Profile Vector Extension (MVE) for Cortex-M Processors, Reference Book, PDF pp. 151, 156–157]

Convolution illustrates why a vectorizable multiply does not guarantee a vectorizable loop: the valid inner-loop bounds vary with each output, and the second input is traversed in the opposite direction. Before replacing it, check for a matching CMSIS-DSP convolution routine and its output and data-format contract in the selected release's [FilteringFunctions sources](https://github.com/ARM-software/CMSIS-DSP/tree/v1.18.0/Source/FilteringFunctions). For custom code, inspect the changing bounds, input order, and tail separately; do not copy the book's sample loop as a general-purpose implementation. [Arm Helium Technology: M-Profile Vector Extension (MVE) for Cortex-M Processors, Reference Book, PDF p. 193]

## Inspect vectorization quality and arithmetic contracts

Compiler vectorization remarks explain why a loop was or was not vectorized, but successful vectorization alone does not establish efficient instruction selection. Inspect the generated assembly for the hot loop and check whether conversions, predicate handling, spills, or unsupported operations still leave avoidable work. Recheck diagnostics after each source change.

For fixed-point code, preserve signedness, scaling, saturation, and rounding when exposing vectorizable idioms. For float-to-integer conversion, explicitly match the required rounding and saturating-narrowing behavior and validate boundary values. Avoid double-precision literals in an intended F32 expression if the conversion to double is unnecessary and changing it preserves the numerical contract. MVE has no vector double-precision arithmetic or native vector division. A reciprocal-based vector approximation is an option only when the application accepts its error and exceptional-value behavior; do not silently substitute it for division with different numerical semantics.

Treat source changes that alter numeric representation or evaluation as contract changes: replacing double with float, allowing floating-point reassociation, changing fused-operation or rounding behavior, or narrowing a data type all require range and error evidence. Use `restrict` only when the relevant pointers truly cannot alias. A tail predicate may disable lanes beyond the caller's valid element count, but masking away required input or output elements is not a valid optimization. Recheck the full result, including boundary lengths and numerical tolerances, after these changes. [Arm Helium Technology: M-Profile Vector Extension (MVE) for Cortex-M Processors, Reference Book, PDF pp. 53, 135–138]

## Keep cache locality and tiling conditional on the target

When the target has a cache and its memory path benefits from reuse, favor packed data and sequential inner-loop accesses. For a working set too large to reuse effectively, tile multidimensional loops so the active data can fit the relevant cache and be reused before eviction. Cache benefit depends on the actual memory system and working set; code or buffer relocation and interrupt activity can change residency. Profile with representative placement and interrupt conditions instead of assuming a cache always improves the workload. [Arm Helium Technology: M-Profile Vector Extension (MVE) for Cortex-M Processors, Reference Book, PDF pp. 174–175]
