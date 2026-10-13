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