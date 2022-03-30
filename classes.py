from dataclasses import dataclass, field
from typing import Optional, List
from pydantic import BaseModel

class Coordinates(BaseModel):
    x0: Optional[float]
    y0: float
    x1: Optional[float]
    y1: float

    def update(self, y):
        return(
            self.x0,
            self.y0 + y,
            self.x1,
            self.y1 + y
            )


class Rectangle(BaseModel):
    l1: list = field(default_factory=list)

class Data(BaseModel):
    l1: list = field(default_factory=list)