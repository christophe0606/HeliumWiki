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

## Choose loop layout and reuse deliberately

Start by identifying which iterations are independent and can occupy vector lanes. For multidimensional data, compare loop orders and tiles so the inner loop walks contiguous elements when possible. A gather-heavy layout can still be useful when loaded values are reused across enough work; alternatively, pack a strided region once if later reuse amortizes the copy.

Unroll only when it exposes independent work or reuses a loaded value. Check the generated code for increased register pressure, spills, code growth, and whether the compiler still recognizes the vector loop. MVE low-overhead loop support already reduces loop-control work, so unrolling by itself is not evidence of a better implementation. Handle incomplete vectors with predication or a correct scalar cleanup, and keep every access within the valid object bounds. A temporary contiguous copy is also safe only when its copy and storage costs are justified by reuse.

## Inspect vectorization quality and arithmetic contracts

Compiler vectorization remarks explain why a loop was or was not vectorized, but successful vectorization alone does not establish efficient instruction selection. Inspect the generated assembly for the hot loop and check whether conversions, predicate handling, spills, or unsupported operations still leave avoidable work. Recheck diagnostics after each source change.

For fixed-point code, preserve signedness, scaling, saturation, and rounding when exposing vectorizable idioms. For float-to-integer conversion, explicitly match the required rounding and saturating-narrowing behavior and validate boundary values. Avoid double-precision literals in an intended F32 expression if the conversion to double is unnecessary and changing it preserves the numerical contract. MVE has no vector double-precision arithmetic or native vector division. A reciprocal-based vector approximation is an option only when the application accepts its error and exceptional-value behavior; do not silently substitute it for division with different numerical semantics.
