from fastapi import APIRouter, HTTPException, Depends, UploadFile, File, Query
from typing import List, Optional
from models import Product, ProductCreate, ProductUpdate, CSVUploadResponse, BulkDeleteRequest, CategoryResponse
from supabase_client import supabase_request
from auth import get_current_user
from rbac import require_permission
import csv
import io
import math

router = APIRouter(prefix="/api/admin", tags=["admin"])

# Schema Headers
HEADERS_MASTER = {'Accept-Profile': 'master'}
HEADERS_MASTER_WRITE = {'Accept-Profile': 'master', 'Content-Profile': 'master', 'Prefer': 'return=representation'}


# ============ CRUD Endpoints ============

@router.get("/products", response_model=dict)
async def get_products(
    page: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1, le=2000),
    search: Optional[str] = None,
    category_id: Optional[str] = None,
    brand_id: Optional[str] = None,
    is_active: Optional[bool] = None,
    is_npl: Optional[bool] = None,
    sort_by: Optional[str] = Query('product_name'),
    sort_order: Optional[str] = Query('asc'),
    current_user: dict = Depends(get_current_user),
    _: bool = Depends(require_permission('product.manage'))
):
    """
    Get all products with pagination from master.products
    """
    # Map frontend column names to database column names if they differ
    sort_map = {
        'sku_code': 'sku_code',
        'product_name': 'product_name',
        'short_name': 'short_name',
        'parent_sku_code': 'parent_sku_code',
        'category_id': 'category_id',
        'brand_id': 'brand_id',
        'principal_id': 'principal_id',
        'price_segment': 'price_segment',
        'variant': 'variant',
        'is_active': 'is_active',
        'is_npl': 'is_npl'
    }
    
    db_sort_col = sort_map.get(sort_by, 'product_name')
    db_sort_order = 'desc' if sort_order == 'descend' or sort_order == 'desc' else 'asc'

    params = {
        'select': '*',
        'order': f'{db_sort_col}.{db_sort_order}',
        'limit': page_size,
        'offset': (page - 1) * page_size
    }
    
    # Filters
    if search:
        params['or'] = f"(product_name.ilike.*{search}*,sku_code.ilike.*{search}*)"
    if category_id:
        params['category_id'] = f"eq.{category_id}"
    if brand_id:
        params['brand_id'] = f"eq.{brand_id}"
    if is_active is not None:
        params['is_active'] = f"eq.{'true' if is_active else 'false'}"
    if is_npl is not None:
        params['is_npl'] = f"eq.{'true' if is_npl else 'false'}"

    try:
        res = supabase_request('GET', 'products', params=params, headers_extra=HEADERS_MASTER)
        data = res.get('data', [])
        total = res.get('count', len(data))
        
        return {
            "data": data,
            "total": total,
            "page": page,
            "pageSize": page_size
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/products/categories", response_model=List[CategoryResponse])
async def get_categories(
    current_user: dict = Depends(get_current_user),
    _: bool = Depends(require_permission('product.manage'))
):
    """Get all product categories from ref_categories"""
    try:
        res = supabase_request('GET', 'ref_categories', params={'order': 'name.asc'}, headers_extra=HEADERS_MASTER)
        return res.get('data', [])
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/products/principals", response_model=List[dict])
async def get_principals(
    current_user: dict = Depends(get_current_user),
    _: bool = Depends(require_permission('product.manage'))
):
    """Get all principals from ref_principals"""
    try:
        res = supabase_request('GET', 'ref_principals', params={'order': 'id.asc'}, headers_extra=HEADERS_MASTER)
        return res.get('data', [])
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/products/brands", response_model=List[dict])
async def get_brands(
    current_user: dict = Depends(get_current_user),
    _: bool = Depends(require_permission('product.manage'))
):
    """Get all brands from ref_brands"""
    try:
        res = supabase_request('GET', 'ref_brands', params={'order': 'name.asc'}, headers_extra=HEADERS_MASTER)
        return res.get('data', [])
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/products/companies", response_model=List[dict])
async def get_companies(
    current_user: dict = Depends(get_current_user),
    _: bool = Depends(require_permission('product.manage'))
):
    """Get all companies from ref_companies"""
    try:
        res = supabase_request('GET', 'ref_companies', params={'order': 'name.asc'}, headers_extra=HEADERS_MASTER)
        return res.get('data', [])
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/products/{sku_code}", response_model=Product)
async def get_product(
    sku_code: str,
    current_user: dict = Depends(get_current_user),
    _: bool = Depends(require_permission('product.manage'))
):
    """Get a single product by SKU code"""
    try:
        res = supabase_request('GET', 'products', params={'sku_code': f"eq.{sku_code}"}, headers_extra=HEADERS_MASTER)
        data = res.get('data', [])
        if not data:
            raise HTTPException(status_code=404, detail="Product not found")
        return data[0]
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/products", response_model=Product, status_code=201)
async def create_product(
    product: ProductCreate,
    current_user: dict = Depends(get_current_user),
    _: bool = Depends(require_permission('product.manage'))
):
    """Create a new product in master.products"""
    try:
        # Validate category exists
        cat_res = supabase_request('GET', 'ref_categories', params={'id': f"eq.{product.category_id}"}, headers_extra=HEADERS_MASTER)
        if not cat_res.get('data'):
            raise HTTPException(status_code=400, detail=f"Category '{product.category_id}' does not exist")
        
        # Validate parent_sku_code if provided
        if product.parent_sku_code:
            parent_res = supabase_request('GET', 'products', params={'sku_code': f"eq.{product.parent_sku_code}"}, headers_extra=HEADERS_MASTER)
            if not parent_res.get('data'):
                raise HTTPException(status_code=400, detail=f"Parent SKU '{product.parent_sku_code}' does not exist")
        
        data = product.dict()
        data['company_id'] = 'ID001'
        res = supabase_request('POST', 'products', json_data=data, headers_extra=HEADERS_MASTER_WRITE)
        return res.get('data', [])[0]
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.put("/products/{sku_code}", response_model=Product)
async def update_product(
    sku_code: str,
    product_update: ProductUpdate,
    current_user: dict = Depends(get_current_user),
    _: bool = Depends(require_permission('product.manage'))
):
    """Update an existing product"""
    try:
        # Validate category if being updated
        if product_update.category_id:
            cat_res = supabase_request('GET', 'ref_categories', params={'id': f"eq.{product_update.category_id}"}, headers_extra=HEADERS_MASTER)
            if not cat_res.get('data'):
                raise HTTPException(status_code=400, detail=f"Category '{product_update.category_id}' does not exist")
        
        # Validate parent_sku_code if being updated
        if product_update.parent_sku_code:
            if product_update.parent_sku_code == sku_code:
                raise HTTPException(status_code=400, detail="Parent SKU cannot be the same as current SKU")
            parent_res = supabase_request('GET', 'products', params={'sku_code': f"eq.{product_update.parent_sku_code}"}, headers_extra=HEADERS_MASTER)
            if not parent_res.get('data'):
                raise HTTPException(status_code=400, detail=f"Parent SKU '{product_update.parent_sku_code}' does not exist")
        
        data = product_update.dict(exclude_unset=True)
        res = supabase_request('PATCH', 'products', params={'sku_code': f"eq.{sku_code}"}, json_data=data, headers_extra=HEADERS_MASTER_WRITE)
        if not res.get('data'):
            raise HTTPException(status_code=404, detail="Product not found")
        return res.get('data', [])[0]
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/products/{sku_code}")
async def delete_product(
    sku_code: str,
    current_user: dict = Depends(get_current_user),
    _: bool = Depends(require_permission('product.manage'))
):
    """Delete a product (checks for child products first)"""
    try:
        # Check for child products
        children = supabase_request('GET', 'products', params={'parent_sku_code': f"eq.{sku_code}"}, headers_extra=HEADERS_MASTER)
        if children.get('data'):
            raise HTTPException(status_code=400, detail=f"Cannot delete: {len(children['data'])} child products depend on this SKU")
        
        supabase_request('DELETE', 'products', params={'sku_code': f"eq.{sku_code}"}, headers_extra=HEADERS_MASTER_WRITE)
        return {"message": "Product deleted successfully", "sku_code": sku_code}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/products/bulk-delete")
async def bulk_delete_products(
    request: BulkDeleteRequest,
    current_user: dict = Depends(get_current_user),
    _: bool = Depends(require_permission('product.manage'))
):
    """Delete multiple products (Note: uses ID list, not SKU codes)"""
    try:
        ids_str = ",".join([str(i) for i in request.ids])
        supabase_request('DELETE', 'products', params={'id': f"in.({ids_str})"}, headers_extra=HEADERS_MASTER_WRITE)
        return {
            "message": f"Deleted successfully",
            "requested_count": len(request.ids)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ============ CSV Upload Endpoints ============

@router.post("/products/upload-csv/validate", response_model=CSVUploadResponse)
async def validate_csv(
    file: UploadFile = File(...),
    current_user: dict = Depends(get_current_user),
    _: bool = Depends(require_permission('product.manage'))
):
    """
    Validate CSV file before importing
    Returns validation results with errors and preview
    """

    
    # Check file extension
    if not file.filename.endswith('.csv'):
        raise HTTPException(status_code=400, detail="Only CSV files are allowed")
    
    # Read file content
    content = await file.read()
    try:
        csv_content = content.decode('utf-8')
    except UnicodeDecodeError:
        raise HTTPException(status_code=400, detail="Invalid CSV encoding. Please use UTF-8")
    
    # Validate CSV
    validator = CSVValidator()
    valid_rows, errors = validator.validate_csv(csv_content)
    
    summary = validator.get_summary()
    
    return CSVUploadResponse(**summary)


@router.post("/products/upload-csv/import")
async def import_csv(
    file: UploadFile = File(...),
    skip_duplicates: bool = Query(False),
    current_user: dict = Depends(get_current_user),
    _: bool = Depends(require_permission('product.manage'))
):
    """
    Import products from validated CSV to Supabase
    """
    # Read and validate
    content = await file.read()
    csv_content = content.decode('utf-8')
    
    from csv_validator import CSVValidator
    validator = CSVValidator()
    valid_rows, _ = validator.validate_csv(csv_content)
    
    if not valid_rows:
        raise HTTPException(status_code=400, detail="No valid rows found in CSV")
    
    # Bulk Upsert to Supabase
    try:
        # Process in chunks of 50
        chunk_size = 50
        imported = 0
        for i in range(0, len(valid_rows), chunk_size):
            chunk = valid_rows[i:i + chunk_size]
            # Convert keys to match DB
            db_chunk = []
            for row in chunk:
                 db_chunk.append({
                     'product_code': row['product_code'],
                     'product_name': row['product_name'],
                     'category': row['category'],
                     'price': row['price'],
                     'stock': row['stock'],
                     'is_active': row.get('is_active', True),
                     'company_id': 'ID001'
                 })
            
            # Use POST with On Conflict if supported via headers or just POST
            # PostgREST Upsert: Prefer: resolution=merge-duplicates (header)
            headers = {**HEADERS_MASTER_WRITE, 'Prefer': 'resolution=merge-duplicates,return=minimal'}
            supabase_request('POST', 'ref_products', json_data=db_chunk, headers_extra=headers)
            imported += len(chunk)
            
        return {'message': f'Successfully imported {imported} products'}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/products/export-csv")
async def export_products_csv(
    current_user: dict = Depends(get_current_user),
    _: bool = Depends(require_permission('product.manage'))
):
    """Export all products to CSV"""
    from fastapi.responses import StreamingResponse
    
    try:
        res = supabase_request('GET', 'products', params={'order': 'product_name.asc'}, headers_extra=HEADERS_MASTER)
        products = res.get('data', [])
        
        output = io.StringIO()
        writer = csv.DictWriter(output, fieldnames=[
            'sku_code', 'product_name', 'short_name', 'parent_sku_code', 'category_id', 'brand_id', 'principal_id',
            'variant', 'price_segment',
            'uom_small', 'isi_pcs_per_small', 'uom_medium', 'isi_pcs_per_medium', 'uom_large', 'isi_pcs_per_large',
            'is_active', 'is_npl'
        ])
        writer.writeheader()
        
        for p in products:
            writer.writerow({
                'sku_code': p.get('sku_code', ''),
                'product_name': p.get('product_name', ''),
                'short_name': p.get('short_name', ''),
                'parent_sku_code': p.get('parent_sku_code', ''),
                'category_id': p.get('category_id', ''),
                'brand_id': p.get('brand_id', ''),
                'principal_id': p.get('principal_id', ''),
                'variant': p.get('variant', ''),
                'price_segment': p.get('price_segment', ''),
                'uom_small': p.get('uom_small', ''),
                'isi_pcs_per_small': p.get('isi_pcs_per_small', ''),
                'uom_medium': p.get('uom_medium', ''),
                'isi_pcs_per_medium': p.get('isi_pcs_per_medium', ''),
                'uom_large': p.get('uom_large', ''),
                'isi_pcs_per_large': p.get('isi_pcs_per_large', ''),
                'is_active': p.get('is_active', True),
                'is_npl': p.get('is_npl', False)
            })
        
        output.seek(0)
        return StreamingResponse(
            iter([output.getvalue()]),
            media_type="text/csv",
            headers={"Content-Disposition": "attachment; filename=products_export.csv"}
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/products/template-csv")
async def download_csv_template(current_user: dict = Depends(get_current_user)):
    """Download CSV template with sample data"""

    
    from fastapi.responses import StreamingResponse
    
    # Create template CSV with sample row
    output = io.StringIO()
    writer = csv.DictWriter(output, fieldnames=[
        'product_code', 'product_name', 'category', 'region', 'price', 'stock', 'is_active'
    ])
    writer.writeheader()
    writer.writerow({
        'product_code': 'SAMPLE001',
        'product_name': 'Sample Product Name',
        'category': 'Electronics',
        'region': 'A',
        'price': '1000000',
        'stock': '100',
        'is_active': 'true'
    })
    
    output.seek(0)
    
    return StreamingResponse(
        iter([output.getvalue()]),
        media_type="text/csv",
        headers={
            "Content-Disposition": "attachment; filename=products_template.csv"
        }
    )
