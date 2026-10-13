---
id: hardware-dtcm-scatter-gather-banks
title: Place scatter and gather data across DTCM banks
type: hardware
architectures:
  - cortex-m55
  - cortex-m85
tags:
  - data-tcm
  - data-placement
  - helium
  - mve
  - cache
confidence: source-reported
reproducibility: concept
related:
  - hardware-itcm-instruction-data-contention
  - patterns-cmsis-dsp-helium-migration
  - techniques-helium-instruction-interleaving
  - techniques-armv8m-cache-management
sources:
  - https://developer.arm.com/community/arm-community-blogs/b/architectures-and-processors-blog/posts/armv8_2d00_m-based-processor-software-development-hints-and-tips
aliases:
  - DTCM banks
  - scatter gather memory placement
  - DTCM bank conflicts
  - data TCM throughput
---

Scatter/gather DSP code can benefit from DTCM when it issues separate data accesses that can reach different banks. On M55 and M85, the article describes four interleaved DTCM banks selected by address bits 2 and 3. Two separate accesses of 32 bits or less can be carried out simultaneously when they target different banks.

Arrange the accessed addresses so the concurrent accesses differ in bits [3:2]; accesses mapping to the same bank cannot use the stated overlap. This is conditional on access size and bank selection. The article contrasts this with AXI data accesses, where the D-cache lookup handles one address per cycle, but it does not claim a general twofold throughput gain for every DTCM workload or vector load.
