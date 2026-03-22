from __future__ import annotations
from datetime import datetime

from pydantic import BaseModel, EmailStr


class DnaProfileIn(BaseModel):
    shape: str | None = None
    style: list[str] = []
    palette: str | None = None
    budget: str | None = None
    mode: str | None = None


class DnaProfileOut(BaseModel):
    shape: str | None = None
    style: list[str] = []
    palette: str | None = None
    budget: str | None = None
    mode: str | None = None

    model_config = {"from_attributes": True}


class UserOut(BaseModel):
    id: str
    email: EmailStr
    name: str
    created_at: datetime
    dna_profile: DnaProfileOut | None = None

    model_config = {"from_attributes": True}

    @classmethod
    def from_orm_full(cls, u) -> "UserOut":
        dna = None
        if u.dna_profile:
            dna = DnaProfileOut(
                shape=u.dna_profile.shape,
                style=[sp.style for sp in u.dna_profile.style_preferences],
                palette=u.dna_profile.palette,
                budget=u.dna_profile.budget,
                mode=u.dna_profile.mode,
            )
        return cls(id=u.id, email=u.email, name=u.name, created_at=u.created_at, dna_profile=dna)


class UserUpdate(BaseModel):
    name: str | None = None
