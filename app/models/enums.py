from enum import IntEnum

class MeasurementEnum(IntEnum):
    GRAMS = 1
    PIECES = 2 
    MILLILITERS = 3

    @property
    def label(self) -> str:
        return {
            MeasurementEnum.GRAMS: "г",
            MeasurementEnum.PIECES: "шт", 
            MeasurementEnum.MILLILITERS: "мл",
        }[self]