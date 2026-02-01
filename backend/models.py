"""
Data models for admin CRUD operations
"""
from pydantic import BaseModel, validator, Field
from typing import Optional, List
from datetime import datetime


# ============ Product Models (master.products) ============

class ProductBase(BaseModel):
    """Base product model for master.products table"""
    sku_code: str = Field(..., min_length=3, max_length=50, description="Unique SKU identifier")
    product_name: str = Field(..., min_length=3, max_length=255)
    short_name: Optional[str] = None
    parent_sku_code: Optional[str] = None  # FK to self for hierarchy
    parent_sku_name: Optional[str] = None  # Denormalized parent name
    principal_id: Optional[str] = None  # Principal/Division
    brand_id: str = Field(..., description="Brand identifier")
    category_id: str = Field(..., description="FK to ref_categories.id")
    variant: Optional[str] = None
    price_segment: Optional[str] = None
    
    # Unit of Measure fields
    uom_small: Optional[str] = None
    uom_medium: Optional[str] = None
    isi_pcs_per_medium: Optional[int] = Field(None, ge=0)
    uom_large: Optional[str] = None
    isi_pcs_per_large: Optional[int] = Field(None, ge=0)
    
    # Status flags
    is_active: bool = True
    is_npl: bool = False  # New Product Launch
    
    @validator('sku_code')
    def validate_sku_code(cls, v):
        if not v.replace('-', '').replace('_', '').isalnum():
            raise ValueError('SKU code must be alphanumeric (hyphens and underscores allowed)')
        return v.upper()
    
    @validator('parent_sku_code')
    def validate_parent_sku(cls, v, values):
        if v and 'sku_code' in values and v == values['sku_code']:
            raise ValueError('Parent SKU cannot be the same as SKU code')
        return v

class ProductCreate(ProductBase):
    """Model for creating a new product"""
    pass

class ProductUpdate(BaseModel):
    """Model for updating an existing product (all fields optional)"""
    product_name: Optional[str] = None
    short_name: Optional[str] = None
    parent_sku_code: Optional[str] = None
    parent_sku_name: Optional[str] = None
    principal_id: Optional[str] = None
    brand_id: Optional[str] = None
    category_id: Optional[str] = None
    variant: Optional[str] = None
    price_segment: Optional[str] = None
    uom_small: Optional[str] = None
    uom_medium: Optional[str] = None
    isi_pcs_per_medium: Optional[int] = None
    uom_large: Optional[str] = None
    isi_pcs_per_large: Optional[int] = None
    is_active: Optional[bool] = None
    is_npl: Optional[bool] = None

class Product(ProductBase):
    """Full product model with metadata"""
    id: Optional[int] = None
    company_id: str
    created_at: Optional[str] = None
    updated_at: Optional[str] = None
    
    class Config:
        from_attributes = True

class CategoryResponse(BaseModel):
    """Response model for category lookup"""
    id: str
    name: str
    company_id: str



class CSVUploadResponse(BaseModel):
    """Response model for CSV upload"""
    total_rows: int
    valid_rows: int
    invalid_rows: int
    errors: List[dict]
    preview: List[dict]


class BulkDeleteRequest(BaseModel):
    """Request model for bulk delete"""
    ids: List[int] = Field(..., min_items=1)


# ============ Role Model ============

class RefRoleBase(BaseModel):
    role_id: str = Field(..., description="Role ID (PK)")
    role_name: str
    description: Optional[str] = None

class RefRoleCreate(RefRoleBase):
    pass

class RefRoleUpdate(BaseModel):
    role_name: Optional[str] = None
    description: Optional[str] = None

class RefRole(RefRoleBase):
    created_at: Optional[datetime] = None

    class Config:
        from_attributes = True

# ============ Division Model ============
class RefDivisionBase(BaseModel):
    division_id: str = Field(..., description="Division ID (PK)")
    division_name: str
    is_active: bool = True

class RefDivisionCreate(RefDivisionBase):
    pass

class RefDivisionUpdate(BaseModel):
    division_name: Optional[str] = None
    is_active: Optional[bool] = None

class RefDivision(RefDivisionBase):
    created_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True

# ============ Region & GRBM Models (New Consistency) ============

class RefGRBMBase(BaseModel):
    grbm_code: str = Field(..., description="GRBM Code (PK)")
    name: str

class RefGRBMCreate(RefGRBMBase):
    pass

class RefGRBMUpdate(BaseModel):
    name: Optional[str] = None

class RefGRBM(RefGRBMBase):
    company_id: str
    created_at: Optional[datetime] = None
    class Config:
        from_attributes = True

class RefRegionBase(BaseModel):
    region_code: str = Field(..., description="Region Code (PK)")
    name: str
    grbm_code: Optional[str] = None

