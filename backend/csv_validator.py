"""
CSV validation module with strict validation rules
"""
import csv
import io
from typing import List, Dict, Any, Tuple
from pydantic import ValidationError
from models import ProductCreate


class CSVValidator:
    """Validator for CSV uploads with strict validation"""
    
    REQUIRED_COLUMNS = ['product_code', 'product_name', 'category', 'region', 'price', 'stock']
    OPTIONAL_COLUMNS = ['is_active']
    ALLOWED_CATEGORIES = ['Electronics', 'Clothing', 'Food', 'Furniture', 'Books']
    ALLOWED_REGIONS = ['A', 'B', 'C', 'D']
    
    def __init__(self):
        self.errors = []
        self.valid_rows = []
        self.invalid_rows = []
    
    def validate_csv(self, file_content: str) -> Tuple[List[Dict], List[Dict]]:
        """
        Validate CSV content with strict rules
        
        Returns:
            Tuple of (valid_rows, errors)
        """
        self.errors = []
        self.valid_rows = []
        self.invalid_rows = []
        
        try:
            # Parse CSV
            csv_file = io.StringIO(file_content)
            reader = csv.DictReader(csv_file)
            
            # Validate headers
            if not self._validate_headers(reader.fieldnames):
                return [], self.errors
            
            # Validate each row
            for row_num, row in enumerate(reader, start=2):  # Start at 2 (1 is header)
                self._validate_row(row, row_num)
            
            return self.valid_rows, self.errors
        
        except Exception as e:
            self.errors.append({
                'row': 0,
                'field': 'file',
                'error': f'Failed to parse CSV: {str(e)}'
            })
            return [], self.errors
    
    def _validate_headers(self, headers: List[str]) -> bool:
        """Validate CSV headers"""
        if not headers:
            self.errors.append({
                'row': 0,
                'field': 'headers',
                'error': 'CSV file is empty or has no headers'
            })
            return False
        
        # Check for required columns
        missing_columns = set(self.REQUIRED_COLUMNS) - set(headers)
        if missing_columns:
            self.errors.append({
                'row': 0,
                'field': 'headers',
                'error': f'Missing required columns: {", ".join(missing_columns)}'
            })
            return False
        
        # Check for unknown columns
        all_allowed = self.REQUIRED_COLUMNS + self.OPTIONAL_COLUMNS
        unknown_columns = set(headers) - set(all_allowed)
        if unknown_columns:
            self.errors.append({
                'row': 0,
                'field': 'headers',
                'error': f'Unknown columns: {", ".join(unknown_columns)}',
                'severity': 'warning'
            })
        
        return True
    
    def _validate_row(self, row: Dict[str, str], row_num: int):
        """Validate a single row with strict rules"""
        row_errors = []
        
        # Check for empty required fields
        for field in self.REQUIRED_COLUMNS:
            if not row.get(field, '').strip():
                row_errors.append({
                    'row': row_num,
                    'field': field,
                    'value': row.get(field),
                    'error': f'{field} is required and cannot be empty'
                })
        
        # If critical errors, skip further validation
        if row_errors:
            self.errors.extend(row_errors)
            self.invalid_rows.append({'row': row_num, 'data': row, 'errors': row_errors})
            return
        
        # Prepare data for Pydantic validation
        try:
            product_data = {
                'product_code': row['product_code'].strip(),
                'product_name': row['product_name'].strip(),
                'category': row['category'].strip(),
                'region': row['region'].strip().upper(),
                'price': float(row['price']),
                'stock': int(row['stock']),
                'is_active': row.get('is_active', 'true').lower() in ['true', '1', 'yes', 'y']
            }
            
            # Validate using Pydantic model
            ProductCreate(**product_data)
            
            # Additional business rules validation
            self._validate_business_rules(product_data, row_num, row_errors)
            
            if row_errors:
                self.errors.extend(row_errors)
                self.invalid_rows.append({'row': row_num, 'data': row, 'errors': row_errors})
            else:
                self.valid_rows.append(product_data)
        
        except ValueError as e:
            # Type conversion errors
            field = 'price' if 'price' in str(e).lower() else 'stock'
            row_errors.append({
                'row': row_num,
                'field': field,
                'value': row.get(field),
                'error': f'Invalid {field}: {str(e)}'
            })
            self.errors.extend(row_errors)
            self.invalid_rows.append({'row': row_num, 'data': row, 'errors': row_errors})
        
        except ValidationError as e:
            # Pydantic validation errors
            for error in e.errors():
                field = error['loc'][0] if error['loc'] else 'unknown'
                row_errors.append({
                    'row': row_num,
                    'field': field,
                    'value': row.get(field),
                    'error': error['msg']
                })
            
            self.errors.extend(row_errors)
            self.invalid_rows.append({'row': row_num, 'data': row, 'errors': row_errors})
    
    def _validate_business_rules(self, data: Dict, row_num: int, errors: List):
        """Additional business rules validation"""
        
        # Rule 1: Product code must be unique (checked at upload time)
        # This will be checked in the API endpoint
        
        # Rule 2: Minimum stock for active products
        if data.get('is_active', True) and data['stock'] < 10:
            errors.append({
                'row': row_num,
                'field': 'stock',
                'value': data['stock'],
                'error': 'Active products must have at least 10 units in stock',
                'severity': 'warning'
            })
        
        # Rule 3: Price range validation by category
        price_ranges = {
            'Electronics': (100000, 50000000),
            'Furniture': (50000, 20000000),
            'Clothing': (10000, 5000000),
            'Food': (1000, 1000000),
            'Books': (10000, 1000000)
        }
        
        if data['category'] in price_ranges:
            min_price, max_price = price_ranges[data['category']]
            if not (min_price <= data['price'] <= max_price):
                errors.append({
                    'row': row_num,
                    'field': 'price',
                    'value': data['price'],
                    'error': f"Price for {data['category']} should be between {min_price:,} and {max_price:,}",
                    'severity': 'warning'
                })
    
    def get_summary(self) -> Dict[str, Any]:
        """Get validation summary"""
        return {
            'total_rows': len(self.valid_rows) + len(self.invalid_rows),
            'valid_rows': len(self.valid_rows),
            'invalid_rows': len(self.invalid_rows),
            'errors': self.errors,
            'preview': self.valid_rows[:5] if self.valid_rows else []
        }
