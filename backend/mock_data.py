"""
Mock data generator for dashboard demo
Simulates sales data across multiple regions
"""
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import List, Dict, Any

# Configuration
REGIONS = ['A', 'B', 'C', 'D']
WEEKS = 13  # Historical data
FORECAST_WEEKS = 13
PRODUCTS = ['Product Alpha', 'Product Beta', 'Product Gamma', 'Product Delta', 'Product Epsilon']

class MockDataGenerator:
    """Generate realistic mock data for dashboard"""
    
    def __init__(self):
        np.random.seed(42)  # For consistent demo data
        self.start_date = datetime.now() - timedelta(weeks=WEEKS)
    
    def get_sales_data(self, region: str = None) -> pd.DataFrame:
        """
        Generate weekly sales data
        
        Args:
            region: Filter by region (None for all regions)
        
        Returns:
            DataFrame with columns: week_start, region, revenue, units_sold, avg_price
        """
        data = []
        
        regions = [region] if region and region != 'ALL' else REGIONS
        
        for reg in regions:
            # Base revenue varies by region
            base_revenue = {
                'A': 500000,
                'B': 450000,
                'C': 600000,
                'D': 400000
            }.get(reg, 500000)
            
            for week in range(WEEKS):
                week_start = self.start_date + timedelta(weeks=week)
                
                # Add seasonality and trend
                seasonality = np.sin(week * 2 * np.pi / 52) * 0.2
                trend = week * 0.02
                noise = np.random.normal(0, 0.1)
                
                multiplier = 1 + seasonality + trend + noise
                revenue = base_revenue * multiplier
                
                units_sold = int(revenue / np.random.uniform(80, 120))
                avg_price = revenue / units_sold if units_sold > 0 else 0
                
                data.append({
                    'week_start': week_start.strftime('%Y-%m-%d'),
                    'region': reg,
                    'revenue': round(revenue, 2),
                    'units_sold': units_sold,
                    'avg_price': round(avg_price, 2)
                })
        
        return pd.DataFrame(data)
    
    def get_target_data(self, region: str = None) -> pd.DataFrame:
        """
        Generate target vs actual data
        
        Returns:
            DataFrame with columns: week_start, region, target, actual, achievement_pct
        """
        sales_df = self.get_sales_data(region)
        
        # Set targets as 95% of max historical + 10% growth
        targets = []
        for _, row in sales_df.iterrows():
            target = row['revenue'] * 1.05  # 5% above actual for demo
            achievement_pct = (row['revenue'] / target) * 100
            
            targets.append({
                'week_start': row['week_start'],
                'region': row['region'],
                'target': round(target, 2),
                'actual': row['revenue'],
                'achievement_pct': round(achievement_pct, 2)
            })
        
        return pd.DataFrame(targets)
    
    def get_forecast_data(self, region: str = None) -> pd.DataFrame:
        """
        Generate forecast data for next 13 weeks
        
        Returns:
            DataFrame with columns: week_start, region, forecast_revenue, lower_bound, upper_bound
        """
        # Get historical data to base forecast on
        historical = self.get_sales_data(region)
        
        data = []
        regions = [region] if region and region != 'ALL' else REGIONS
        
        for reg in regions:
            reg_historical = historical[historical['region'] == reg]
            avg_revenue = reg_historical['revenue'].mean()
            std_revenue = reg_historical['revenue'].std()
            
            # Simple trend calculation
            trend = (reg_historical['revenue'].iloc[-1] - reg_historical['revenue'].iloc[0]) / len(reg_historical)
            
            last_date = datetime.strptime(reg_historical['week_start'].iloc[-1], '%Y-%m-%d')
            
            for week in range(1, FORECAST_WEEKS + 1):
                week_start = last_date + timedelta(weeks=week)
                
                # Forecast with trend and seasonality
                seasonality = np.sin((WEEKS + week) * 2 * np.pi / 52) * 0.2
                forecast = avg_revenue + (trend * week) + (avg_revenue * seasonality)
                
                # Confidence intervals (wider as we go further)
                uncertainty = std_revenue * (1 + week * 0.05)
                lower_bound = forecast - (1.96 * uncertainty)
                upper_bound = forecast + (1.96 * uncertainty)
                
                data.append({
                    'week_start': week_start.strftime('%Y-%m-%d'),
                    'region': reg,
                    'forecast_revenue': round(forecast, 2),
                    'lower_bound': round(max(0, lower_bound), 2),
                    'upper_bound': round(upper_bound, 2)
                })
        
        return pd.DataFrame(data)
    
    def get_kpis(self, region: str = None) -> Dict[str, Any]:
        """
        Calculate KPIs for dashboard
        
        Returns:
            Dict with KPI metrics
        """
        sales_df = self.get_sales_data(region)
        target_df = self.get_target_data(region)
        
        total_revenue = sales_df['revenue'].sum()
        total_target = target_df['target'].sum()
        avg_achievement = target_df['achievement_pct'].mean()
        
        # Growth (last 4 weeks vs previous 4 weeks)
        last_4_weeks = sales_df.tail(4)['revenue'].sum()
        previous_4_weeks = sales_df.iloc[-8:-4]['revenue'].sum()
        growth_pct = ((last_4_weeks - previous_4_weeks) / previous_4_weeks) * 100 if previous_4_weeks > 0 else 0
        
        # Get forecast
        forecast_df = self.get_forecast_data(region)
        next_month_forecast = forecast_df.head(4)['forecast_revenue'].sum()
        
        return {
            'total_revenue': round(total_revenue, 2),
            'total_target': round(total_target, 2),
            'achievement_rate': round(avg_achievement, 2),
            'growth_rate': round(growth_pct, 2),
            'next_month_forecast': round(next_month_forecast, 2),
            'total_units': int(sales_df['units_sold'].sum()),
            'avg_price': round(sales_df['avg_price'].mean(), 2)
        }
    
    def get_top_products(self, region: str = None, limit: int = 5) -> List[Dict[str, Any]]:
        """
        Get top products by revenue
        
        Returns:
            List of products with revenue and units sold
        """
        regions = [region] if region and region != 'ALL' else REGIONS
        
        data = []
        for product in PRODUCTS:
            for reg in regions:
                # Random revenue for each product
                revenue = np.random.uniform(100000, 800000)
                units = int(revenue / np.random.uniform(80, 150))
                
                data.append({
                    'product': product,
                    'region': reg,
                    'revenue': revenue,
                    'units_sold': units
                })
        
        df = pd.DataFrame(data)
        
        # Group by product and sum
        product_summary = df.groupby('product').agg({
            'revenue': 'sum',
            'units_sold': 'sum'
        }).reset_index()
        
        product_summary = product_summary.sort_values('revenue', ascending=False).head(limit)
        
        return [
            {
                'product': row['product'],
                'revenue': round(row['revenue'], 2),
                'units_sold': int(row['units_sold'])
            }
            for _, row in product_summary.iterrows()
        ]
    
    def get_region_comparison(self) -> List[Dict[str, Any]]:
        """
        Compare performance across all regions
        
        Returns:
            List of region metrics
        """
        result = []
        
        for region in REGIONS:
            sales = self.get_sales_data(region)
            kpis = self.get_kpis(region)
            
            result.append({
                'region': region,
                'total_revenue': kpis['total_revenue'],
                'achievement_rate': kpis['achievement_rate'],
                'growth_rate': kpis['growth_rate'],
                'total_units': kpis['total_units']
            })
        
        return sorted(result, key=lambda x: x['total_revenue'], reverse=True)


# Singleton instance
_generator = MockDataGenerator()

def get_data_generator() -> MockDataGenerator:
    """Get the singleton data generator instance"""
    return _generator
