import json
from datetime import datetime
import logging
import sys
import codecs
from difflib import SequenceMatcher

class UnicodedStreamHandler(logging.StreamHandler):
    def __init__(self, stream=None):
        if stream is None:
            stream = sys.stdout
        if sys.platform == 'win32':
            stream = codecs.getwriter('utf-8')(stream.buffer)
        super().__init__(stream)

def setup_logging(log_file_path):
    """Set up logging to both file and console with proper Unicode handling"""
    logging.getLogger().handlers = []
    formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
    
    file_handler = logging.FileHandler(log_file_path, encoding='utf-8')
    file_handler.setFormatter(formatter)
    
    console_handler = UnicodedStreamHandler()
    console_handler.setFormatter(formatter)
    
    logging.basicConfig(
        level=logging.INFO,
        handlers=[file_handler, console_handler]
    )

def normalize_name(name):
    """Normalize resort names by removing special characters and common suffixes"""
    name = name.replace('\u200b', '').strip()
    # Remove common suffixes and parenthetical additions
    common_suffixes = [" (Ski amedé)", " (Snow Space)", " (SkiWelt)"]
    for suffix in common_suffixes:
        name = name.replace(suffix, "")
    return name.lower()

def name_similarity(name1, name2):
    """Calculate similarity ratio between two names"""
    return SequenceMatcher(None, normalize_name(name1), normalize_name(name2)).ratio()

def check_elevations_match(resort_data, url_data, tolerance=5):
    """Check if elevations match within a tolerance"""
    try:
        resort_elevations = (
            int(resort_data.get('elevations', {}).get('Top Lift', {}).get('elevation_m', 0)),
            int(resort_data.get('elevations', {}).get('Mid Lift', {}).get('elevation_m', 0)),
            int(resort_data.get('elevations', {}).get('Bottom Lift', {}).get('elevation_m', 0))
        )
        url_elevations = (
            url_data.get('topLiftElevation_m'),
            url_data.get('midLiftElevation_m'),
            url_data.get('botLiftElevation_m')
        )
        
        if not all(resort_elevations) or not all(url_elevations):
            return False
            
        return all(abs(r - u) <= tolerance for r, u in zip(resort_elevations, url_elevations))
    except (TypeError, ValueError):
        return False

def merge_json_files(first_file_path, second_file_path, output_file_path, log_file_path):
    setup_logging(log_file_path)
    logging.info("Starting ordered merge process")
    
    try:
        # Load both files
        with open(first_file_path, 'r', encoding='utf-8') as f:
            resort_details = json.load(f)
        with open(second_file_path, 'r', encoding='utf-8') as f:
            resort_urls = json.load(f)
            
        logging.info(f"Loaded {len(resort_details)} resorts from first file")
        logging.info(f"Loaded {len(resort_urls)} resorts from second file")
        
        # Create new ordered dictionary based on second file's order
        ordered_merged = {}
        unmatched_resorts = []
        elevation_mismatches = []
        
        # Track statistics
        stats = {
            'matched': 0,
            'elevation_mismatch': 0,
            'not_found': 0
        }
        
        # Process resorts in order of second file
        for url_entry in resort_urls:
            url_resort_name = url_entry['resort']
            found_match = False
            best_match = None
            best_similarity = 0
            
            # Find best matching resort from first file
            for resort_name, resort_data in resort_details.items():
                similarity = name_similarity(url_resort_name, resort_name)
                if similarity > best_similarity:
                    best_similarity = similarity
                    best_match = (resort_name, resort_data)
            
            # If we found a good match (similarity > 0.8)
            if best_similarity > 0.8:
                resort_name, resort_data = best_match
                # Check elevations
                if check_elevations_match(resort_data, url_entry):
                    merged_data = resort_data.copy()
                    merged_data['url'] = url_entry['url']
                    ordered_merged[resort_name] = merged_data
                    stats['matched'] += 1
                    found_match = True
                else:
                    elevation_mismatches.append({
                        'resort_name': resort_name,
                        'url_name': url_resort_name,
                        'similarity': best_similarity,
                        'resort_elevations': {
                            'top': resort_data.get('elevations', {}).get('Top Lift', {}).get('elevation_m'),
                            'mid': resort_data.get('elevations', {}).get('Mid Lift', {}).get('elevation_m'),
                            'bot': resort_data.get('elevations', {}).get('Bottom Lift', {}).get('elevation_m')
                        },
                        'url_elevations': {
                            'top': url_entry.get('topLiftElevation_m'),
                            'mid': url_entry.get('midLiftElevation_m'),
                            'bot': url_entry.get('botLiftElevation_m')
                        }
                    })
                    stats['elevation_mismatch'] += 1
            
            if not found_match:
                unmatched_resorts.append(url_resort_name)
                stats['not_found'] += 1
        
        # Write merged data
        with open(output_file_path, 'w', encoding='utf-8') as f:
            json.dump(ordered_merged, f, indent=4, ensure_ascii=False)
        
        # Log results
        logging.info("\nMerge Summary:")
        logging.info(f"Total matches found: {stats['matched']}")
        logging.info(f"Elevation mismatches: {stats['elevation_mismatch']}")
        logging.info(f"No matches found: {stats['not_found']}")
        
        if elevation_mismatches:
            logging.info("\nElevation Mismatches (Name matches but elevations differ):")
            for mismatch in elevation_mismatches:
                logging.info(f"\nResort: {mismatch['resort_name']} / {mismatch['url_name']}")
                logging.info(f"Name similarity: {mismatch['similarity']:.2f}")
                logging.info("Resort elevations: "
                           f"Top={mismatch['resort_elevations']['top']}m, "
                           f"Mid={mismatch['resort_elevations']['mid']}m, "
                           f"Bot={mismatch['resort_elevations']['bot']}m")
                logging.info("URL elevations: "
                           f"Top={mismatch['url_elevations']['top']}m, "
                           f"Mid={mismatch['url_elevations']['mid']}m, "
                           f"Bot={mismatch['url_elevations']['bot']}m")
        
        if unmatched_resorts:
            logging.info("\nUnmatched Resorts:")
            for resort in unmatched_resorts:
                logging.info(f"- {resort}")
                
    except Exception as e:
        logging.error(f"An error occurred: {str(e)}")
        raise

if __name__ == "__main__":
    first_file = "weather_dataFull_4.json"
    second_file = "successful_url_region_resorts.json"
    output_file = "weather_dataFull_All_6.json.json"
    log_file = f"merge_log_ordered_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
    
    merge_json_files(first_file, second_file, output_file, log_file)
    
    

    
    

    
    
