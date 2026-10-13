---
id: patterns-cmsis-nn-mve-runtime-selection
title: Select CMSIS-NN Helium kernels through the application runtime
type: patterns
architectures:
  - cortex-m55
tags:
  - helium
  - mve
  - compiler-target-configuration
  - c
confidence: source-reported
reproducibility: concept
related:
  - techniques-arm-compiler-mve-target-configuration
  - techniques-helium-auto-vectorization
  - techniques-profile-guided-helium-optimization
sources:
  - https://github.com/Arm-Examples/Helium-Optimization/blob/bc9dfb67be64a2a5ee8e5325910a3f060a593863/General_optimizations/basic_optimization_topics.md#L80-L107
  - https://github.com/Arm-Examples/Helium-Optimization/blob/bc9dfb67be64a2a5ee8e5325910a3f060a593863/Performance_analysis/ml-dsp-front-end-optimization-with-helium.md#L296-L352
  - https://github.com/Arm-Examples/Helium-Optimization/blob/bc9dfb67be64a2a5ee8e5325910a3f060a593863/Performance_analysis/ml-dsp-front-end-optimization-with-helium.md#L519-L544
aliases:
  - CMSIS-NN MVE runtime integration
  - TFLM CMSIS-NN optimized kernels
prerequisites:
  - Build the runtime and CMSIS-NN for the processor's implemented MVE and floating-point features.
  - Confirm that the runtime version supports the operators and kernel path required by the model.
---

Use this pattern when an ML application runs through a runtime such as TensorFlow Lite Micro and should select optimized CMSIS-NN kernels for a Helium-capable target. The repository describes runtime integration as the normal path for NN operators; it does not imply that every custom DSP or frontend loop becomes vectorized when the library is enabled.

Build the runtime and CMSIS-NN with a target configuration that matches the fitted processor and the enabled MVE/FPU features. Review the runtime's operator resolver and library release to confirm that the model's required operators have an optimized implementation. The source gives TFLM's OPTIMIZED_KERNEL_DIR=cmsis_nn setting as an example; check the selected runtime version's build instructions before using that spelling as a build option.

After enabling the optimized kernel path, inspect the build configuration or generated call path to confirm that the runtime selected the intended implementation. Profile the full application again: library selection can change which custom frontend or post-processing loops are now worth optimizing. Keep those loops subject to compiler vectorization diagnostics and numerical validation.