// Global variables
let availableFolders = [];
let currentQuestionData = null;

// DOM elements
const questionIdInput = document.getElementById('questionId');
const searchBtn = document.getElementById('searchBtn');
const questionSection = document.getElementById('questionSection');
const loadingOverlay = document.getElementById('loadingOverlay');
const errorMessage = document.getElementById('errorMessage');
const closeBtn = document.getElementById('closeBtn');
const foldersGrid = document.getElementById('foldersGrid');

// Initialize the application
document.addEventListener('DOMContentLoaded', function() {
    initializeApp();
    setupEventListeners();
});

// Initialize application
async function initializeApp() {
    await loadFolders();
    renderFolders();
}

// Setup event listeners
function setupEventListeners() {
    // Search functionality
    searchBtn.addEventListener('click', handleSearch);
    questionIdInput.addEventListener('keypress', function(e) {
        if (e.key === 'Enter') {
            handleSearch();
        }
    });

    // Close question section
    closeBtn.addEventListener('click', closeQuestion);

    // Input validation and suggestions
    questionIdInput.addEventListener('input', handleInputChange);
}

// Load available folders from API
async function loadFolders() {
    try {
        const response = await fetch('/api/folders');
        const data = await response.json();
        availableFolders = data.folders || [];
        updateStats();
    } catch (error) {
        console.error('Error loading folders:', error);
        showError('Failed to load folder information');
    }
}

// Update statistics in header
function updateStats() {
    const folderCount = availableFolders.length;
    const totalQuestions = availableFolders.reduce((sum, folder) => sum + folder.count, 0);
    
    document.getElementById('folder-count').textContent = folderCount;
    document.getElementById('total-questions').textContent = totalQuestions;
}

// Render folder cards
function renderFolders() {
    foldersGrid.innerHTML = '';
    
    // Group folders by subject based on their path
    const mathFolders = [];
    const englishFolders = [];
    const otherFolders = [];
    
    availableFolders.forEach(folder => {
        const folderPath = folder.name.toLowerCase();
        if (folderPath.startsWith('math/') || 
            folderPath === 'algebra' || 
            folderPath === 'geometry' || 
            folderPath === 'advancedmath' || 
            folderPath === 'problemsolving') {
            mathFolders.push(folder);
        } else if (folderPath.startsWith('eng/') || 
                   folderPath === 'craftandstructure' || 
                   folderPath === 'expressionofidea' || 
                   folderPath === 'informationandideas' || 
                   folderPath === 'standardenglish') {
            englishFolders.push(folder);
        } else {
            otherFolders.push(folder);
        }
    });
    
    // Create subject categories
    if (mathFolders.length > 0) {
        createFolderCategory('Math', mathFolders, 'calculator');
    }
    
    if (englishFolders.length > 0) {
        createFolderCategory('English', englishFolders, 'book');
    }
    
    if (otherFolders.length > 0) {
        createFolderCategory('Other', otherFolders, 'folder');
    }
    
    // Add expand/collapse for small screens
    if (window.innerWidth <= 768) {
        addCollapseToggle();
    }
}

// Create folder category section
function createFolderCategory(title, folders, iconName) {
    const categoryContainer = document.createElement('div');
    categoryContainer.className = 'folders-category';
    
    const categoryTitle = document.createElement('h4');
    categoryTitle.innerHTML = `<i class="fas fa-${iconName}"></i> ${title}`;
    
    const categoryGrid = document.createElement('div');
    categoryGrid.className = 'folders-grid';
    
    folders.forEach(folder => {
        const folderCard = createFolderCard(folder);
        categoryGrid.appendChild(folderCard);
    });
    
    categoryContainer.appendChild(categoryTitle);
    categoryContainer.appendChild(categoryGrid);
    foldersGrid.appendChild(categoryContainer);
}

