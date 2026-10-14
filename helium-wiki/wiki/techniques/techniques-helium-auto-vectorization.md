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
  - half-precision
  - floating-point
confidence: source-reported
reproducibility: snippet
related:
  - techniques-arm-compiler-mve-target-configuration
  - techniques-armv81m-feature-initialization
  - techniques-helium-low-overhead-loop-alignment
  - techniques-helium-instruction-interleaving
  - techniques-helium-matrix-kernel-layout
  - techniques-helium-vector-reductions
  - languages-arm-mve-intrinsics-and-assembly
  - languages-c-float16-half-precision
  - patterns-helium-small-kernel-fusion
  - techniques-helium-predication-and-tail-handling
sources:
  - https://support.arm.com/documentation/102095/0101/?lang=en
  - https://llvm.org/docs/Vectorizers.html
  - https://clang.llvm.org/docs/LanguageExtensions.html
  - https://clang.llvm.org/docs/LanguageExtensions.html#extensions-for-loop-hint-optimizations
  - https://developer.arm.com/community/arm-community-blogs/b/architectures-and-processors-blog/posts/armv8_2d00_m-based-processor-software-development-hints-and-tips
  - https://github.com/Arm-Examples/Helium-Optimization/blob/bc9dfb67be64a2a5ee8e5325910a3f060a593863/General_optimizations/optimizing_c_functions.md#L24-L116
  - https://github.com/Arm-Examples/Helium-Optimization/blob/bc9dfb67be64a2a5ee8e5325910a3f060a593863/Performance_analysis/ml-dsp-front-end-optimization-with-helium.md#L759-L822
  - https://github.com/Arm-Examples/Helium-Optimization/blob/bc9dfb67be64a2a5ee8e5325910a3f060a593863/Performance_analysis/ml-dsp-front-end-optimization-with-helium.md#L1019-L1227
  - https://github.com/arm-education/Arm-Helium-Technology/blob/main/HeliumTechnology_referencebook.pdf
  - https://github.com/ARM-software/CMSIS-DSP/tree/v1.18.0/Source/FilteringFunctions
  - https://github.com/ARM-software/CMSIS-DSP/blob/v1.18.0/Source/MatrixFunctions/arm_mat_vec_mult_f16.c
aliases:
  - Helium SLP loop vectorization and interleaving
  - clang loop vectorization hints
  - Helium auto-vectorization
  - MVE loop vectorization
  - armclang vectorization remarks
  - restrict and vectorization
  - MVE loop layout and data reuse
  - Helium vectorization quality inspection
  - MVE mixed-width vectorization width
  - Clang vectorize_predicate loop hint
  - MVE F16 vectorization inspection
prerequisites:
  - Compile for a target configuration that implements the intended Helium features.
  - Preserve the program's behavior when changing loop structure or pointer contracts.
---

