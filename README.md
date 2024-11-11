# Genna - Generative AI Annotation Tool

Genna (a portmanteau of "Generative AI" and "Annotation") is a powerful web-based annotation tool designed to facilitate data labeling and organization. It provides an intuitive interface for managing multiple annotation projects, with features specifically tailored for analyzing and categorizing data.

## Features

### Project Management
- Create and manage multiple annotation projects
- Configure project-specific settings
- Set project objectives and category columns
- Hierarchical project/file organization

### Data Handling
- CSV file upload support
- Dynamic table view with sorting capabilities
- Multi-filter functionality based on customizable category columns
- Real-time annotation saving

### Annotation System
- Thumbs up/down annotation options
- Comment field for detailed notes
- Auto-saving with debounce protection
- Separate storage for annotations and source files

### User Interface
- Clean, modern Bootstrap-based design
- Dark/light mode toggle
- Responsive layout for all screen sizes
- Intuitive project navigation

## Project Structure

```
genna/
├── app.py              # Flask application main file
├── static/
│   ├── script.js       # Client-side JavaScript
│   ├── styles.css      # Custom CSS styles
│   └── favicon.ico     # Site favicon
├── templates/
│   ├── index.html      # Main annotation interface
│   └── settings.html   # Project settings page
└── data/              # Project data directory
    └── {project_name}/ # Individual project directories
        ├── project_settings.json  # Project configuration
        ├── {csv_files}           # Uploaded CSV files
        └── annotations/          # Annotation JSON files
```

## Setup

1. Install dependencies:
```bash
pip install flask pandas
```

2. Run the application:
```bash
python app.py
```

3. Access the application at `http://localhost:5001`

## Usage

1. Project Creation:
   - Click the '+' button to create a new project
   - Configure project settings using the gear icon
   - Set project objective and category columns

2. Data Upload:
   - Select a project from the dropdown
   - Use the file input to upload CSV files
   - Files appear in the project's file list

3. Annotation:
   - Click on a CSV file to load it
   - Use thumbs up/down to annotate rows
   - Add comments as needed
   - All changes save automatically

4. Filtering:
   - Use the multi-select filters at the top
   - Combine multiple category filters
   - Filters are based on project settings

## Data Organization

- Each project has its own directory
- CSV files are stored in the project directory
- Annotations are stored separately as JSON files
- Project settings maintain category configurations
- All data is organized hierarchically for easy management

## Technical Details

- Backend: Flask (Python)
- Frontend: JavaScript, Bootstrap 5
- Data Storage: File-based (CSV, JSON)
- Styling: Custom CSS with dark/light mode support
- Real-time Updates: Debounced auto-saving
