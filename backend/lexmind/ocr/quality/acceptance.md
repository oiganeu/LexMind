# Acceptance Criteria -- OCR Quality Metrics

## AC-1: QualityMetric Validation
[x] QualityMetric rejects score outside [0,1] and negative weight.
[x] Valid QualityMetric stores name, score, weight and details.

## AC-2: OcrQualityOptions
[x] OcrQualityOptions.is_enabled returns True for all names when enabled_metrics is empty.
[x] OcrQualityOptions.is_enabled respects the enabled_metrics whitelist.
[x] OcrQualityOptions.keeps returns True when score >= threshold.

## AC-3: Rule-Based Calculators
[x] ConfidenceMetricCalculator returns 0.0 for empty text and a valid metric for non-empty text.
[x] LengthMetricCalculator scales linearly from 0.0 to 1.0 based on expected_length.
[x] WhitespaceMetricCalculator returns 1.0 for balanced whitespace and decays for excessive whitespace.

## AC-4: Registry
[x] register rejects empty names.
[x] get raises QualityCalculatorNotFoundError for unknown names.
[x] has and registered_names reflect current state.

## AC-5: Service and Plugin
[x] OcrQualityService.score emits Started/Completed events and returns a report.
[x] OcrQualityService.score emits Completed with is_low_quality flag.
[x] OcrQualityService.score emits Failed and re-raises on unexpected error.
[x] OcrQualityPlugin declares PluginCapability.OCR_QUALITY_METRICS.
[x] OcrQualityPlugin.score returns a valid OcrQualityReport.
[x] OcrQualityPlugin.register_calculator adds to the registry.
