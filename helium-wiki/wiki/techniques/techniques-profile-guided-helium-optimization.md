---
id: techniques-profile-guided-helium-optimization
title: Profile and prioritize Helium optimization work
type: techniques
architectures:
  - armv8.1-m
  - cortex-m52
  - cortex-m55
  - cortex-m85
tags:
  - helium
  - mve
  - profile-guided-optimization
confidence: source-reported
reproducibility: concept
related:
  - techniques-helium-auto-vectorization
  - patterns-cmsis-dsp-helium-migration
  - patterns-cmsis-nn-mve-runtime-selection
  - techniques-helium-trace-analysis
sources:
  - https://github.com/Arm-Examples/Helium-Optimization/blob/bc9dfb67be64a2a5ee8e5325910a3f060a593863/Performance_analysis/ml-dsp-front-end-optimization-with-helium.md#L88-L198
  - https://github.com/Arm-Examples/Helium-Optimization/blob/bc9dfb67be64a2a5ee8e5325910a3f060a593863/Performance_analysis/ml-dsp-front-end-optimization-with-helium.md#L868-L1018
  - https://github.com/Arm-Examples/Helium-Optimization/blob/bc9dfb67be64a2a5ee8e5325910a3f060a593863/Performance_analysis/ml-dsp-front-end-optimization-with-helium.md#L1286-L1336
  - https://github.com/arm-education/Arm-Helium-Technology/blob/main/HeliumTechnology_referencebook.pdf
aliases:
  - Helium hotspot profiling workflow
  - profile DSP and NN workloads
  - isolate hot loops for compiler inspection
prerequisites:
  - Use a representative application build and workload.
  - Select an active profiler, trace source, or simulator that supports the target.
---

Use profiling to select implementation work from the application's current bottlenecks. Compare end-to-end DSP, NN, and accelerator contributions instead of assuming that an earlier hotspot list remains valid after enabling Helium, changing libraries, or offloading work to an NPU.

## Iterate from application profile to kernel change

Capture a representative workload and identify which application stages currently account for the work of interest. Prefer a low-risk library substitution or data-placement change when it addresses the hotspot. After every structural change, profile the complete application again because the relative cost of DSP frontend, NN backend, and accelerator work can shift.

Active profiling can use markers, timestamps, PMU samples, or RTOS and stream-node transitions. It may require source instrumentation or a rebuild, and instrumentation can perturb execution. Passive profiling uses supported hardware or simulator trace features, such as ETM-based tools or model trace plugins, and can reduce source changes; its availability depends on the target, probe, model, and tool version. Choose the method that can observe the relevant workload with enough context.

## Isolate a hot loop for diagnosis

Function-level reports may hide loops inlined into callers. Use line or assembly execution profiling where available. A temporary noinline boundary can make a loop easier to attribute, inspect generated code for, and unit-test in isolation. Remove diagnostic attributes from production when they are no longer needed; LTO may make different cross-file inlining decisions in the production build.

Preserve the real input ranges, boundary cases, aliasing, and numerical behavior in focused tests. Use the isolated test to understand code generation, then confirm any change with the original complete workload. The source case study's platform contributions and profiler outputs are examples for its own build, not expected results for another system.

## Keep measurement conditions representative

Measure the complete system around the real workload, not just an isolated kernel. Record the selected core/device configuration, feature enablement, memory placement and cache state, and the RTOS and interrupt behavior that will be present in the application. Caches or other implementation options may be disabled until startup configures them, so use the same setup as the intended build when comparing candidate changes. [Arm Helium Technology: M-Profile Vector Extension (MVE) for Cortex-M Processors, Reference Book, PDF pp. 165, 173–175]

Bound profiling to the interval that answers the question. Semihosted `printf` or file I/O may involve debugger services and distort a short measurement; source instrumentation also adds work. Shorter periodic sampling can provide more detail but may increase sampling overhead. Separate setup, logging, and measurement so they do not become accidental parts of the interval under study. [Arm Helium Technology: M-Profile Vector Extension (MVE) for Cortex-M Processors, Reference Book, PDF pp. 165–166, 173]

## Check PMU support and event meaning

On Armv8.1-M PMU-enabled implementations, the PMU profiling interface extends counters also exposed through legacy DWT views; they are shared physical resources, not independent counter banks. Check the selected core/device's implemented PMU features and event support, and do not try to use PMU and legacy DWT profiling interfaces concurrently as if each owned separate counters. Use the processor's technical reference and applicable architecture documentation for its event set. [Arm Helium Technology: M-Profile Vector Extension (MVE) for Cortex-M Processors, Reference Book, PDF pp. 166–170]

Separate architectural retired-work events from optional microarchitectural observations. MVE instructions-retired and MVE load/store-retired events describe executed work; cache refills and frontend, backend, or MVE dependency stalls expose implementation-specific behavior and may be optional or conditional on the implemented cache and core. Confirm event availability before using a missing event as evidence that an event did not occur. [Arm Helium Technology: M-Profile Vector Extension (MVE) for Cortex-M Processors, Reference Book, PDF pp. 170, 172]

Combine counters only when their event scopes match the question: for example, compare cache refills with the corresponding cache-access events, contiguous MVE loads with all MVE loads, or MVE memory work with the intended MVE instruction work. Check the selected counters' widths and monitor their overflow flags. Resetting a count does not necessarily clear its overflow status, so clear overflow state separately using the target's documented interface. [Arm Helium Technology: M-Profile Vector Extension (MVE) for Cortex-M Processors, Reference Book, PDF pp. 167–170, 172]