// Add collapse functionality for mobile
function addCollapseToggle() {
    const categories = document.querySelectorAll('.folders-category');
    const isMobile = window.innerWidth <= 480;
    
    categories.forEach((category, index) => {
        const title = category.querySelector('h4');
        const grid = category.querySelector('.folders-grid');
        
        // Add expand/collapse indicator
        const indicator = document.createElement('span');
        indicator.className = 'category-toggle';
        
        // On mobile, collapse all except first category
        const shouldCollapse = isMobile && index > 0;
        grid.style.display = shouldCollapse ? 'none' : 'grid';
        indicator.textContent = shouldCollapse ? ' (+)' : ' (-)';
        title.appendChild(indicator);
        
        title.style.cursor = 'pointer';
        
        title.addEventListener('click', () => {
            const isCollapsed = grid.style.display === 'none';
            grid.style.display = isCollapsed ? 'grid' : 'none';
            
            // Update indicator
            indicator.textContent = isCollapsed ? ' (-)' : ' (+)';
        });
    });
}

// Create folder card element
function createFolderCard(folder) {
    const card = document.createElement('div');
    card.className = 'folder-card';
    
    // Extract folder name without parent directory
    let displayName = folder.name;
    if (displayName.includes('/')) {
        displayName = displayName.split('/').pop();
    }
    
    // Format the name and count
    card.innerHTML = `
        <h4 title="${formatFolderName(folder.name)}">${formatFolderName(displayName)}</h4>
        <div class="question-count">${folder.count}</div>
    `;
    
    card.addEventListener('click', () => browseFolderQuestions(folder.name));
    return card;
}

// Format folder name for display
function formatFolderName(name) {
    // Handle path-based names (e.g., "math/algebra" -> "Algebra")
    let displayName = name;
    if (displayName.includes('/')) {
        displayName = displayName.split('/').pop();
    }
    
    // Handle specific folder name mappings for better readability
    const nameMap = {
        'craftandstructure': 'Craft and Structure',
        'expressionofidea': 'Expression of Ideas',
        'informationandideas': 'Information and Ideas',
        'standardenglish': 'Standard English',
        'advancedmath': 'Advanced Math',
        'problemsolving': 'Problem Solving'
    };
    
    const lowerName = displayName.toLowerCase();
    if (nameMap[lowerName]) {
        return nameMap[lowerName];
    }
    
    // Default formatting: capitalize first letter of each word
    return displayName
        .replace(/[_-]/g, ' ')
        .split(' ')
        .map(word => word.charAt(0).toUpperCase() + word.slice(1))
        .join(' ');
}

// Browse questions in a folder
async function browseFolderQuestions(folderName) {
    const modal = document.getElementById('questionListModal');
    const title = document.getElementById('questionListTitle');
    const scroll = document.getElementById('questionListScroll');
    
    // Find folder data for title
    const folder = availableFolders.find(f => f.name === folderName);
    const displayName = formatFolderName(folderName);
    const count = folder ? folder.count : '?';
    
    title.textContent = `${displayName} (${count} questions)`;
    scroll.innerHTML = '<div style="text-align: center; padding: 20px; color: var(--text-secondary);">Loading questions...</div>';
    
    modal.style.display = 'flex';
    
    try {
        // Encode the folder path properly for URLs with slashes
        const encodedFolder = encodeURIComponent(folderName);
        const response = await fetch(`/api/questions/${encodedFolder}`);
        const data = await response.json();
        
        if (data.success) {
            showFolderQuestions(data.questions);
        } else {
            scroll.innerHTML = '<div style="text-align: center; padding: 20px; color: var(--error-color);">Error loading questions</div>';
            console.error('Error:', data.error);
        }
    } catch (error) {
        scroll.innerHTML = '<div style="text-align: center; padding: 20px; color: var(--error-color);">Error loading questions</div>';
        console.error('Error browsing folder:', error);
    }
}

