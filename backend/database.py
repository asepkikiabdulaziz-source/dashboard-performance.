"""
In-memory database for demo
In production, replace with real database (PostgreSQL, MySQL, etc.)
"""
from datetime import datetime
from typing import List, Optional, Dict, Any
import json


class InMemoryDB:
    """Simple in-memory database for demo purposes"""
    
    def __init__(self):
        self.products = []
        self.next_id = 1
        self._initialize_sample_data()
    
    def _initialize_sample_data(self):
        """Initialize with sample data"""
        sample_products = [
            {
                'product_code': 'PROD001',
                'product_name': 'Laptop Dell XPS',
                'category': 'Electronics',
                'region': 'A',
                'price': 15000000,
                'stock': 50,
                'is_active': True
            },
            {
                'product_code': 'PROD002',
                'product_name': 'Office Chair Premium',
                'category': 'Furniture',
                'region': 'B',
                'price': 2500000,
                'stock': 100,
                'is_active': True
            },
            {
                'product_code': 'PROD003',
                'product_name': 'T-Shirt Cotton',
                'category': 'Clothing',
                'region': 'C',
                'price': 150000,
                'stock': 500,
                'is_active': True
            },
            {
                'product_code': 'PROD004',
                'product_name': 'Python Programming Book',
                'category': 'Books',
                'region': 'A',
                'price': 250000,
                'stock': 200,
                'is_active': True
            },
            {
                'product_code': 'PROD005',
                'product_name': 'Organic Rice 5kg',
                'category': 'Food',
                'region': 'D',
                'price': 75000,
                'stock': 1000,
                'is_active': True
            }
        ]
        
        for product in sample_products:
            self.create_product(product)
    
    def get_all_products(self, skip: int = 0, limit: int = 100) -> List[Dict[str, Any]]:
        """Get all products with pagination"""
        return self.products[skip:skip + limit]
    
    def get_product_by_id(self, product_id: int) -> Optional[Dict[str, Any]]:
        """Get product by ID"""
        for product in self.products:
            if product['id'] == product_id:
                return product
        return None
    
    def get_product_by_code(self, product_code: str) -> Optional[Dict[str, Any]]:
        """Get product by code"""
        for product in self.products:
            if product['product_code'] == product_code:
                return product
        return None
    
    def create_product(self, product_data: dict) -> Dict[str, Any]:
        """Create a new product"""
        now = datetime.now().isoformat()
        product = {
            'id': self.next_id,
            **product_data,
            'created_at': now,
            'updated_at': now
        }
        self.products.append(product)
        self.next_id += 1
        return product
    
    def update_product(self, product_id: int, update_data: dict) -> Optional[Dict[str, Any]]:
        """Update an existing product"""
        for i, product in enumerate(self.products):
            if product['id'] == product_id:
                # Update only provided fields
                for key, value in update_data.items():
                    if value is not None:
                        product[key] = value
                
                product['updated_at'] = datetime.now().isoformat()
                self.products[i] = product
                return product
        return None
    
    def delete_product(self, product_id: int) -> bool:
        """Delete a product"""
        for i, product in enumerate(self.products):
            if product['id'] == product_id:
                self.products.pop(i)
                return True
        return False
    
    def bulk_delete_products(self, product_ids: List[int]) -> int:
        """Delete multiple products"""
        deleted_count = 0
        for product_id in product_ids:
            if self.delete_product(product_id):
                deleted_count += 1
        return deleted_count
    
    def search_products(self, query: str) -> List[Dict[str, Any]]:
        """Search products by name or code"""
        query = query.lower()
        return [
            product for product in self.products
            if query in product['product_name'].lower() or query in product['product_code'].lower()
        ]
    
    def filter_products(self, filters: dict) -> List[Dict[str, Any]]:
        """Filter products by criteria"""
        results = self.products
        
        if 'category' in filters and filters['category']:
            results = [p for p in results if p['category'] == filters['category']]
        
        if 'region' in filters and filters['region']:
            results = [p for p in results if p['region'] == filters['region']]
        
        if 'is_active' in filters and filters['is_active'] is not None:
            results = [p for p in results if p['is_active'] == filters['is_active']]
        
        return results


# Singleton instance
_db = InMemoryDB()

def get_db() -> InMemoryDB:
    """Get database instance"""
    return _db
