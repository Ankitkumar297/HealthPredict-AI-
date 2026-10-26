from datetime import date, datetime
from math import isfinite
from typing import Annotated
from pydantic import BaseModel, ConfigDict, EmailStr, Field, BeforeValidator, field_validator


def parse_dob(value):
    if isinstance(value, date) and not isinstance(value, datetime):
        result = value
    elif isinstance(value, str):
        try:
            result = datetime.strptime(value, "%d/%m/%Y").date()
            if result.strftime("%d/%m/%Y") != value:
                raise ValueError()
        except ValueError:
            raise ValueError("Date of birth must be a real date in DD/MM/YYYY format") from None
    else:
        raise ValueError("Date of birth must be in DD/MM/YYYY format")
    if result > date.today():
        raise ValueError("Date of birth cannot be in the future")
    return result


def parse_number(value):
    if isinstance(value, bool) or value is None or (isinstance(value, str) and not value.strip()):
        raise ValueError("Enter a non-negative number")
    try:
        number = float(value)
    except (TypeError, ValueError):
        raise ValueError("Enter a valid number") from None
    if not isfinite(number) or number < 0:
        raise ValueError("Enter a finite, non-negative number")
    return number


Number = Annotated[float, BeforeValidator(parse_number)]


class PatientInput(BaseModel):
    full_name: str = Field(min_length=1, max_length=200)
    date_of_birth: Annotated[date, BeforeValidator(parse_dob)]
    email: EmailStr
    glucose: Number
    haemoglobin: Number
    cholesterol: Number

    @field_validator("full_name")
    @classmethod
    def name_not_blank(cls, value):
        value = value.strip()
        if not value:
            raise ValueError("Full name cannot be empty")
        return value


class PatientOutput(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    full_name: str
    date_of_birth: date
    email: EmailStr
    glucose: float
    haemoglobin: float
    cholesterol: float
    ai_remarks: str | None
    ai_status: str
    created_at: datetime
    updated_at: datetime


class AssessmentError(BaseModel):
    detail: str
    status: str = "failed"
