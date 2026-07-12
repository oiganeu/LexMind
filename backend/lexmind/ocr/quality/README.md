# OCR Quality Metrics

Scores OCR output via composable metric calculators.

## Overview

Each calculator produces a single `QualityMetric` (name, score in [0,1],
weight, details). The `OcrQualityService` runs every enabled calculator,
aggregates their weighted scores into an `OcrQualityReport` and emits
lifecycle events via an injected `EventBus`.

## Built-in Calculators

| Calculator               | Heuristic                                  |
|--------------------------|--------------------------------------------|
| `ConfidenceMetricCalculator` | Ratio of alphanumeric to non-whitespace chars |
| `LengthMetricCalculator`     | Linear scale vs expected text length       |
| `WhitespaceMetricCalculator` | Balance of whitespace vs total characters  |

All three are dependency-free and use no external models.

## Usage

```python
from lexmind.ocr.quality import OcrQualityPlugin

plugin = OcrQualityPlugin()
plugin.start()
report = plugin.score("Some OCR text here...")
print(report.overall_score, report.is_low_quality)
plugin.stop()
```

## Extending

Implement the `QualityMetricCalculator` protocol and register:

```python
plugin.register_calculator(MyCustomCalculator())
```
