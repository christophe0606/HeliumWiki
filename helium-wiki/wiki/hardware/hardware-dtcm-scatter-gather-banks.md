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
  - techniques-cortex-m55-memory-access-scheduling
sources:
  - https://developer.arm.com/community/arm-community-blogs/b/architectures-and-processors-blog/posts/armv8_2d00_m-based-processor-software-development-hints-and-tips
  - https://support.arm.com/documentation/102692/0101
aliases:
  - DTCM banks
  - scatter gather memory placement
  - DTCM bank conflicts
  - data TCM throughput
  - Cortex-M55 vector-load bank conflict
  - DTCM address bits 3:2
---

Scatter/gather DSP code can benefit from DTCM when it issues separate data accesses that can reach different banks. On M55 and M85, the article describes four interleaved DTCM banks selected by address bits 2 and 3. Two separate accesses of 32 bits or less can be carried out simultaneously when they target different banks.

Arrange the accessed addresses so the concurrent accesses differ in bits [3:2]; accesses mapping to the same bank cannot use the stated overlap. This is conditional on access size and bank selection. The article contrasts this with AXI data accesses, where the D-cache lookup handles one address per cycle, but it does not claim a general twofold throughput gain for every DTCM workload or vector load.

## Cortex-M55 r1p1 vector-load conflict timing

The Cortex-M55 r1p1, Issue 03 guide states that its TCM has four banks, each 32 bits wide. For addresses requested by one vector load, equal address bits [3:2] select the same bank; those addresses cannot be loaded in the same cycle, and the guide reports a one-cycle bank-conflict penalty. This timing statement is specific to Cortex-M55 r1p1 and should not be applied as an M85 timing claim. [Arm Cortex-M55 Processor Software Optimization Guide, r1p1, Issue 03, §4.1.3, p. 47]

As an original illustration of the stated bit rule, `0x20010000` and `0x20010010` both have bits [3:2] equal to `00`, so requests for both in one vector load map to the same bank. An illustrative address such as `0x20010004` has bits [3:2] equal to `01` and selects a different bank. These are address-bit examples, not measured layouts or a guarantee that every different-bank access can proceed simultaneously under all other resource and data conditions. [§4.1.3, p. 47]

When the application's vector-load access pattern permits it, consider a data layout or stride that places concurrently requested words in different banks while preserving the program's access semantics. Verify the actual addresses and workload: the guide establishes the same-bank conflict condition and penalty, not a general throughput gain from changing layout. See [techniques-cortex-m55-memory-access-scheduling](../techniques/techniques-cortex-m55-memory-access-scheduling.md) for related memory-access timing guidance.
