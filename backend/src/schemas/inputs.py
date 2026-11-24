from typing import Annotated, Literal

from pydantic import BaseModel, ConfigDict, Field, StringConstraints, field_validator, model_validator


class Input(BaseModel):
    model_config = ConfigDict(extra='forbid', str_strip_whitespace=True, allow_inf_nan=False)


CrewCode = Annotated[str, StringConstraints(pattern=r'^G[0-9]{2}$')]
OrderCode = Annotated[str, StringConstraints(pattern=r'^[A-Z][A-Z0-9-]{2,19}$')]


class Intake(Input):
    minutes: float = Field(ge=0.01, le=180)
    shots: int = Field(ge=1, le=1000)
    switches: int = Field(ge=0, le=1000)

    @model_validator(mode='after')
    def validate_switches(self):
        if self.switches >= self.shots:
            raise ValueError('背景切换次数必须小于镜头数')
        return self


class OrderDetails(Intake):
    title: str = Field(min_length=1, max_length=90)
    crew: CrewCode
    hours: float = Field(ge=0, le=200)


class OrderInput(OrderDetails):
    code: OrderCode


class PlanInput(Input):
    name: str = Field(min_length=1, max_length=64)
    alpha: float = Field(ge=0.001, le=100)
    features: list[Literal['minutes', 'shots', 'switches']] = Field(min_length=1, max_length=3)

    @field_validator('features')
    @classmethod
    def unique_features(cls, value):
        if len(set(value)) != len(value):
            raise ValueError('版本内的特征不能重复')
        return value


class RunInput(Input):
    plan_id: int = Field(gt=0, le=9223372036854775807)
    holdout: CrewCode


class LoginInput(Input):
    email: str = Field(min_length=3, max_length=100)
    password: str = Field(min_length=1, max_length=128)
