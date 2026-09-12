from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field

class LoginRequest(BaseModel):
    email: str
    password: str

class RegisterRequest(BaseModel):
    full_name: str
    email: str
    password: str
    role: str = "OFFICER"
    badge_number: Optional[str] = None
    jurisdiction_zone: Optional[str] = None

class UserProfile(BaseModel):
    user_id: str
    email: str
    full_name: str
    role: str
    badge_number: Optional[str] = None
    jurisdiction_zone: Optional[str] = None

class OfficerCreateRequest(BaseModel):
    full_name: str
    email: str
    password: str
    role: str = "OFFICER"
    badge_number: Optional[str] = None
    jurisdiction_zone: Optional[str] = None

class OfficerUpdateRequest(BaseModel):
    full_name: Optional[str] = None
    role: Optional[str] = None
    badge_number: Optional[str] = None
    jurisdiction_zone: Optional[str] = None
    is_active: Optional[bool] = None

class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserProfile

class RuleModel(BaseModel):
    rule_id: str
    clause: str
    title: str
    category: str
    is_universal: bool = True
    status: str = "ACTIVE"
    mandatory: bool = True
    text: str
    source_pdf: Optional[str] = None
    source_url: Optional[str] = None

class ViolationModel(BaseModel):
    field: Optional[str] = None
    clause: Optional[str] = None
    rule_id: Optional[str] = None
    severity: str = "MAJOR"
    title: str
    description: str
    legal_citation: Optional[str] = None
    remedy: Optional[str] = None

class EntityInfoModel(BaseModel):
    manufacturer_name_address: str
    commodity_name: str
    mrp: str
    mfg_date: str
    net_quantity: str

class PenaltyInfoModel(BaseModel):
    applicable: bool
    statutory_section: str
    first_offence_str: Optional[str] = None
    second_offence_str: Optional[str] = None
    subsequent_offence_str: Optional[str] = None
    seizure_advised: bool
    recommended_action: str

class ArtifactsModel(BaseModel):
    original_image_path: str
    original_image_filename: str
    annotated_image_path: str
    annotated_image_filename: str
    annotated_image_url: str
    original_image_url: str

class InspectionResponseModel(BaseModel):
    inspection_id: Optional[str] = None
    status: str
    is_compliant: bool
    compliance_score: float
    category: str
    timestamp: str
    summary: Dict[str, Any]
    compliant_fields: List[str]
    non_compliant_fields: List[str]
    violations: List[Dict[str, Any]]
    entity_info: EntityInfoModel
    penalty_info: PenaltyInfoModel
    font_verification: Optional[Dict[str, Any]] = None
    pdp_summary: Optional[Dict[str, Any]] = None
    artifacts: ArtifactsModel
    ocr_raw: Optional[Dict[str, Any]] = None
    rule_engine_metadata: Optional[Dict[str, Any]] = None

class NoticeGenerationRequest(BaseModel):
    inspection_report: Dict[str, Any]
    notice_number: Optional[str] = None
    officer_notes: Optional[str] = None

class NoticeResponseModel(BaseModel):
    success: bool
    notice_number: str
    notice_filename: str
    notice_url: str
    file_path: str
    generated_at: str

class SamplePackageInfo(BaseModel):
    id: str
    name: str
    filename: str
    category: str
    expected_status: str
    description: str
    thumbnail_url: str

class AnalyticsOverviewResponse(BaseModel):
    total_inspections: int
    compliant_count: int
    non_compliant_count: int
    pass_rate: float
    active_officer: str
    zone: str
    top_violations: List[Dict[str, Any]]