class RefRegionCreate(RefRegionBase):
    pass

class RefRegionUpdate(BaseModel):
    name: Optional[str] = None
    grbm_code: Optional[str] = None

class RefRegion(RefRegionBase):
    company_id: str
    created_at: Optional[datetime] = None
    class Config:
        from_attributes = True


# ============ Employee & User Models ============

class EmployeeBase(BaseModel):
    """Base Employee model"""
    nik: str = Field(..., min_length=3, max_length=20)
    full_name: str = Field(..., min_length=2, max_length=100)
    role_id: str = Field(..., description="Role ID from master.ref_role")
    email: Optional[str] = Field(None, pattern=r'^[\w\.-]+@[\w\.-]+\.\w+$')
    phone_number: Optional[str] = Field(None, max_length=20)
    is_active: bool = True

class EmployeeCreate(EmployeeBase):
    """Model for creating a new employee with optional user creation"""
    create_auth_user: bool = False
    password: Optional[str] = Field(None, min_length=6, description="Required if create_auth_user is True")

    @validator('password')
    def validate_password(cls, v, values):
        if values.get('create_auth_user') and not v:
            raise ValueError('Password is required when creating a system user')
        return v

class EmployeeUpdate(BaseModel):
    """Model for updating an employee"""
    full_name: Optional[str] = Field(None, min_length=3, max_length=100)
    role_id: Optional[str] = None
    email: Optional[str] = None
    phone_number: Optional[str] = None
    is_active: Optional[bool] = None
    create_auth_user: Optional[bool] = False
    password: Optional[str] = None

class Employee(EmployeeBase):
    """Full Employee model"""
    auth_user_id: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    role_name: Optional[str] = None  # For display purposes

    class Config:
        from_attributes = True


# ============ Master Data Models ============

class RefLookupBase(BaseModel):
    """Base model for Universal Lookup"""
    category: str = Field(..., description="Category code (e.g. REGION, GRBM)")
    code: str = Field(..., description="Unique code within category")
    name: str = Field(..., description="Display name")
    description: Optional[str] = None

    @validator('category')
    def validate_category(cls, v):
        return v.upper()

class RefLookupCreate(RefLookupBase):
    pass

class RefLookupUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None

class RefLookup(RefLookupBase):
    company_id: str
    created_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True


# --- Branch Models ---

class RefBranchBase(BaseModel):
    """Base model for Branch"""
    id: str = Field(..., description="Branch ID")
    name: str = Field(..., description="Branch Name")
    region_code: Optional[str] = Field(None, description="Code from RefLookup (REGION)")
    grbm_code: Optional[str] = Field(None, description="Code from RefLookup (GRBM)")
    # region_name & grbm_name can be fetched via lookup on frontend or joined.

class RefBranchCreate(RefBranchBase):
    pass

class RefBranchUpdate(BaseModel):
    name: Optional[str] = None
    region_code: Optional[str] = None
    grbm_code: Optional[str] = None

class RefBranch(RefBranchBase):
    company_id: str
    # Augmented fields (optional, populated by join if we did that, but we rely on simple select)
    region_name: Optional[str] = None 
    grbm_name: Optional[str] = None

    class Config:
        from_attributes = True



# --- Distributor Models ---

class RefDistributorBase(BaseModel):
    kd_dist: str = Field(..., description="Distributor Code (PK)")
    name: str = Field(..., description="Distributor Name") # Matches DB Column 'name'
    branch_id: Optional[str] = None # Link to Area/Branch
    parent_kd_dist: Optional[str] = None # Parent Distributor Code for Analysis

class RefDistributorCreate(RefDistributorBase):
    pass

class RefDistributorUpdate(BaseModel):
    name: Optional[str] = None
    branch_id: Optional[str] = None

class RefDistributor(RefDistributorBase):
    company_id: str
    # Augmented fields from Join
    ref_branches: Optional[dict] = Field(None, description="Joined Branch Data")
    
    class Config:
        from_attributes = True

# --- PMA Models ---

class RefPMABase(BaseModel):
    id: Optional[str] = None # Surrogate Key
    pma_code: str = Field(..., alias="pma_code") 
    pma_name: str
    distributor_id: Optional[str] = None
    kd_dist_ori: Optional[str] = None
    legacy_code: Optional[str] = None

class RefPMACreate(RefPMABase):
    pass

class RefPMAUpdate(BaseModel):
    pma_name: Optional[str] = None
    distributor_id: Optional[str] = None

class RefPMA(RefPMABase):
    company_id: str
    ref_distributors: Optional[dict] = Field(None, description="Joined Distributor Data")
    
    class Config:
        from_attributes = True

