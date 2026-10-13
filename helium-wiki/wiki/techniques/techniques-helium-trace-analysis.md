---
id: techniques-helium-trace-analysis
title: Capture and interpret Cortex-M execution traces
type: techniques
architectures:
  - armv8.1-m
  - cortex-m52
  - cortex-m55
  - cortex-m85
tags:
  - helium
  - trace-analysis
confidence: source-reported
reproducibility: concept
related:
  - techniques-profile-guided-helium-optimization
  - techniques-helium-instruction-interleaving
  - techniques-cortex-m-data-prefetch-and-cache-hints
sources:
  - https://github.com/Arm-Examples/Helium-Optimization/blob/bc9dfb67be64a2a5ee8e5325910a3f060a593863/Performance_analysis/ml-dsp-front-end-optimization-with-helium.md#L1579-L1709
  - https://github.com/Arm-Examples/Helium-Optimization/blob/bc9dfb67be64a2a5ee8e5325910a3f060a593863/Performance_analysis/ml-dsp-front-end-optimization-with-helium.md#L1744-L1889
  - https://github.com/Arm-Examples/Helium-Optimization/blob/bc9dfb67be64a2a5ee8e5325910a3f060a593863/Performance_analysis/tools/arm_tarmac_2_chrometracing.py
  - https://github.com/Arm-Examples/Helium-Optimization/blob/bc9dfb67be64a2a5ee8e5325910a3f060a593863/Performance_analysis/tools/arm_json_merge.py
aliases:
  - TARMAC trace profiling
  - ETM trace analysis
  - Cortex-M instruction trace workflow
prerequisites:
  - Confirm that the target, simulator, probe, trace plugin, and post-processing tools support the selected trace format.
  - Keep the executable, symbol file, and trace capture from the same build.
---

Use trace analysis when the target or simulator can report instruction flow and execution events and a profile needs more detail than function-level attribution. Trace support, plugin names, timestamp sources, and post-processing formats vary by model, probe, and tool release; verify the installed toolchain's documentation before choosing a workflow.

## Capture a bounded, representative interval

Tracing an entire periodic workload can produce unwieldy output and slow simulation. Filter capture to a representative interval or delay trace start until the part of interest. The source uses the model parameter `TRACE.TarmacTrace.start-instruction-count` for delayed capture; confirm that the installed model and trace plugin expose it. Keep the workload and capture conditions stable when comparing builds, and record which executable and platform produced each trace. A trace from an FVP or AVH model can help inspect structural behavior, but the repository warns that those model timestamps are not cycle-accurate target timing.

## Match symbols and post-process consistently

Use the symbol file from the exact executable that generated the trace. Post-process with the public trace utilities appropriate to the input format, then inspect function or instruction-address attribution. Mapping PC ranges to source-level functions requires matching symbols; instruction-address bins can reveal a hot region hidden by function-level aggregation.

The [Arm Tarmac Trace Utilities](https://github.com/ARM-software/tarmac-trace-utilities/blob/main/doc/index.rst) provide call-tree, profile, and flamegraph views. The source repository also provides [arm_tarmac_2_chrometracing.py](https://github.com/Arm-Examples/Helium-Optimization/blob/bc9dfb67be64a2a5ee8e5325910a3f060a593863/Performance_analysis/tools/arm_tarmac_2_chrometracing.py) to correlate a TARMAC log with a matching symbol file and emit Trace Event JSON, and [arm_json_merge.py](https://github.com/Arm-Examples/Helium-Optimization/blob/bc9dfb67be64a2a5ee8e5325910a3f060a593863/Performance_analysis/tools/arm_json_merge.py) to align captures around selected events. Check each script's accepted input and options before converting; input formats and capture support differ. In the viewer, inspect self time as well as inclusive duration to distinguish a function's own work from its callees.

When comparing captures, align the same semantic event or workload occurrence and use a common time basis. Retain source identity for each trace and do not combine unrelated windows merely because they have similar duration. Perfetto can display trace-event JSON; the source describes the legacy Chrome trace viewer as superseded.

## Interpret timestamps and sleep carefully

Trace timestamps may be emitted only at selected PC discontinuities or loop branches rather than for every instruction. ETM capture granularity and timestamp support depend on configuration. The source also notes that timestamps can freeze while the MCU sleeps in one capture configuration; absence of CPU trace activity does not establish accelerator elapsed time. Use trace views to form structural hypotheses and confirm timing conclusions on the intended target with an appropriate measurement method.