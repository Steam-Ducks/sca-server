from enum import Enum


class OperationStatus(str, Enum):
    SUCCESS = "SUCCESS"
    FAILED = "FAILED"
    PARTIAL = "PARTIAL"


class OperationType(str, Enum):
    INGEST = "INGEST"
    TRANSFORM = "TRANSFORM"
    MERGE = "MERGE"


class LayerSchema(str, Enum):
    BRONZE = "bronze"
    SILVER = "silver"
    GOLD = "gold"