Use these source-level checks when C or C++ loops are not being vectorized for Helium. The guide describes compiler opportunities and obstacles, not guaranteed transformations or speedups; inspect compiler remarks and preserve the original semantics when refactoring. For ordinary C/C++, use a suitable library function or compiler-generated vectors where they meet the need. Inspect output before escalating to intrinsics; hand-written assembly requires target-pipeline knowledge and may need different schedules for different processors. See [CMSIS-DSP migration guidance](../patterns/patterns-cmsis-dsp-helium-migration.md) for library selection. [Coding for Helium v1.1, §§3, 6, pp. 8–10, 16](https://support.arm.com/documentation/102095/0101/?lang=en)

The guide's 2020 Arm Compiler 6 table enables auto-vectorization by default at `-O2` and higher, including its listed `-Os`, `-Oz`, `-Ofast`, and `-Omax` levels. At `-O1`, vectorization is disabled by default but can be enabled with `-fvectorize`; `-fno-vectorize` disables it, and `-O0` ignores `-fvectorize`. Treat these as version-specific Arm Compiler settings and check the selected toolchain documentation. The guide presents `-Ofast` as a high-performance option, but it can change floating-point semantics, so use it only when the application's numerical requirements permit those changes. [Coding for Helium v1.1, §6, pp. 17–18](https://support.arm.com/documentation/102095/0101/?lang=en)

Loop vectorization widens loop instructions across multiple consecutive iterations. SLP vectorization combines similar independent scalar instructions already present in the code into vector operations. Loop interleaving is a separate transformation that can expose instruction-level parallelism across iterations. The guide discusses these transformations, but its loop-vectorization shorthand and pragma explanation oversimplify or swap them; use the distinctions in the compiler documentation. [Coding for Helium v1.1, §6, pp. 16, 20](https://support.arm.com/documentation/102095/0101/?lang=en) [LLVM Auto-Vectorization](https://llvm.org/docs/Vectorizers.html)

Request loop-vectorization success, analysis, and missed remarks with:

```text
-Rpass=loop-vectorize -Rpass-analysis=loop-vectorize -Rpass-missed=loop-vectorize
```

Use the reported reason to guide source changes. The article identifies these patterns as hard or impossible to vectorize in its context:

- Dependencies between different loop iterations.
- `break` clauses or complex conditions.
- Trip counts or termination behavior that are difficult for the compiler to analyze.
- Operations that cannot be vectorized, such as memory barriers.
- Double-precision floating-point processing for Helium; the article notes that low-overhead branch may still be used in such loops.

Where semantics allow, simplify conditions, make iteration independence visible, and arrange for the trip count to be known before entry. A known-at-entry count is a useful heuristic in the guide's Arm Compiler 6 context, not an absolute restriction across compilers or vectorization techniques. If early exit is required, isolate vectorizable work from control-dependent work or split the loop only when behavior is preserved; account for added passes and intermediate storage. Remove legacy manual loop unrolling when it prevents the compiler from recognizing a vectorization opportunity. Use `restrict` only when the pointed-to objects truly do not alias for the relevant accesses; it is a non-aliasing promise to the compiler, not a hint that can safely be added speculatively. [Coding for Helium v1.1, §6, p. 19](https://support.arm.com/documentation/102095/0101/?lang=en)

Recheck the diagnostics after each change and validate the resulting numerical behavior, especially if changing optimization level or aliasing declarations. See [techniques-arm-compiler-mve-target-configuration](techniques-arm-compiler-mve-target-configuration.md) for target feature selection.

Use successful, missed, and analysis vectorization remarks together: success identifies a transformed loop, missed remarks explain where vectorization did not occur, and analysis remarks can point to statements blocking it. Then inspect the generated hot loop for scalar work, conversions, lane movement, unsupported operations, spills, and tail handling. A success remark alone does not show that the resulting loop has an efficient instruction sequence. [Arm Helium Technology: M-Profile Vector Extension (MVE) for Cortex-M Processors, Reference Book, PDF p. 135]

For Arm Compiler 6, use `-S` to emit assembly for inspection alongside the vectorization remarks. The guide's clipping example illustrates applying the same bounds independently to successive elements, but its assembly listing conflicts with the prose about compare/predication and store width; do not treat that listing as verified output or copy it mechanically. Preserve the application's required NaN, signed-zero, and floating-point optimization behavior when changing such code. [Coding for Helium v1.1, §6, pp. 18–19](https://support.arm.com/documentation/102095/0101/?lang=en)

Do not use `restrict` or an independence pragma to conceal a real loop-carried dependency. A recurrence in which an iteration consumes a value produced by an earlier iteration must retain that ordering. A reduction is a separate case: the compiler may use partial vector accumulators and combine them later, but reordered floating-point additions can change the result. Confirm that the reduction is recognized and validate its numerical error against the application's tolerance. [Arm Helium Technology: M-Profile Vector Extension (MVE) for Cortex-M Processors, Reference Book, PDF pp. 137–138]

A small helper called from a hot loop can hide operations from the vectorizer. Where inlining preserves behavior and exposes useful work, let the compiler inline it or use a compiler-specific control only after confirming that the call boundary blocks vectorization. The book's `always_inline` suggestion is specific to its compiler context, not a universal requirement; inspect the compiler decision, code growth, and register pressure. [Arm Helium Technology: M-Profile Vector Extension (MVE) for Cortex-M Processors, Reference Book, PDF pp. 138–139]

Use `#pragma clang loop vectorize(enable)` to request loop vectorization and `#pragma clang loop interleave(enable)` to request loop interleaving. These are compiler hints: the compiler ignores a hint when the transformation is unsafe and other compiler limits can still prevent a requested transformation. A pragma cannot remove a true loop-carried dependency. The guide marks these as Arm Compiler community features, so verify availability and behavior in the selected toolchain documentation. [Clang Language Extensions, loop hint optimizations](https://clang.llvm.org/docs/LanguageExtensions.html) [LLVM Auto-Vectorization](https://llvm.org/docs/Vectorizers.html) [Coding for Helium v1.1, §6, p. 20](https://support.arm.com/documentation/102095/0101/?lang=en)

## Request a vector width that matches the mixed-width dot step

For a mixed signed 8-bit weight by signed 16-bit input loop, eight signed halfword lanes match one dot-product step. Clang and compatible armclang versions accept a loop hint such as `#pragma clang loop vectorize_width(8)`; the equivalent pragma operator spelling is `_Pragma("clang loop vectorize_width(8)")` when a macro or generated source needs it. Check the selected compiler version and its documentation for support.

The width hint requests eight loop elements per vector group. It does not select how many independent output rows to block together, and it does not request loop interleaving or unrolling; those are separate decisions. A compiler may decline a hint when legality or its implementation limits prevent the transformation. [Clang loop hint optimizations](https://clang.llvm.org/docs/LanguageExtensions.html#extensions-for-loop-hint-optimizations) [LLVM auto-vectorization](https://llvm.org/docs/Vectorizers.html)

Use vectorization remarks and emitted code to verify signed widening loads, the intended halfword reduction, bounded tail handling, and absence of unexpected spills. For a row-blocked kernel, check that one input vector is reused across independent row accumulators rather than reloaded for every row. A width hint cannot repair signed overflow, an invalid aliasing assumption, or an incorrect tail. See [Helium matrix kernel layout](techniques-helium-matrix-kernel-layout.md), [Helium vector reductions](techniques-helium-vector-reductions.md), and [MVE ACLE and assembly contracts](../languages/languages-arm-mve-intrinsics-and-assembly.md) for the arithmetic, register, and ABI contracts.

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

## Inspect F16 vectorization and test tail policy

For an F16 row-dot loop targeting MVE floating point, inspect compiler remarks and emitted code for eight-lane loads and fused multiply-accumulates, a complete horizontal reduction, bias after that reduction, and correct zero-count and tail paths. A vectorized loop can still have excess predicate setup, spills, or an unsuitable schedule; row blocking also changes live-register pressure. Compare generated code under the selected compiler and target, and preserve the numerical contract when contraction or reassociation changes.

Place this Clang loop hint immediately before the column loop as an experiment when the default vectorizer folds the remainder into a predicated vector loop:

```c
#pragma clang loop vectorize_predicate(disable)
```

Treat this as a compiler policy experiment. Current [Clang loop-hint documentation](https://clang.llvm.org/docs/LanguageExtensions.html#extensions-for-loop-hint-optimizations) describes `vectorize_predicate(enable)` as permitting tail folding; it does not establish how every compiler version interprets `disable` or what loop instruction sequence it emits. Check support in the selected Clang or armclang release, compare with its default, and inspect whether it emits a full-vector main loop with a scalar remainder. Disabling vectorizer tail folding never permits an out-of-bounds access or an omitted remainder. Keep zero-count handling, bounded loads, reduction, and final bias correct. The release-pinned [CMSIS-DSP F16 matrix-vector implementation](https://github.com/ARM-software/CMSIS-DSP/blob/v1.18.0/Source/MatrixFunctions/arm_mat_vec_mult_f16.c) is a public example to inspect, not proof that a custom loop has the same contracts.

## Keep cache locality and tiling conditional on the target

When the target has a cache and its memory path benefits from reuse, favor packed data and sequential inner-loop accesses. For a working set too large to reuse effectively, tile multidimensional loops so the active data can fit the relevant cache and be reused before eviction. Cache benefit depends on the actual memory system and working set; code or buffer relocation and interrupt activity can change residency. Profile with representative placement and interrupt conditions instead of assuming a cache always improves the workload. [Arm Helium Technology: M-Profile Vector Extension (MVE) for Cortex-M Processors, Reference Book, PDF pp. 174–175]
