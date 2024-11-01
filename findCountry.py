import pandas as pd
import json
import re
from difflib import get_close_matches


def clean_resort_names(resort_name):
    # Remove non-ASCII characters (hidden or special characters)
    resort_name = resort_name.encode('ascii', 'ignore').decode('ascii')

    # Replace specific characters with their simpler equivalents
    replacements = {
        'é': 'e', 'š': 's', 'ž': 'z', 'ý': 'y', 'ř': 'r',
        'č': 'c', 'ů': 'u', 'ń': 'n', 'ö': 'o', 'ä': 'a', 'ü': 'u'
    }
    for k, v in replacements.items():
        resort_name = resort_name.replace(k, v)

    # Strip leading/trailing spaces
    resort_name = resort_name.strip()

    return resort_name


def remove_unexpected_parentheses(resort_name):
    # Keep text before the first set of parentheses
    if '(' in resort_name:
        resort_name = resort_name.split('(')[0].strip()
    
    return resort_name


def format_resort_name(resort_name):
    # Convert to title case (capitalize first letter of each word)
    resort_name = resort_name.title()

    return resort_name


def clean_location_name(resort_name):
    # Remove special characters and hidden characters
    resort_name = clean_resort_names(resort_name)

    # Remove text in parentheses
    resort_name = remove_unexpected_parentheses(resort_name)

    # Ensure consistent title case formatting
    resort_name = format_resort_name(resort_name)

    return resort_name


# Step 1: Load the CSV file and clean resort names
def load_and_clean_csv(csv_file):
    df = pd.read_csv(csv_file)
    df['CleanedResort'] = df['Resort'].apply(clean_location_name)  # Create cleaned resort names
    resort_to_country = dict(zip(df['CleanedResort'], df['Country']))
    resort_to_original = dict(zip(df['CleanedResort'], df['Resort']))  # Keep track of original names
    return resort_to_country, resort_to_original

# Step 2: Load the JSON file
def load_json(json_file):
    with open(json_file, 'r') as f:
        resorts_data = json.load(f)
    return resorts_data


# Step 4: Match resorts from JSON to the closest match in the CSV
def match_resorts(json_resorts, resort_to_country, resort_to_original):
    matched_resorts = []
    unmatched_resorts = []
    
    for resort_data in json_resorts:
        resort_name = resort_data['resort']
        
        # Use difflib to find the best match
        best_matches = get_close_matches(resort_name, resort_to_country.keys(), n=1, cutoff=0.8)
        
        if best_matches:
            best_match = best_matches[0]

            # Update the resort name in the JSON with the original CSV name
            resort_data['resort'] = resort_to_original[best_match]

            # Add the country info to the resort data
            resort_data['Country'] = resort_to_country[best_match]
            matched_resorts.append(resort_data)
        else:
            unmatched_resorts.append(resort_data)
    
    return matched_resorts, unmatched_resorts



# Step 5: Save the new JSON file with updated resort names
def save_json(data, file_name):
    with open(file_name, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=4)
# Step 6: Main function to orchestrate the process


def main():
    # Load and clean CSV data
    resort_to_country, resort_to_original = load_and_clean_csv('European_Ski_Resorts.csv')
    
    # Load the original JSON data
    json_resorts = load_json('successful_resorts_data_v2.json')
    
    # Match resorts to countries and update names
    matched_resorts, unmatched_resorts = match_resorts(json_resorts, resort_to_country, resort_to_original)
    
    # Save the results
    save_json(matched_resorts, 'matched_resorts_with_countries.json')
    save_json(unmatched_resorts, 'unmatched_resorts.json')
    
    # Log the number of matched and unmatched resorts
    print(f"Number of matched resorts: {len(matched_resorts)}")
    print(f"Number of unmatched resorts: {len(unmatched_resorts)}")

# Run the script
if __name__ == "__main__":
    main()
