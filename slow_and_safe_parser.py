
import json
import os
import requests
import time
from pathlib import Path
from typing import Dict, List, Optional
import logging
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('api_calls.log'),
        logging.StreamHandler()
    ]
)

class QuestionBankProcessor:
    def __init__(self):
        self.api_url = "https://qbank-api.collegeboard.org/msreportingquestionbank-prod/questionbank/digital/get-question"
        self.headers = {
            'Content-Type': 'application/json',
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        self.session = requests.Session()
        self.session.headers.update(self.headers)
        
    def list_available_files(self) -> Dict[str, List[str]]:
        """List all JSON files in eng and math directories"""
        available_files = {}
        
        for directory in ['eng', 'math']:
            if os.path.exists(directory):
                files = [f for f in os.listdir(directory) if f.endswith('.json')]
                available_files[directory] = files
            else:
                available_files[directory] = []
                
        return available_files
    
    def display_file_menu(self) -> str:
        """Display available files and get user selection"""
        files = self.list_available_files()
        
        print("\n" + "="*50)
        print("Available JSON Files:")
        print("="*50)
        
        file_options = []
        counter = 1
        
        for directory, file_list in files.items():
            if file_list:
                print(f"\n{directory.upper()} Directory:")
                print("-" * 20)
                for file in file_list:
                    print(f"{counter}. {file}")
                    file_options.append(os.path.join(directory, file))
                    counter += 1
        
        if not file_options:
            print("No JSON files found in eng or math directories!")
            return None
            
        print("\n" + "="*50)
        
        while True:
            try:
                choice = input(f"Select a file (1-{len(file_options)}): ").strip()
                index = int(choice) - 1
                if 0 <= index < len(file_options):
                    return file_options[index]
                else:
                    print(f"Please enter a number between 1 and {len(file_options)}")
            except ValueError:
                print("Please enter a valid number")
            except KeyboardInterrupt:
                print("\nExiting...")
                return None
    
    def load_json_file(self, file_path: str) -> Optional[List[Dict]]:
        """Load and parse the selected JSON file"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            logging.info(f"Successfully loaded {file_path} with {len(data)} items")
            return data
        except Exception as e:
            logging.error(f"Error loading {file_path}: {e}")
            return None
    
    def create_output_folder(self, file_path: str) -> str:
        """Create output folder based on JSON filename"""
        # Extract filename without extension
        base_name = Path(file_path).stem
        folder_name = base_name.replace('.json', '')
        
        # Create folder if it doesn't exist
        if not os.path.exists(folder_name):
            os.makedirs(folder_name)
            logging.info(f"Created folder: {folder_name}")
        else:
            logging.info(f"Using existing folder: {folder_name}")
            
        return folder_name
    
    def make_api_call(self, external_id: str) -> Optional[Dict]:
        """Make API call to get question data"""
        try:
            payload = {"external_id": external_id}
            
            response = self.session.post(
                self.api_url, 
                json=payload,
                timeout=30
            )
            
            if response.status_code == 200:
                return response.json()
            elif response.status_code == 429:
                logging.warning(f"Rate limited (429) for external_id: {external_id}")
                return None
            else:
                logging.error(f"API call failed with status {response.status_code} for external_id: {external_id}")
                return None
                
        except Exception as e:
            logging.error(f"Error making API call for external_id {external_id}: {e}")
            return None
    
    def save_question_data(self, folder_path: str, question_id: str, data: Dict) -> bool:
        """Save question data to JSON file"""
        try:
            file_path = os.path.join(folder_path, f"{question_id}.json")
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            return True
        except Exception as e:
            logging.error(f"Error saving data for question {question_id}: {e}")
            return False
    
    def process_questions(self, data: List[Dict], output_folder: str, delay: float = 2.0):
        """Process all questions with rate limiting"""
        total_questions = len(data)
        processed = 0
        successful = 0
        failed = 0
        
        print(f"\nProcessing {total_questions} questions...")
        print(f"Rate limiting: {delay} seconds between requests")
        print("="*50)
        
        for i, item in enumerate(data, 1):
            question_id = item.get('questionId')
            external_id = item.get('external_id')
            
            if not question_id or not external_id:
                logging.warning(f"Missing questionId or external_id in item {i}")
                failed += 1
                continue
            
            # Check if file already exists
            output_path = os.path.join(output_folder, f"{question_id}.json")
            if os.path.exists(output_path):
                logging.info(f"Skipping {question_id} - file already exists")
                processed += 1
                successful += 1
                continue
            
            print(f"Processing {i}/{total_questions}: {question_id}")
            
            # Make API call
            question_data = self.make_api_call(external_id)
            
            if question_data:
                if self.save_question_data(output_folder, question_id, question_data):
                    successful += 1
                    logging.info(f"Successfully saved {question_id}")
                else:
                    failed += 1
            else:
                failed += 1
                logging.error(f"Failed to get data for {question_id}")
            
            processed += 1
            
            # Rate limiting - wait between requests
            if i < total_questions:  # Don't wait after the last request
                time.sleep(delay)
            
            # Progress update every 10 items
            if i % 10 == 0:
                print(f"Progress: {i}/{total_questions} ({(i/total_questions)*100:.1f}%)")
        
        # Final summary
        print("\n" + "="*50)
        print("PROCESSING COMPLETE")
        print("="*50)
        print(f"Total questions: {total_questions}")
        print(f"Processed: {processed}")
        print(f"Successful: {successful}")
        print(f"Failed: {failed}")
        print(f"Success rate: {(successful/processed)*100:.1f}%")
        print("="*50)
    
    def run(self):
        """Main execution function"""
        print("Question Bank Data Processor")
        print("="*50)
        
        # Select file
        selected_file = self.display_file_menu()
        if not selected_file:
            return
        
        print(f"\nSelected file: {selected_file}")
        
        # Load data
        data = self.load_json_file(selected_file)
        if not data:
            print("Failed to load the selected file.")
            return
        
        # Create output folder
        output_folder = self.create_output_folder(selected_file)
        
        # Get rate limiting preference
        print("\nRate Limiting Options:")
        print("1. Conservative (3 seconds) - Safest")
        print("2. Moderate (2 seconds) - Balanced")
        print("3. Aggressive (1 second) - Faster but riskier")
        
        while True:
            try:
                choice = input("Select rate limiting (1-3): ").strip()
                delay_map = {'1': 3.0, '2': 2.0, '3': 1.0}
                if choice in delay_map:
                    delay = delay_map[choice]
                    break
                else:
                    print("Please enter 1, 2, or 3")
            except KeyboardInterrupt:
                print("\nExiting...")
                return
        
        # Confirm before starting
        print(f"\nReady to process {len(data)} questions into folder '{output_folder}'")
        print(f"Rate limiting: {delay} seconds between requests")
        confirm = input("Continue? (y/N): ").strip().lower()
        
        if confirm in ['y', 'yes']:
            # Process questions
            self.process_questions(data, output_folder, delay)
        else:
            print("Processing cancelled.")

def main():
    """Main function"""
    processor = QuestionBankProcessor()
    processor.run()

if __name__ == "__main__":
    main()
