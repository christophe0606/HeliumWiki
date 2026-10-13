---
id: techniques-helium-auto-vectorization
title: Use vectorization diagnostics to refactor C and C++ loops for Helium
type: techniques
architectures:
  - armv8.1-m
  - cortex-m55
  - cortex-m85
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
sources:
  - https://developer.arm.com/community/arm-community-blogs/b/architectures-and-processors-blog/posts/armv8_2d00_m-based-processor-software-development-hints-and-tips
aliases:
  - Helium auto-vectorization
  - MVE loop vectorization
  - armclang vectorization remarks
  - restrict and vectorization
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