// Show folder questions in the modal
function showFolderQuestions(questions) {
    const scroll = document.getElementById('questionListScroll');
    scroll.innerHTML = '';
    
    if (!questions || questions.length === 0) {
        scroll.innerHTML = '<div style="text-align: center; padding: 20px; color: var(--text-secondary);">No questions found</div>';
        return;
    }
    
    questions.forEach(questionId => {
        const item = document.createElement('div');
        item.className = 'question-item';
        item.onclick = () => {
            loadQuestion(questionId);
            closeQuestionList();
        };
        
        const idElement = document.createElement('div');
        idElement.className = 'question-item-id';
        idElement.textContent = questionId;
        
        const selectElement = document.createElement('div');
        selectElement.className = 'question-item-select';
        selectElement.textContent = 'Select';
        
        item.appendChild(idElement);
        item.appendChild(selectElement);
        scroll.appendChild(item);
    });
}

// Close question list modal
function closeQuestionList() {
    const modal = document.getElementById('questionListModal');
    modal.style.display = 'none';
}

// Handle search button click
async function handleSearch() {
    const questionId = questionIdInput.value.trim();
    if (!questionId) {
        showError('Please enter a question ID');
        return;
    }

    await loadQuestion(questionId);
}

// Load question from API
async function loadQuestion(questionId) {
    try {
        showLoading();
        const response = await fetch(`/api/question/${questionId}`);
        const data = await response.json();
        
        if (data.success) {
            currentQuestionData = data;
            displayQuestion(data);
        } else {
            showError(data.error || 'Question not found');
        }
    } catch (error) {
        console.error('Error loading question:', error);
        showError('Failed to load question. Please check your connection.');
    } finally {
        hideLoading();
    }
}

// Global variables for answer state
let hasUserAnswered = false;
let correctAnswerLetter = null;

// Display question data
function displayQuestion(questionData) {
    const { data, folder } = questionData;
    
    // Reset answer state
    hasUserAnswered = false;
    correctAnswerLetter = null;
    
    // Update question metadata
    document.getElementById('displayQuestionId').textContent = questionIdInput.value;
    document.getElementById('displayFolder').textContent = formatFolderName(folder);
    document.getElementById('displayType').textContent = (data.type || 'MCQ').toUpperCase();
    
    // Display question stem
    displayQuestionStem(data.stem);
    
    // Display answer options if they exist
    const hasOptions = data.answerOptions && Array.isArray(data.answerOptions) && data.answerOptions.length > 0;
    const optionsSection = document.querySelector('.answer-options');
    
    // Always preload the data but control visibility based on options
    displayCorrectAnswer(data.correct_answer);
    displayRationale(data.rationale);
    
    if (hasOptions) {
        optionsSection.style.display = 'block';
        displayAnswerOptions(data.answerOptions, data.keys, data.correct_answer);
        
        // Hide the correct answer section initially for MCQs
        document.getElementById('correctAnswerSection').style.display = 'none';
        
        // Hide the rationale initially for MCQs
        document.getElementById('rationaleSection').style.display = 'none';
    } else {
        // Hide options section completely if no options
        optionsSection.style.display = 'none';
        
        // Show correct answer if no options (e.g., for informational content)
        document.getElementById('correctAnswerSection').style.display = 
            (data.correct_answer && data.correct_answer.length) ? 'block' : 'none';
            
        // Show rationale immediately if no options
        document.getElementById('rationaleSection').style.display = 
            data.rationale ? 'block' : 'none';
    }
    
    // Show question section
    questionSection.style.display = 'block';
    questionSection.scrollIntoView({ behavior: 'smooth' });
    
    // Render math after content is loaded
    setTimeout(() => {
        if (window.MathJax) {
            MathJax.typesetPromise();
        }
    }, 100);
}

// Display question stem
function displayQuestionStem(stem) {
    const stemContent = document.getElementById('stemContent');
    stemContent.innerHTML = formatContent(stem);
}

