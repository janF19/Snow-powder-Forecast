import pandas as pd
from sklearn.ensemble import RandomForestRegressor, RandomForestClassifier

# Load the data
df = pd.read_csv('winter_weather_data.csv')
df['date'] = pd.to_datetime(df['date'])

# Extract week and month, ignoring year
df['week'] = df['date'].dt.isocalendar().week
df['month'] = df['date'].dt.month

# Create powder day indicator
df['is_powder_day'] = (df['snowfall_sum'] >= 10)

# Features we'll use for prediction
features = ['week', 'month', 'elevation', 'latitude', 'longitude']

# Train the models
snowfall_model = RandomForestRegressor(n_estimators=100, random_state=42)
snowfall_model.fit(df[features], df['snowfall_sum'])

powder_model = RandomForestClassifier(n_estimators=100, random_state=42)
powder_model.fit(df[features], df['is_powder_day'])

def get_resorts_by_date_range(start_date, end_date):
    start_date = pd.to_datetime(start_date)
    end_date = pd.to_datetime(end_date)
    
    # Get weeks and months for the date range
    weeks = set()
    months = set()
    current_date = start_date
    while current_date <= end_date:
        weeks.add(current_date.isocalendar().week)
        months.add(current_date.month)
        current_date += pd.Timedelta(days=1)
    
    resort_predictions = []
    for resort in df['resort'].unique():
        resort_data = df[df['resort'] == resort]
        if not resort_data.empty:
            elevation = resort_data['elevation'].iloc[0]  # These should be constant for each resort
            latitude = resort_data['latitude'].iloc[0]
            longitude = resort_data['longitude'].iloc[0]
            
            # Make predictions for each week-month combination in the date range
            snowfall_preds = []
            powder_probs = []
            
            for week in weeks:
                for month in months:
                    features_dict = {
                        'week': week,
                        'month': month,
                        'elevation': elevation,
                        'latitude': latitude,
                        'longitude': longitude
                    }
                    
                    X_pred = pd.DataFrame([features_dict])
                    
                    snowfall_pred = snowfall_model.predict(X_pred)[0]
                    powder_prob = powder_model.predict_proba(X_pred)[0][1]
                    
                    snowfall_preds.append(snowfall_pred)
                    powder_probs.append(powder_prob)
            
            # Average the predictions across all week-month combinations
            avg_snowfall = sum(snowfall_preds) / len(snowfall_preds)
            avg_powder_prob = sum(powder_probs) / len(powder_probs)
            
            resort_predictions.append({
                'resort': resort,
                'predicted_snowfall': avg_snowfall,
                'probability_of_powder': avg_powder_prob * 100,
                'elevation': elevation
            })
    
    return resort_predictions

def get_top_resorts_by_powder_probability(resorts, n=5):
    return sorted(resorts, key=lambda x: x['probability_of_powder'], reverse=True)[:n]




import pandas as pd
from datetime import datetime
import pandas as pd
from datetime import datetime

def generate_monthly_summaries(predictions_func):
    """
    Generate monthly summaries of powder day probabilities for different resorts
    """
    months = {
        12: "December",
        1: "January",
        2: "February",
        3: "March",
        4: "April"
    }
    
    def get_predictions_for_month(month):
        # Use the first and last day of each month
        if month == 12:
            year = 2024
        else:
            year = 2025
            
        if month in [4, 6, 9, 11]:
            last_day = 30
        elif month == 2:
            last_day = 28
        else:
            last_day = 31
            
        start_date = f"{year}-{month:02d}-01"
        end_date = f"{year}-{month:02d}-{last_day}"
        
        predictions = predictions_func(start_date, end_date)
        # Add country information from the original dataframe
        for pred in predictions:
            resort_data = df[df['resort'] == pred['resort']]
            if not resort_data.empty:
                pred['country'] = resort_data['country'].iloc[0]
        return predictions

    def print_top_resorts(predictions, n=6, country_filter=None):
        filtered_predictions = predictions
        if country_filter:
            filtered_predictions = [p for p in predictions if p.get('country') == country_filter]
        
        top_resorts = sorted(filtered_predictions, 
                           key=lambda x: x['probability_of_powder'], 
                           reverse=True)[:n]
        
        if top_resorts:  # Only print if there are resorts to show
            for resort in top_resorts:
                print(f"  {resort['resort']:<40} - {resort['probability_of_powder']:>5.1f}%")
        else:
            print("  No resorts found for this country")

    # Overall monthly summary
    print("\n=== MONTHLY SUMMARY OF TOP POWDER DESTINATIONS ===")
    print("(Top 6 resorts globally for each month)\n")
    
    for month in months.keys():
        predictions = get_predictions_for_month(month)
        print(f"\n{months[month].upper()}:")
        print("-" * 50)
        print_top_resorts(predictions)

    # Country-specific summary
    countries = ['Austria', 'Switzerland', 'Italy', 'France', 'Germany', 'Slovakia']
    
    print("\n\n=== COUNTRY-SPECIFIC MONTHLY POWDER PROBABILITIES ===")
    print("(Top 5 resorts per country for each month)\n")
    
    for month in months.keys():
        print(f"\n{months[month].upper()}:")
        print("=" * 50)
        predictions = get_predictions_for_month(month)
        
        for country in countries:
            print(f"\n{country}:")
            print("-" * 30)
            print_top_resorts(predictions, n=5, country_filter=country)

if __name__ == "__main__":
    # Load the data first (needed for country information)
    df = pd.read_csv('winter_weather_data.csv')
    df['date'] = pd.to_datetime(df['date'])
    
    # Example date range for predictions
    start_date = '2025-01-01'
    end_date = '2025-01-10'
    
    print("Getting predictions for all resorts...")
    predictions = get_resorts_by_date_range(start_date, end_date)
    
    print("\nTop 10 resorts with highest powder probability:")
    top_resorts = get_top_resorts_by_powder_probability(predictions, n=10)
    for resort in top_resorts:
        print(f"Resort: {resort['resort']}")
        print(f"Elevation: {resort['elevation']}m")
        print(f"Predicted Snowfall: {resort['predicted_snowfall']:.1f}cm")
        print(f"Powder Probability: {resort['probability_of_powder']:.1f}%")
        print("-" * 50)
    
    # Generate monthly summaries
    generate_monthly_summaries(get_resorts_by_date_range)