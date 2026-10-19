# Prespecified paired representation extension

Recorded before any new structural-stress model outcome, after the existing
five-source context selection and frozen X descriptors. The ordinary raw
reference campaign is unchanged. Every one of the five prospectively selected
stress tasks receives both raw and SNV; no source/target is selected by an
observed favorable score. This is exploratory confrontation, not untouched
confirmation, and H1-H5 definitions remain unchanged.

Run the identical full-reference, exact-size-control and context-excluded
training populations on the identical evaluation IDs. Use the same fixed PLS
components and Ridge alpha=1. Native Methods SNV(with_mean=true,with_std=true,
ddof=0) acts per spectrum and learns no population mean or variance; the
previously qualified row-isolation protocol applies. Diagnostic PCA fits only
each training population, then transforms evaluation without refitting.

Freeze and compare private population fingerprints across representations.
Compute I_RMSE = D_RMSE_SNV - D_RMSE_raw and
I_skill = D_skill_SNV - D_skill_raw, with the same matched-control null
denominator. These scalar contrasts reuse native scores. Neither a large nor
a small raw/SNV descriptor change guarantees an interaction: retain zero,
opposite and model-specific responses. Five tasks, related populations, limited
support diagnostics and unknown assay dependencies cannot validate an independent
study-level prediction rule. Fixed raw/SNV Ridge also changes effective
regularization relative to feature intensity units; this is a pipeline contrast.

Additional bound: five existing tasks, 30 model fits, 15 train-only one-component
PCAs and five per-spectrum SNV calls; 5,242,880 reserved bytes (1 MiB per task).
Total paired stress uses ten representation-task executions, 60 model fits and
30 diagnostic PCAs, below the original bank-stage ceiling of 24 deeper tasks /
144 model fits. No new sources, targets, hyperparameter search or acquisition.
The extra 5 MiB remains inside the existing reservation ceiling of 1,805,306,368
and combined-storage ceiling of 20,289,597,121 bytes. **No ceiling increase.**
Serial execution, 2 GiB RAM, cumulative eight-hour worker bound, task/evidence
caps, source permissions and historical retained memberships remain unchanged.