// Display answer options
function displayAnswerOptions(options, correctKeys, correctAnswerLetters) {
    const optionsContainer = document.getElementById('optionsContainer');
    optionsContainer.innerHTML = '';
    
    if (!options || !Array.isArray(options)) {
        optionsContainer.innerHTML = '<p>No answer options available</p>';
        return;
    }
    
    // Keep track of which option is correct by letter
    if (correctAnswerLetters && correctAnswerLetters.length > 0) {
        correctAnswerLetter = correctAnswerLetters[0]; // Use first correct answer for simplicity
    }
    
    options.forEach((option, index) => {
        const optionElement = createOptionElement(option, index, correctKeys);
        optionsContainer.appendChild(optionElement);
    });
}

// Create option element
function createOptionElement(option, index, correctKeys) {
    const optionDiv = document.createElement('div');
    const optionLabel = String.fromCharCode(65 + index); // A, B, C, D...
    const isCorrect = correctKeys && correctKeys.includes(option.id);
    
    optionDiv.className = 'option';
    optionDiv.dataset.correct = isCorrect;
    optionDiv.dataset.letter = optionLabel;
    optionDiv.innerHTML = `
        <div class="option-label">${optionLabel}</div>
        <div class="option-content">${formatContent(option.content)}</div>
    `;
    
    // Add click handler to handle selection
    optionDiv.addEventListener('click', function() {
        // If already answered, do nothing
        if (hasUserAnswered) return;
        
        // Mark as answered
        hasUserAnswered = true;
        
        // Mark this option as selected
        this.classList.add('selected');
        
        // Get current question data
        const questionData = currentQuestionData;
        if (!questionData || !questionData.data) return;
        
        // Check if correct or incorrect
        if (this.dataset.correct === 'true') {
            this.classList.add('correct');
            this.innerHTML += '<div class="option-result"><i class="fas fa-check-circle"></i></div>';
        } else {
            this.classList.add('incorrect');
            this.innerHTML += '<div class="option-result"><i class="fas fa-times-circle"></i></div>';
            
            // Highlight the correct answer
            document.querySelectorAll('.option').forEach(opt => {
                if (opt.dataset.correct === 'true') {
                    opt.classList.add('correct');
                    opt.innerHTML += '<div class="option-result"><i class="fas fa-check-circle"></i></div>';
                }
            });
        }
        
        // Update and show the correct answer section
        displayCorrectAnswer(questionData.data.correct_answer);
        document.getElementById('correctAnswerSection').style.display = 'block';
        
        // Update and show the explanation/rationale
        displayRationale(questionData.data.rationale);
        document.getElementById('rationaleSection').style.display = 'block';
        
        // Re-render math in newly shown content
        if (window.MathJax) {
            MathJax.typesetPromise();
        }
    });
    
    return optionDiv;
}

// Display correct answer
function displayCorrectAnswer(correctAnswer) {
    const correctAnswerDisplay = document.getElementById('correctAnswerDisplay');
    
    if (correctAnswer && Array.isArray(correctAnswer) && correctAnswer.length > 0) {
        correctAnswerDisplay.innerHTML = `
            <span class="correct-marker"><i class="fas fa-check-circle"></i></span>
            Option ${correctAnswer.join(', ')}
        `;
    } else {
        correctAnswerDisplay.textContent = 'Not specified';
    }
}

// Display rationale
function displayRationale(rationale) {
    const rationaleContent = document.getElementById('rationaleContent');
    
    if (rationale) {
        rationaleContent.innerHTML = formatContent(rationale);
    } else {
        rationaleContent.innerHTML = '<p>No explanation available</p>';
    }
}

