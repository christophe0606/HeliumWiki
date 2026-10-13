---
id: hardware-itcm-instruction-data-contention
title: Avoid instruction and constant-data contention in ITCM
type: hardware
architectures:
  - cortex-m55
  - cortex-m85
tags:
  - instruction-tcm
  - data-tcm
  - data-placement
  - cache
  - c
confidence: source-reported
reproducibility: concept
related:
  - patterns-cmsis-dsp-helium-migration
  - hardware-dtcm-scatter-gather-banks
  - techniques-armv8m-cache-management
sources:
  - https://developer.arm.com/community/arm-community-blogs/b/architectures-and-processors-blog/posts/armv8_2d00_m-based-processor-software-development-hints-and-tips
aliases:
  - ITCM data contention
  - ITCM coefficients
  - instruction TCM bandwidth
  - literal data placement
---

When code executes from ITCM and repeatedly reads coefficients or literals from that same ITCM, data reads compete with instruction fetches for its bandwidth. The article reports 32 bits per cycle for M55 ITCM and 64 bits per cycle for M85 ITCM; the higher M85 figure does not remove possible fetch contention.

If the code must run from ITCM, place frequently used coefficient tables in another suitable memory with linker-script placement, then verify the linked address. The article also suggests declaring tables `static` instead of `const`, but a C storage-class declaration alone does not guarantee placement in DTCM or any particular physical memory; confirm the resulting section and address in the link output.

For literal-heavy control code, consider placing literal data in DTCM or executing from AXI-connected memory with caches enabled. Code executing from AXI-connected memory does not incur this specific ITCM instruction/data contention. These are placement choices for the described access pattern, not a claim that ITCM execution is generally slower.
