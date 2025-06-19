import json
import os
import asyncio
import aiohttp
import aiofiles
from pathlib import Path
from typing import Dict, List, Optional
import logging
from datetime import datetime
import time

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
        self.max_concurrent = 50  # Maximum concurrent requests
        self.timeout = aiohttp.ClientTimeout(total=30)
        
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
    
    async def make_api_call(self, session: aiohttp.ClientSession, external_id: str) -> Optional[Dict]:
        """Make async API call to get question data"""
        try:
            payload = {"external_id": external_id}
            
            async with session.post(
                self.api_url, 
                json=payload,
                headers=self.headers
            ) as response:
                if response.status == 200:
                    return await response.json()
                elif response.status == 429:
                    logging.warning(f"Rate limited (429) for external_id: {external_id}")
                    return None
                else:
                    logging.error(f"API call failed with status {response.status} for external_id: {external_id}")
                    return None
                
        except Exception as e:
            logging.error(f"Error making API call for external_id {external_id}: {e}")
            return None
    
    async def save_question_data(self, folder_path: str, question_id: str, data: Dict) -> bool:
        """Save question data to JSON file asynchronously"""
        try:
            file_path = os.path.join(folder_path, f"{question_id}.json")
            async with aiofiles.open(file_path, 'w', encoding='utf-8') as f:
                await f.write(json.dumps(data, indent=2, ensure_ascii=False))
            return True
        except Exception as e:
            logging.error(f"Error saving data for question {question_id}: {e}")
            return False
    
    async def process_single_question(self, session: aiohttp.ClientSession, item: Dict, output_folder: str, semaphore: asyncio.Semaphore) -> tuple[bool, str]:
        """Process a single question with concurrency control"""
        async with semaphore:
            question_id = item.get('questionId')
            external_id = item.get('external_id')
            
            if not question_id or not external_id:
                return False, f"Missing questionId or external_id"
            
            # Check if file already exists
            output_path = os.path.join(output_folder, f"{question_id}.json")
            if os.path.exists(output_path):
                return True, f"Skipped {question_id} - file already exists"
            
            # Make API call
            question_data = await self.make_api_call(session, external_id)
            
            if question_data:
                if await self.save_question_data(output_folder, question_id, question_data):
                    return True, f"Successfully saved {question_id}"
                else:
                    return False, f"Failed to save {question_id}"
            else:
                return False, f"Failed to get data for {question_id}"

    async def process_questions(self, data: List[Dict], output_folder: str):
        """Process all questions with maximum concurrency"""
        total_questions = len(data)
        print(f"\nProcessing {total_questions} questions with {self.max_concurrent} concurrent requests...")
        print("="*50)
        
        # Create semaphore to limit concurrent requests
        semaphore = asyncio.Semaphore(self.max_concurrent)
        
        # Create aiohttp session with connection pooling
        connector = aiohttp.TCPConnector(
            limit=100,  # Total connection pool size
            limit_per_host=self.max_concurrent,  # Per host limit
            keepalive_timeout=60,
            enable_cleanup_closed=True
        )
        
        start_time = time.time()
        
        async with aiohttp.ClientSession(
            connector=connector,
            timeout=self.timeout
        ) as session:
            # Create tasks for all questions
            tasks = [
                self.process_single_question(session, item, output_folder, semaphore)
                for item in data
            ]
            
            # Process with progress tracking
            successful = 0
            failed = 0
            completed = 0
            
            # Process in batches to show progress
            batch_size = min(100, len(tasks))
            for i in range(0, len(tasks), batch_size):
                batch = tasks[i:i + batch_size]
                results = await asyncio.gather(*batch, return_exceptions=True)
                
                for result in results:
                    completed += 1
                    if isinstance(result, Exception):
                        failed += 1
                        logging.error(f"Exception occurred: {result}")
                    else:
                        success, message = result
                        if success:
                            successful += 1
                        else:
                            failed += 1
                        if completed % 50 == 0:  # Log every 50 completions
                            logging.info(message)
                
                # Progress update
                progress = (completed / total_questions) * 100
                elapsed = time.time() - start_time
                rate = completed / elapsed if elapsed > 0 else 0
                print(f"Progress: {completed}/{total_questions} ({progress:.1f}%) - Rate: {rate:.1f} req/sec")
        
        # Final summary
        elapsed_total = time.time() - start_time
        print("\n" + "="*50)
        print("PROCESSING COMPLETE")
        print("="*50)
        print(f"Total questions: {total_questions}")
        print(f"Successful: {successful}")
        print(f"Failed: {failed}")
        print(f"Success rate: {(successful/total_questions)*100:.1f}%")
        print(f"Total time: {elapsed_total:.2f} seconds")
        print(f"Average rate: {total_questions/elapsed_total:.1f} requests/second")
        print("="*50)
    
    async def run_async(self):
        """Main async execution function"""
        print("High-Speed Question Bank Data Processor")
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
        
        # Get concurrency preference
        print(f"\nConcurrency Options (Current: {self.max_concurrent}):")
        print("1. Low (25 concurrent) - More conservative")
        print("2. Medium (50 concurrent) - Balanced")
        print("3. High (100 concurrent) - Maximum speed")
        print("4. Custom - Enter your own value")
        
        while True:
            try:
                choice = input("Select concurrency level (1-4): ").strip()
                if choice == '1':
                    self.max_concurrent = 25
                    break
                elif choice == '2':
                    self.max_concurrent = 50
                    break
                elif choice == '3':
                    self.max_concurrent = 100
                    break
                elif choice == '4':
                    custom = input("Enter concurrent requests (1-200): ").strip()
                    custom_val = int(custom)
                    if 1 <= custom_val <= 200:
                        self.max_concurrent = custom_val
                        break
                    else:
                        print("Please enter a value between 1 and 200")
                else:
                    print("Please enter 1, 2, 3, or 4")
            except ValueError:
                print("Please enter a valid number")
            except KeyboardInterrupt:
                print("\nExiting...")
                return
        
        # Confirm before starting
        print(f"\nReady to process {len(data)} questions into folder '{output_folder}'")
        print(f"Concurrent requests: {self.max_concurrent}")
        print("⚡ MAXIMUM SPEED MODE - No rate limiting! ⚡")
        confirm = input("Continue? (y/N): ").strip().lower()
        
        if confirm in ['y', 'yes']:
            # Process questions
            await self.process_questions(data, output_folder)
        else:
            print("Processing cancelled.")

    def run(self):
        """Main execution function wrapper"""
        asyncio.run(self.run_async())

def main():
    """Main function"""
    processor = QuestionBankProcessor()
    processor.run()

if __name__ == "__main__":
    main()
