import mimetypes
from enum import Enum
from pathlib import Path

class SourceType(str, Enum):
    RESUME_PDF = "RESUME_PDF"
    CSV = "CSV"
    UNKNOWN = "UNKNOWN"

class SourceTypeDetector:
    """Detects the type of a source file based on extension and MIME type."""
    
    @staticmethod
    def detect(file_path: Path) -> SourceType:
        if not file_path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")
            
        ext = file_path.suffix.lower()
        if ext == '.pdf':
            return SourceType.RESUME_PDF
        if ext == '.csv':
            return SourceType.CSV
            
        mime_type, _ = mimetypes.guess_type(str(file_path))
        if mime_type == 'application/pdf':
            return SourceType.RESUME_PDF
        if mime_type in ['text/csv', 'application/csv']:
            return SourceType.CSV
            
        return SourceType.UNKNOWN
