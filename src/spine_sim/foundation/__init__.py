"""Public M00 foundation API; deliberately independent of future physical modules."""

from .canonical import semantic_hash, source_file_hash, stable_content_id, uuid7
from .config import ConfigSchema, ResolvedConfig, load_strict_document, resolve_config
from .integrity import VerifyMode, verify_bundle
from .plot_requirements import PlotDataGapRequest, PlotDataRequirements
from .reader import (
    ChunkedArrayView,
    DatasetCatalog,
    FilterSpec,
    JoinSpec,
    OrderSpec,
    QueryResult,
    ResultReader,
)
from .registry import FieldMetadata, ResultExtensionDescriptor, SchemaRegistry
from .writer import ResultWriter

__all__ = [
    "ChunkedArrayView",
    "ConfigSchema",
    "DatasetCatalog",
    "FieldMetadata",
    "FilterSpec",
    "JoinSpec",
    "OrderSpec",
    "PlotDataGapRequest",
    "PlotDataRequirements",
    "QueryResult",
    "ResolvedConfig",
    "ResultExtensionDescriptor",
    "ResultReader",
    "ResultWriter",
    "SchemaRegistry",
    "VerifyMode",
    "load_strict_document",
    "resolve_config",
    "semantic_hash",
    "source_file_hash",
    "stable_content_id",
    "uuid7",
    "verify_bundle",
]
