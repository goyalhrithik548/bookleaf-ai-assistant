from typing import Any, Dict

from pydantic import BaseModel, Field, model_validator


class IdentityMatchRequest(BaseModel):
    profile_1: Dict[str, Any] = Field(..., description="First identity profile")
    profile_2: Dict[str, Any] = Field(..., description="Second identity profile")

    @model_validator(mode="after")
    def validate_profiles(self):
        if not self.profile_1 or not self.profile_2:
            raise ValueError("Both profile_1 and profile_2 must be non-empty objects")

        return self
