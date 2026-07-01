from pydantic import BaseModel
from typing import List

class PDFHyperlink(BaseModel):
    uri: str
    page_number: int
    bounding_box: List[float]
