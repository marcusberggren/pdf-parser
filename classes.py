from dataclasses import dataclass, field

@dataclass
class Coordinates:
    y0: float
    y1: float

@dataclass
class Rectangle:
    x0: float
    y0: float
    x1: float
    y1: float

    def update(self, y):
        return(
            self.x0,
            self.y0 + y,
            self.x1,
            self.y1 + y
            )

@dataclass
class Data:
    l1: list = field(default_factory=list)