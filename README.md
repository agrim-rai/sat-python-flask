# SAT Question Viewer 🧠

A beautiful, modern web application to view and browse SAT questions with proper mathematical notation rendering.

## ✨ Features

- **Smart Question Search**: Enter any question ID to instantly fetch and display the question
- **Folder Browser**: Browse questions by subject (Math, English) with live statistics
- **Mathematical Rendering**: Perfect MathML rendering using MathJax
- **Beautiful Design**: Modern, responsive UI with smooth animations
- **Answer Highlighting**: Correct answers are visually highlighted
- **Detailed Explanations**: Full rationale and explanations for each question
- **Keyboard Shortcuts**: Efficient navigation with keyboard support
- **Mobile Responsive**: Works perfectly on all devices

## 🚀 Quick Start

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Start the Application

```bash
python app.py
```

### 3. Open Your Browser

Navigate to `http://localhost:5000` and start exploring!

## 📁 Project Structure

```
sat-question-viewer/
├── app.py                 # Flask backend server
├── parser.py             # Question data processor (for generating folders)
├── requirements.txt      # Python dependencies
├── templates/
│   └── index.html       # Main application template
├── static/
│   ├── css/
│   │   └── style.css    # Application styles
│   └── js/
│       └── app.js       # Frontend JavaScript
└── [question folders]/  # Generated question folders
    ├── math_geometry/
    ├── math_algebra/
    ├── english_craftAndStructure/
    └── ...
```

## 🎯 How to Use

### Search for Questions

1. **By Question ID**: Enter the question ID (e.g., `1f0b582e`) in the search box
2. **Browse by Folder**: Click on any folder card to see available questions
3. **Keyboard Shortcuts**: 
   - Press `Enter` in the search box to search
   - Press `Escape` to close the current question
   - Press `Ctrl+F` to focus the search box

### Question Display

Once you search for a question, you'll see:

- **Question Text**: Properly formatted with mathematical notation
- **Answer Options**: Multiple choice options (A, B, C, D)
- **Correct Answer**: Highlighted in green
- **Detailed Explanation**: Step-by-step rationale

### Mathematical Notation

The application uses **MathJax** to render mathematical expressions:
- Inline math: `$x^2 + y^2 = z^2$`
- Display math: `$$\int_{-\infty}^{\infty} e^{-x^2} dx = \sqrt{\pi}$$`
- MathML: Full support for MathML elements

## 🔧 Configuration

### Folder Structure

The app automatically scans for question folders. Supported folder names:
- `math_geometry`
- `math_algebra` 
- `math_problemsolving`
- `math_advancedmath`
- `english_craftAndStructure`
- `english_expressionOfIdea`
- `english_informationAndIdeas`
- `english_standardEnglish`

### Custom Folders

Add any folder containing `.json` files and the app will automatically detect it.

## 🎨 Customization

### Styling

Edit `static/css/style.css` to customize:
- Colors and themes
- Fonts and typography
- Layout and spacing
- Animations and effects

### Functionality

Edit `static/js/app.js` to modify:
- Search behavior
- Display formatting
- User interactions
- API calls

## 📱 Responsive Design

The application is fully responsive and includes:
- **Desktop**: Full-featured interface with sidebar navigation
- **Tablet**: Adapted layout with touch-friendly controls
- **Mobile**: Optimized for phone screens with collapsible sections

## 🚀 Performance Features

- **Fast Loading**: Efficient API calls and caching
- **Smooth Animations**: CSS transitions and transforms
- **Optimized Math Rendering**: Lazy-loaded MathJax with performance optimizations
- **Error Handling**: Graceful error messages and recovery

## 🐛 Troubleshooting

### Common Issues

1. **Question Not Found**
   - Verify the question ID is correct
   - Check if the question folder exists
   - Ensure the JSON file is properly formatted

2. **Math Not Rendering**
   - Check internet connection (MathJax loads from CDN)
   - Wait a moment for MathJax to initialize
   - Refresh the page if math appears as raw text

3. **Folders Not Loading**
   - Ensure folder permissions are correct
   - Check that folders contain valid JSON files
   - Restart the Flask application

### Error Messages

- **"Question not found"**: The question ID doesn't exist in any folder
- **"Failed to load folders"**: Issue accessing the folder structure
- **"Failed to load question"**: Network or file access issue

## 🔍 API Endpoints

The Flask backend provides these endpoints:

- `GET /` - Main application page
- `GET /api/folders` - List all available folders with question counts
- `GET /api/question/<id>` - Fetch specific question data
- `GET /api/questions/<folder>` - List all questions in a folder

## 🎯 Example Usage

```javascript
// Search for a question
await questionViewer.loadQuestion('1f0b582e');

// Show error message
questionViewer.showError('Custom error message');

// Get current question data
const data = questionViewer.currentQuestionData();
```

## 📊 Supported Question Format

Questions should be in JSON format with these fields:

```json
{
  "stem": "Question text with <math>...</math>",
  "answerOptions": [
    {
      "id": "option-id",
      "content": "Option text with <math>...</math>"
    }
  ],
  "correct_answer": ["A"],
  "keys": ["correct-option-id"],
  "rationale": "Explanation with <math>...</math>",
  "type": "mcq"
}
```

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test thoroughly
5. Submit a pull request

## 📄 License

This project is open source and available under the MIT License.

---

**Happy Learning! 🎓** 