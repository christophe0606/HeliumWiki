---
id: languages-arm-mve-intrinsics-and-assembly
title: Preserve ACLE, ABI and context contracts in MVE code
type: languages
architectures:
  - armv8.1-m
tags:
  - helium
  - mve
  - mve-programming-contracts
  - floating-point
  - c
  - cpp
  - asm
confidence: source-reported
reproducibility: concept
related:
  - techniques-arm-compiler-mve-target-configuration
  - techniques-helium-predication-and-tail-handling
  - techniques-helium-instruction-interleaving
  - patterns-cmsis-dsp-helium-migration
sources:
  - https://github.com/arm-education/Arm-Helium-Technology/blob/main/HeliumTechnology_referencebook.pdf
  - https://developer.arm.com/architectures/system-architectures/software-standards/acle
aliases:
  - Arm MVE ACLE intrinsics
  - Helium inline assembly contracts
  - MVE register and ABI rules
  - Helium exception context
  - arm_mve.h vector types
---

Use these rules when implementing Helium code with C/C++ intrinsics, inline assembly, or callable assembly functions. They keep scalar-reference behavior, compiler assumptions, ABI obligations, and exception continuation state aligned so that low-level optimization does not silently break callers or interrupt handling.

## Progress from a reference implementation to intrinsics

Begin with portable scalar code that can serve as a correctness reference. Profile it to find the actual bottleneck, then check whether a matching library routine or compiler auto-vectorization addresses that hotspot before writing intrinsics. Introduce intrinsics only for work that still warrants architecture-specific code, and isolate such code in separate files or functions where that helps maintenance and porting. Keep scalar control code separate when doing so makes the vector contract easier to review. [Arm Helium Technology: M-Profile Vector Extension (MVE) for Cortex-M Processors, Reference Book, PDF pp. 151–152]

## Use ACLE types and distinguish conversion from reinterpretation

Use the ACLE interfaces declared through `arm_mve.h` and the corresponding vector types to express MVE operations in C or C++. `vreinterpret` changes the compiler's type view while preserving the bits; it does not numerically convert the value. `vcvt` performs a numeric conversion and may change precision or rounding. Use the operation that matches the data contract. Compiler-specific vector operators or indexing syntax are not necessarily portable ACLE, so verify them against the selected compiler and ACLE version. [Arm Helium Technology: M-Profile Vector Extension (MVE) for Cortex-M Processors, Reference Book, PDF pp. 37, 141–142, 150]

An intrinsic is an interface, not a promise of one machine instruction. A predicated intrinsic can require predicate setup plus the operation, and an aggregate `vld4q` represents the complete sequence of VLD4 pattern instructions. Inspect generated assembly for the actual sequence, address updates, predicates, and live-register use; confirm that a source-level operation preserves the intended lane and memory behavior. [Arm Helium Technology: M-Profile Vector Extension (MVE) for Cortex-M Processors, Reference Book, PDF pp. 140–144]

## Account for shared vector and scalar register storage

The eight 128-bit Q registers alias the scalar floating-point S and D registers, so scalar FP temporaries can consume the same physical storage as live MVE vectors. Keep the number of simultaneously live vectors within the available register set and inspect compiler output for spills. Where an instruction supports a vector/scalar operand form, using a scalar general-purpose register can avoid an unnecessary vector duplicate. [Arm Helium Technology: M-Profile Vector Extension (MVE) for Cortex-M Processors, Reference Book, PDF pp. 43–44, 151]

## Make inline-assembly effects visible to the compiler

Describe every inline-assembly input and output, including read/write operands, early-clobber outputs, fixed-register requirements, condition-code changes, and memory side effects. If an instruction updates a pointer, declare that pointer as both read and written so the compiler cannot reuse its stale value. Prefer symbolic operands and compiler-selected registers when possible. Constraint codes and immediate ranges vary by toolchain and instruction; verify them against the selected compiler rather than copying unverified constraint strings. [Arm Helium Technology: M-Profile Vector Extension (MVE) for Cortex-M Processors, Reference Book, PDF pp. 152–155]

## Preserve callable-function and enclosing-function ABI obligations

Follow the selected Arm procedure-call standard and ABI variant for native assembly functions, including scalar general-purpose registers and stack alignment. The reference book summarizes Q4–Q7 as callee-preserved and Q0–Q3 as caller-saved and available for arguments or results; it also says the VPR mask fields must be zero at function boundaries while the P0 predicate bits need not be preserved. Treat that summary as an orientation, not a complete ABI specification, and verify the exact obligations for the selected toolchain and environment. [Arm Helium Technology: M-Profile Vector Extension (MVE) for Cortex-M Processors, Reference Book, PDF p. 156; Procedure Call Standard for the Arm Architecture (AAPCS32)]

Do not remove required callee saves when moving a callable kernel into a loop or combining it with a larger function. Saves may be placed around a larger enclosing region to amortize repeated entry/exit work only when the complete enclosing function still preserves every value required by its caller. Check the register liveness and all exits across that full scope. [Arm Helium Technology: M-Profile Vector Extension (MVE) for Cortex-M Processors, Reference Book, PDF pp. 156, 210]

## Preserve MVE exception context and stack capacity

MVE instructions execute in beats, so an exception can occur while vector instructions are partially complete. Preserve the architecturally defined exception continuation state when returning to interrupted code; do not treat every vector instruction as indivisible or reconstruct continuation from undocumented field assumptions. Exception context can include the shared FP/MVE register state and VPR according to the applicable frame and system policy. Context-switch and handler code must retain that state when it owns exception return. [Arm Helium Technology: M-Profile Vector Extension (MVE) for Cortex-M Processors, Reference Book, PDF pp. 43–44, 159–162]

With lazy FP/MVE context preservation, the system can reserve extended-frame space and defer saving the shared register state until an exception handler executes an FP or MVE instruction. This can avoid that state transfer when the handler does not use those features, while the first such instruction can trigger preservation. Audit latency-sensitive handlers for compiler-generated FP/MVE instructions as well as explicit intrinsics, and budget stack capacity for the applicable eager or lazy context policy. Follow the system's documented exception policy; do not assume every handler avoids FP/MVE or claim a fixed interrupt cost. [Arm Helium Technology: M-Profile Vector Extension (MVE) for Cortex-M Processors, Reference Book, PDF pp. 159–160]
