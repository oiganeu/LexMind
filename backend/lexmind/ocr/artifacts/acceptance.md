# Acceptance Criteria -- OCR Artifact Integration

- [x] AC-1: An OcrArtifact can be created with valid fields and
  validates on construction (empty id, empty document_id, page < 1
  raise ValueError).
- [x] AC-2: OcrArtifactQuery.matches filters by document_id and
  optional page_number.
- [x] AC-3: OcrArtifactOptions.allows_overwrite reflects the
  configured flag.
- [x] AC-4: InMemoryArtifactRepository supports save/get/find/delete/
  list_all; saving a duplicate id with overwrite=False raises
  DuplicateArtifactError and with overwrite=True succeeds.
- [x] AC-5: OcrArtifactIntegrationService publishes OcrArtifactStored /
  OcrArtifactDeleted / OcrArtifactFailed events on the injected
  EventBus and delegates to the repository.
