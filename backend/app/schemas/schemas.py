from pydantic import BaseModel, EmailStr, Field, field_validator
from typing import Optional, Any

class RegisterIn(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)
    display_name: str = Field(default="", max_length=120)
    @field_validator("password")
    @classmethod
    def pw_strength(cls, v):
        if not any(c.isalpha() for c in v) or not any(c.isdigit() for c in v):
            raise ValueError("Password must contain a letter and a number")
        return v

class LoginIn(BaseModel):
    email: EmailStr
    password: str = Field(min_length=1, max_length=128)

class UserOut(BaseModel):
    id: str; email: str; display_name: str
    providers: list[str] = []
    github_username: str = ""
    google_connected: bool = False
    github_connected: bool = False

class CodeFileIn(BaseModel):
    path: str = Field(min_length=1, max_length=500)
    content: str

class CodeReviewIn(BaseModel):
    title: str = Field(default="Code review", max_length=300)
    language: str = Field(default="python", max_length=20)
    files: list[CodeFileIn] = Field(min_length=1)
    include_llm: bool = True

class PRReviewIn(BaseModel):
    owner: str = Field(min_length=1, max_length=100)
    repo: str = Field(min_length=1, max_length=100)
    number: int = Field(gt=0)
    include_llm: bool = True

class FindingOut(BaseModel):
    id: str; title: str; description: str; category: str; severity: str; confidence: str
    file_path: str; start_line: Optional[int]; end_line: Optional[int]; evidence: str
    explanation: str; remediation: str; suggested_patch: str; suggested_tests: list
    source: str; verification_status: str; rule_id: str
    class Config: from_attributes = True

class ReviewOut(BaseModel):
    id: str; title: str; source_type: str; language: str; status: str; source_label: str
    github_url: str; pr_number: Optional[int]; head_sha: str; summary: dict; warnings: list
    created_at: Any; finding_counts: dict = {}
    class Config: from_attributes = True

class ReviewDetailOut(ReviewOut):
    findings: list[FindingOut] = []
    files: list[dict] = []

class SettingsOut(BaseModel):
    theme: str; default_language: str; llm_enabled: bool; include_info_findings: bool
    display_name: str; email: str
    google_connected: bool; github_connected: bool; github_username: str

class SettingsPatch(BaseModel):
    theme: Optional[str] = None; default_language: Optional[str] = None
    llm_enabled: Optional[bool] = None; include_info_findings: Optional[bool] = None
    display_name: Optional[str] = Field(default=None, max_length=120)
    @field_validator("theme")
    @classmethod
    def theme_ok(cls, v):
        if v is not None and v not in ("light","dark","system"): raise ValueError("invalid theme")
        return v
