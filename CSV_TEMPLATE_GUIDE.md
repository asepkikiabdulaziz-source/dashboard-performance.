# Sample CSV Template for Product Import

## Valid CSV Example

```csv
product_code,product_name,category,region,price,stock,is_active
PROD100,Smartphone Samsung Galaxy,Electronics,A,8500000,75,true
PROD101,Office Desk Wooden,Furniture,B,3500000,30,true
PROD102,Jeans Levis 501,Clothing,C,850000,200,true
PROD103,Rice Cooker Philips,Electronics,A,450000,150,true
PROD104,Organic Honey 500ml,Food,D,125000,80,true
```

## Field Descriptions

| Field | Type | Required | Rules |
|-------|------|----------|-------|
| product_code | String | Yes | 3-20 characters, alphanumeric, unique |
| product_name | String | Yes | 3-100 characters |
| category | String | Yes | Must be one of: Electronics, Clothing, Food, Furniture, Books |
| region | String | Yes | Must be one of: A, B, C, D |
| price | Number | Yes | Must be greater than 0 |
| stock | Integer | Yes | Must be 0 or positive |
| is_active | Boolean | No | true/false, 1/0, yes/no (default: true) |

## Business Rules

1. **Product Code**: Must be unique across all products
2. **Active Products**: Should have at least 10 units in stock (warning if less)
3. **Price Ranges** (warning if outside):
   - Electronics: IDR 100,000 - 50,000,000
   - Furniture: IDR 50,000 - 20,000,000
   - Clothing: IDR 10,000 - 5,000,000
   - Food: IDR 1,000 - 1,000,000
   - Books: IDR 10,000 - 1,000,000

## Common Errors

### Header Errors
- ❌ Missing required columns
- ❌ Unknown column names
- ❌ Wrong spelling of column names

### Data Errors
- ❌ Empty required fields
- ❌ Invalid category (must match exact spelling)
- ❌ Invalid region (only A, B, C, D allowed)
- ❌ Negative price or stock
- ❌ Price = 0
- ❌ Non-numeric values in price/stock
- ❌ Duplicate product codes

## How to Use

1. **Download Template**: Click "Template" button in Admin Panel
2. **Fill Data**: Open in Excel/Google Sheets and fill your products
3. **Save as CSV**: Save file as CSV (UTF-8 encoding)
4. **Upload**: Click "Import CSV" in Admin Panel
5. **Review Validation**: Check for errors and warnings
6. **Import**: Click "Import Now" if validation passes

## Tips

- Use UTF-8 encoding when saving CSV
- Don't add extra spaces in data
- Use exact category and region names
- Product codes are case-insensitive (will be converted to uppercase)
- Duplicate product codes will be skipped during import
