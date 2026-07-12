# OCR Artifact Integration

Associate OCR output with document artifacts such as pages, images and
regions.  The integration framework provides:

- **artifact_types** -- domain value objects (`OcrArtifact`,
  `OcrArtifactQuery`, `OcrArtifactOptions`).
- **artifact_repository** -- persistence protocol and in-memory
  implementation with a named-registry for multiple backends.
- **ocr_artifact_integration** -- service layer that orchestrates
  store/get/find/delete/list_all and publishes lifecycle events.
- **ocr_artifact_plugin** -- plugin wrapper exposing the service
  through the standard plugin interface.