// Format content for display (handle HTML and MathML)
function formatContent(content) {
    if (!content) return '';
    
    // First cleanup escaped characters
    let formatted = content
        .replace(/\\n/g, '\n')      // Replace literal \n with newline
        .replace(/\\"/g, '"')       // Replace \" with "
        .replace(/\\\\/g, '\\')     // Replace \\ with \
        .trim();
    
    // Clean up the content
    formatted = formatted
        .replace(/\s+/g, ' ')       // Normalize whitespace
        .replace(/>\s+</g, '><');   // Remove spaces between tags
    
    // Fix common MathML issues
    formatted = formatted
        .replace(/<math([^>]*)>(.*?)<\/math>/gs, (match, attributes, content) => {
            // Normalize the math tag content - careful cleaning of internal structure
            return `<math${attributes}>${content}</math>`;
        });
    
    // Ensure proper paragraph formatting
    if (!formatted.startsWith('<p') && !formatted.includes('<p>')) {
        formatted = `<p>${formatted}</p>`;
    }
    
    return formatted;
}

// Handle input change for suggestions
function handleInputChange() {
    const value = questionIdInput.value.trim();
    
    if (value.length < 2) {
        hideSuggestions();
        return;
    }
    
    // Simple validation
    if (!/^[a-fA-F0-9]*$/.test(value)) {
        questionIdInput.style.borderColor = '#ff6b6b';
    } else {
        questionIdInput.style.borderColor = '';
    }
}

// Show suggestions
function showSuggestions(suggestions) {
    const suggestionsContainer = document.getElementById('suggestions');
    suggestionsContainer.innerHTML = '';
    
    if (suggestions.length === 0) {
        hideSuggestions();
        return;
    }
    
    suggestions.forEach(suggestion => {
        const item = document.createElement('div');
        item.className = 'suggestion-item';
        item.textContent = suggestion;
        item.addEventListener('click', () => {
            questionIdInput.value = suggestion;
            hideSuggestions();
            handleSearch();
        });
        suggestionsContainer.appendChild(item);
    });
    
    suggestionsContainer.style.display = 'block';
}

// Hide suggestions
function hideSuggestions() {
    const suggestionsContainer = document.getElementById('suggestions');
    suggestionsContainer.style.display = 'none';
}

// Close question section
function closeQuestion() {
    questionSection.style.display = 'none';
    questionIdInput.value = '';
    currentQuestionData = null;
    hasUserAnswered = false;
    correctAnswerLetter = null;
    
    // Reset display sections for next question
    document.getElementById('correctAnswerSection').style.display = 'block';
    document.getElementById('rationaleSection').style.display = 'block';
}

// Show loading overlay
function showLoading() {
    loadingOverlay.style.display = 'flex';
}

// Hide loading overlay
function hideLoading() {
    loadingOverlay.style.display = 'none';
}

// Show error message
function showError(message) {
    const errorText = document.getElementById('errorText');
    errorText.textContent = message;
    errorMessage.style.display = 'block';
    
    // Auto-hide after 5 seconds
    setTimeout(hideError, 5000);
}

// Hide error message
function hideError() {
    errorMessage.style.display = 'none';
}

// Utility function to escape HTML
function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

// Close modal when clicking outside
document.addEventListener('DOMContentLoaded', function() {
    const modal = document.getElementById('questionListModal');
    if (modal) {
        modal.addEventListener('click', function(e) {
            if (e.target === this) {
                closeQuestionList();
            }
        });
    }
});

// Add keyboard shortcuts
document.addEventListener('keydown', function(e) {
    // ESC to close question
    if (e.key === 'Escape' && questionSection.style.display !== 'none') {
        closeQuestion();
    }
    
    // Ctrl+F to focus search
    if (e.ctrlKey && e.key === 'f') {
        e.preventDefault();
        questionIdInput.focus();
    }
});

// Handle window resize for responsive design
window.addEventListener('resize', function() {
    // Reposition elements if needed
    if (window.MathJax) {
        MathJax.typesetPromise();
    }
});

// Export functions for debugging
window.questionViewer = {
    loadQuestion,
    closeQuestion,
    showError,
    hideError,
    currentQuestionData: () => currentQuestionData
}; 