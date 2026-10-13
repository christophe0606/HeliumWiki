---
id: techniques-helium-instruction-interleaving
title: Interleave different Helium instruction types to overlap execution
type: techniques
architectures:
  - cortex-m55
  - cortex-m85
tags:
  - instruction-scheduling
  - helium
  - mve
  - asm
confidence: source-reported
reproducibility: concept
related:
  - techniques-helium-auto-vectorization
  - techniques-helium-low-overhead-loop-alignment
  - hardware-dtcm-scatter-gather-banks
sources:
  - https://developer.arm.com/community/arm-community-blogs/b/architectures-and-processors-blog/posts/armv8_2d00_m-based-processor-software-development-hints-and-tips
aliases:
  - Helium instruction scheduling
  - MVE instruction interleaving
  - instruction overlap
  - assembly scheduling
---

In hand-optimized Helium assembly for M55 or M85, a run of one instruction type may leave opportunities to overlap execution unused. Interleave different types of Helium instructions in the sequence so the processor can work on their execution concurrently.

Preserve true data dependencies when changing the order, and inspect the resulting code for the target processor. The article gives this qualitative scheduling guideline only: it supplies no instruction-pair schedule, latency table, or measured speedup, so there is no universal ordering to apply mechanically.
