# Mermaid Examples

Example diagrams demonstrating the supported Mermaid rendering.

## Flowchart

```mermaid
flowchart TD
    A[Document] --> B[OCR]
    B --> C[Parse]
    C --> D[Chunk]
    D --> E[Embed]
    E --> F[Index]
```

## Sequence Diagram

```mermaid
sequenceDiagram
    participant U as User
    participant A as API
    participant R as Retriever
    U->>A: Query
    A->>R: Search
    R-->>A: Results
    A-->>U: Context
```

## Entity Relationship Diagram

```mermaid
erDiagram
    DOCUMENT ||--o{ CHUNK : contains
    CHUNK ||--o{ EMBEDDING : has
    ENTITY ||--o{ MENTION : extracted_from
```

## State Diagram

```mermaid
stateDiagram-v2
    [*] --> Ingestion
    Ingestion --> Processing
    Processing --> Indexed
    Indexed --> [*]
```

## Class Diagram

```mermaid
classDiagram
    class Plugin {
        +load()
        +configure()
    }
    class Workspace {
        +documents
        +index
    }
```

## Timeline

```mermaid
timeline
    title Case Timeline
    2021 : Filing
    2022 : Hearing
    2023 : Judgment
```
