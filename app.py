from flask import Flask, request, jsonify, render_template, send_from_directory
import json
import os
from pathlib import Path
import glob

app = Flask(__name__)

class QuestionFinder:
    def __init__(self):
        self.question_folders = []
        self.scan_folders()
    
    def scan_folders(self):
        """Scan for all question folders"""
        self.question_folders = []
        
        # Check content directories
        content_dirs = ['math', 'eng']
        
        for content_dir in content_dirs:
            if os.path.exists(content_dir):
                for item in os.listdir(content_dir):
                    folder_path = os.path.join(content_dir, item)
                    if os.path.isdir(folder_path):
                        json_files = glob.glob(os.path.join(folder_path, '*.json'))
                        if json_files:
                            self.question_folders.append(folder_path)
        
        # Also check root level folders
        possible_folders = [
            'craftAndStructure',
            'expressionOfIdea', 
            'informationAndIdeas',
            'standardEnglish',
            'geometry',
            'problemsolving',
            'advancedmath',
            'algebra'
        ]
        
        for folder in possible_folders:
            if os.path.exists(folder):
                json_files = glob.glob(os.path.join(folder, '*.json'))
                if json_files:
                    self.question_folders.append(folder)
        
        # Scan for any other folders containing JSON files
        for item in os.listdir('.'):
            if os.path.isdir(item) and item not in ['math', 'eng', 'templates', 'static'] and not item.startswith('.'):
                json_files = glob.glob(os.path.join(item, '*.json'))
                if json_files and item not in self.question_folders:
                    self.question_folders.append(item)
    
    def clean_html_content(self, content):
        """Clean HTML content by removing extra escape characters"""
        if isinstance(content, str):
            # Fix common SVG/MathML issues with escape characters
            return content.replace('\\n', '\n').replace('\\"', '"')
        return content
    
    def process_json_data(self, data):
        """Process JSON data to fix escape character issues"""
        # Fix stem content
        if 'stem' in data:
            data['stem'] = self.clean_html_content(data['stem'])
        
        # Fix answer options
        if 'answerOptions' in data and isinstance(data['answerOptions'], list):
            for option in data['answerOptions']:
                if 'content' in option:
                    option['content'] = self.clean_html_content(option['content'])
        
        # Fix rationale
        if 'rationale' in data:
            data['rationale'] = self.clean_html_content(data['rationale'])
            
        return data
        
    def find_question(self, question_id):
        """Find a question by ID in all folders"""
        for folder in self.question_folders:
            file_path = os.path.join(folder, f"{question_id}.json")
            if os.path.exists(file_path):
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                    
                    # Process data to fix escape characters
                    processed_data = self.process_json_data(data)
                    
                    return {
                        'success': True,
                        'data': processed_data,
                        'folder': folder
                    }
                except Exception as e:
                    return {
                        'success': False,
                        'error': f"Error reading file: {str(e)}"
                    }
        
        return {
            'success': False,
            'error': f"Question with ID '{question_id}' not found in any folder"
        }
    
    def get_available_folders(self):
        """Get list of available folders with question counts"""
        folder_info = []
        for folder in self.question_folders:
            json_files = glob.glob(os.path.join(folder, '*.json'))
            folder_info.append({
                'name': folder,
                'count': len(json_files)
            })
        return folder_info

question_finder = QuestionFinder()

@app.route('/')
def index():
    """Serve the main page"""
    return render_template('index.html')

@app.route('/api/question/<question_id>')
def get_question(question_id):
    """API endpoint to get a question by ID"""
    result = question_finder.find_question(question_id)
    return jsonify(result)

@app.route('/api/folders')
def get_folders():
    """API endpoint to get available folders"""
    folders = question_finder.get_available_folders()
    return jsonify({'folders': folders})

@app.route('/api/questions/<path:folder_name>')
def get_questions_in_folder(folder_name):
    """API endpoint to get all question IDs in a folder"""
    # Check if folder exists in our list (with more flexible matching)
    folder_exists = False
    for folder in question_finder.question_folders:
        if folder == folder_name or folder.replace('\\', '/') == folder_name:
            folder_exists = True
            folder_name = folder
            break
    
    if not folder_exists:
        return jsonify({'success': False, 'error': f'Folder not found: {folder_name}'})
    
    json_files = glob.glob(os.path.join(folder_name, '*.json'))
    question_ids = [os.path.splitext(os.path.basename(f))[0] for f in json_files]
    question_ids.sort()
    
    return jsonify({
        'success': True,
        'questions': question_ids,
        'count': len(question_ids)
    })

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000) 