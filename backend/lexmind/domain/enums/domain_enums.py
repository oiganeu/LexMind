"""Domain enumerations for LexMind.

Every enumeration models a closed set of business states or categories.
"""

from enum import Enum, unique


@unique
class DocumentStatus(Enum):
    """Lifecycle status of a document within the platform."""

    DRAFT = "draft"
    PENDING_IMPORT = "pending_import"
    IMPORTING = "importing"
    IMPORTED = "imported"
    PROCESSING = "processing"
    PROCESSED = "processed"
    FAILED = "failed"
    ARCHIVED = "archived"
    DELETED = "deleted"


@unique
class DocumentTypeEnum(Enum):
    """Classification of document types in the legal domain."""

    CONTRACT = "contract"
    CORRESPONDENCE = "correspondence"
    COURT_FILING = "court_filing"
    EVIDENCE = "evidence"
    LEGAL_BRIEF = "legal_brief"
    JUDGMENT = "judgment"
    STATUTE = "statute"
    REGULATION = "regulation"
    MEMO = "memo"
    REPORT = "report"
    PHOTOGRAPH = "photograph"
    AUDIO = "audio"
    VIDEO = "video"
    OTHER = "other"


@unique
class EvidenceType(Enum):
    """Types of evidence admitted in legal proceedings."""

    DOCUMENTARY = "documentary"
    TESTIMONIAL = "testimonial"
    REAL = "real"
    DEMONSTRATIVE = "demonstrative"
    DIGITAL = "digital"
    FORENSIC = "forensic"
    EXPERT = "expert"
    CIRCUMSTANTIAL = "circumstantial"


@unique
class PersonRole(Enum):
    """Roles a person can assume in a legal context."""

    CLIENT = "client"
    ATTORNEY = "attorney"
    WITNESS = "witness"
    EXPERT = "expert"
    JUDGE = "judge"
    PROSECUTOR = "prosecutor"
    DEFENDANT = "defendant"
    PLAINTIFF = "plaintiff"
    VICTIM = "victim"
    WITNESS_FOR = "witness_for"
    WITNESS_AGAINST = "witness_against"
    THIRD_PARTY = "third_party"


@unique
class RelationshipType(Enum):
    """Types of relationships between entities."""

    EMPLOYMENT = "employment"
    OWNERSHIP = "ownership"
    FAMILY = "family"
    CONTRACTUAL = "contractual"
    AGENCY = "agency"
    PARTNERSHIP = "partnership"
    SUBSIDIARY = "subsidiary"
    CITATION = "citation"
    REFERENCE = "reference"
    CONTRADICTION = "contradiction"
    SUPPORT = "support"
    TEMPORAL = "temporal"
    CAUSAL = "causal"


@unique
class StatementType(Enum):
    """Classification of statements in legal proceedings."""

    TESTIMONY = "testimony"
    DEPOSITION = "deposition"
    AFFIDAVIT = "affidavit"
    DECLARATION = "declaration"
    CONFESSION = "confession"
    DENIAL = "denial"
    EXPERT_OPINION = "expert_opinion"
    HEARSAY = "hearsay"
    ADMISSIBLE = "admissible"
    INADMISSIBLE = "inadmissible"


@unique
class MeetingType(Enum):
    """Types of meetings in legal practice."""

    CLIENT_INTAKE = "client_intake"
    STRATEGY = "strategy"
    DEPOSITION = "deposition"
    MEDIATION = "mediation"
    HEARING = "hearing"
    TRIAL = "trial"
    SETTLEMENT = "settlement"
    CONFERENCE = "conference"
    CONSULTATION = "consultation"


@unique
class ImportStatus(Enum):
    """Status of a document import job."""

    PENDING = "pending"
    DISCOVERING = "discovering"
    VALIDATING = "validating"
    IMPORTING = "importing"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


@unique
class ProcessingStatus(Enum):
    """Status of document processing through the pipeline."""

    PENDING = "pending"
    VALIDATING = "validating"
    EXTRACTING_METADATA = "extracting_metadata"
    OCR = "ocr"
    LANGUAGE_DETECTION = "language_detection"
    CLASSIFYING = "classifying"
    PARSING = "parsing"
    ENTITY_EXTRACTION = "entity_extraction"
    CHUNKING = "chunking"
    EMBEDDING = "embedding"
    INDEXING = "indexing"
    KNOWLEDGE_GRAPH = "knowledge_graph"
    TIMELINE = "timeline"
    CONTRADICTION_CHECK = "contradiction_check"
    SEARCH_REGISTRATION = "search_registration"
    COMPLETED = "completed"
    FAILED = "failed"


@unique
class CaseStatus(Enum):
    """Lifecycle status of a legal case."""

    OPEN = "open"
    ACTIVE = "active"
    PENDING_REVIEW = "pending_review"
    SETTLED = "settled"
    CLOSED = "closed"
    ARCHIVED = "archived"
    REOPENED = "reopened"


@unique
class RiskLevel(Enum):
    """Risk classification levels."""

    NONE = "none"
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


@unique
class ConfidenceLevel(Enum):
    """Confidence levels for AI and analysis results."""

    VERY_LOW = "very_low"
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    VERY_HIGH = "very_high"


@unique
class Country(Enum):
    """ISO 3166-1 alpha-2 country codes (subset)."""

    RO = "Romania"
    DE = "Germany"
    FR = "France"
    IT = "Italy"
    ES = "Spain"
    PL = "Poland"
    NL = "Netherlands"
    BE = "Belgium"
    AT = "Austria"
    CZ = "Czech Republic"
    HU = "Hungary"
    BG = "Bulgaria"
    HR = "Croatia"
    GR = "Greece"
    PT = "Portugal"
    SE = "Sweden"
    DK = "Denmark"
    FI = "Finland"
    IE = "Ireland"
    CY = "Cyprus"
    LV = "Latvia"
    LT = "Lithuania"
    EE = "Estonia"
    SK = "Slovakia"
    SI = "Slovenia"
    LU = "Luxembourg"
    MT = "Malta"
    US = "United States"
    GB = "United Kingdom"
    CH = "Switzerland"
    NO = "Norway"
    OTHER = "Other"


@unique
class CourtLevel(Enum):
    """Hierarchy of courts in the legal system."""

    FIRST_INSTANCE = "first_instance"
    APPELLATE = "appellate"
    SUPREME = "supreme"
    CONSTITUTIONAL = "constitutional"
    ADMINISTRATIVE = "administrative"
    EUROPEAN_COURT = "european_court"
    INTERNATIONAL = "international"
