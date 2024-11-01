import pandas as pd
import sys
from datetime import datetime
import os
import io
import contextlib

# Set UTF-8 encoding for stdout
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

def calculate_snowfall_stats(start_date, end_date, top_n=20):
    """
    Calculate snowfall statistics for ski resorts within a date range.
    Returns top N resorts by average snowfall.
    """
    try:
        # Load the CSV file
        print("Current working directory:", os.getcwd(), file=sys.stderr)
        
        if not os.path.exists('filtered_weather_data.csv'):
            print("Error: filtered_weather_data.csv not found", file=sys.stderr)
        df = pd.read_csv('filtered_weather_data.csv')
        
        # Convert the date column to datetime
        df['date'] = pd.to_datetime(df['date'])
        
        # Parse input dates
        start_date = datetime.strptime(start_date, '%m-%d')
        end_date = datetime.strptime(end_date, '%m-%d')
        
        # Create a mask for date filtering that ignores the year
        if start_date.month <= end_date.month:
            mask = (
                (df['date'].dt.month > start_date.month) |
                ((df['date'].dt.month == start_date.month) & (df['date'].dt.day >= start_date.day))
            ) & (
                (df['date'].dt.month < end_date.month) |
                ((df['date'].dt.month == end_date.month) & (df['date'].dt.day <= end_date.day))
            )
        else:
            # Handle cases spanning across years (e.g., Dec to Jan)
            mask = (
                ((df['date'].dt.month > start_date.month) |
                 ((df['date'].dt.month == start_date.month) & (df['date'].dt.day >= start_date.day))) |
                ((df['date'].dt.month < end_date.month) |
                 ((df['date'].dt.month == end_date.month) & (df['date'].dt.day <= end_date.day)))
            )
        
        filtered_df = df[mask]
        
        # Calculate days in period
        if start_date.month == 12 and end_date.month < 12:
            days_in_december = 31 - start_date.day + 1
            days_in_period = days_in_december + end_date.day
        else:
            if start_date.month == end_date.month:
                days_in_period = end_date.day - start_date.day + 1
            else:
                month_days = [31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31]
                if start_date.month < end_date.month:
                    days_in_period = (month_days[start_date.month - 1] - start_date.day + 1 +
                                    sum(month_days[start_date.month:(end_date.month - 1)]) +
                                    end_date.day)
                else:
                    days_in_period = (month_days[start_date.month - 1] - start_date.day + 1 +
                                    sum(month_days[start_date.month:] + month_days[:end_date.month - 1]) +
                                    end_date.day)

        # Group by resort and calculate statistics
        resort_stats = filtered_df.groupby(['country', 'resort', 'elevation'])['snowfall_sum'].agg([
            ('avg_snowfall', 'mean')
        ]).reset_index()
        
        # Calculate total snowfall based on avg_snowfall * days_in_period
        resort_stats['total_snowfall'] = resort_stats['avg_snowfall'] * days_in_period
        
        # Sort by average snowfall and get top N resorts
        resort_stats = resort_stats.nlargest(top_n, 'avg_snowfall')
        
        # Format results for output
        results = []
        for _, row in resort_stats.iterrows():
            resort_name = f"{row['resort']} ({row['elevation']}m)"
            # Remove any problematic characters
            resort_name = resort_name.replace('\u200b', '').replace('\u2010', '-')
            country = row['country'].replace('\u200b', '').replace('\u2010', '-')
            
            print(f"Location: {resort_name}, Avg Snowfall: {row['avg_snowfall']}, Total Snowfall: {row['total_snowfall']}, Country: {country}")

    except Exception as e:
        print(f"An error occurred: {e}", file=sys.stderr)

if __name__ == '__main__':
    if len(sys.argv) != 3:
        print("Usage: python script.py <start_date> <end_date>", file=sys.stderr)
        sys.exit(1)
    
    start_date = sys.argv[1]  # MM-DD format
    end_date = sys.argv[2]    # MM-DD format
    
    calculate_snowfall_stats(start_date, end_date)