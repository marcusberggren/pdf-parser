from typing import Optional, List
from pydantic import BaseModel, Field

class Coordinates(BaseModel):
    x0: float
    y0: float = 0
    x1: float
    y1: float = 0
    
    def update(self, y0, y1):
        return(
            self.x0,
            self.y0 + y0[1],
            self.x1,
            self.y1 + y1[3]
            )

class Rectangle(BaseModel):
    t1: tuple

class Data(BaseModel):

    def if_Same_row():


        pass