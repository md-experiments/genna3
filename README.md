# Genna - Text Annotation System

Genna is a Flask-based text annotation system that allows you to:
1. Upload and manage CSV files for annotation
2. Configure AI models as annotators and judges
3. Manage annotations across multiple projects
4. Compare and evaluate annotations through a judging system

## Features

### Project Management
- Create and manage multiple annotation projects
- Upload CSV files to projects
- Configure which columns to show, label, use as content, or filter
- Set project objectives and annotation guidelines

### AI Models
- Configure AI models (like GPT-3, GPT-4) as annotators or judges
- Customize model parameters:
  - Temperature for controlling randomness
  - Custom prompts for different annotation tasks
  - Label types (text, boolean, numeric)

### Annotation System
1. **Annotators**
   - AI models configured to annotate text
   - Each annotator has a unique name and configuration
   - Can handle multiple label types per annotation
   - Annotations are stored separately from source data

2. **Judges**
   - Special AI models that evaluate annotations
   - Compare annotations from two different annotators
   - Selected dynamically at annotation time
   - Help evaluate annotation quality and consistency

### Category Columns
- Filter data using category columns
- Multi-select filtering capabilities
- Organize and manage annotations by categories

## Usage

### Setting Up a Project
1. Create a new project
2. Upload your CSV file
3. Configure column settings:
   - Show: Columns to display
   - Label: Columns to annotate
   - Content: Columns containing text to annotate
   - Filter: Category columns for filtering

### Creating Annotators
1. Go to project settings
2. Click "Add New Model"
3. Configure the annotator:
   - Give it a unique name
   - Select the AI model
   - Set temperature
   - Write base prompt
   - Configure label prompts
4. Save the annotator

### Using Judges
1. Create a judge model similar to annotators
2. When running the judge:
   - Click "Annotate" on the judge
   - Select two annotators to compare
   - Judge will evaluate their annotations
   - Results appear in the scores section

### Managing Files
- Files are automatically organized by project
- Annotations stored separately from source files
- Easy deletion of files when needed
- Category-based filtering for better organization

## Technical Details

### File Structure
```
project_name/
├── data/
│   ├── source_files/
│   │   └── uploaded_csv_files
│   └── annotations/
│       └── annotator_results
├── settings/
│   └── project_settings.json
└── models/
    └── model_configurations
```

### Annotation Format
Annotations are stored in a structured format:
```json
{
  "annotator_id": "unique_id",
  "timestamp": "ISO_timestamp",
  "labels": {
    "column1": "value1",
    "column2": true,
    "column3": 5
  }
}
```

### Judge Evaluation
Judges compare annotations by:
1. Analyzing both annotators' results
2. Evaluating consistency and quality
3. Providing numerical scores
4. Highlighting discrepancies

## Best Practices

1. **Project Setup**
   - Clear project objectives
   - Well-defined annotation guidelines
   - Consistent label schemas

2. **Model Configuration**
   - Descriptive model names
   - Clear, specific prompts
   - Appropriate temperature settings

3. **Judging**
   - Regular evaluation of annotations
   - Compare different annotator combinations
   - Monitor scores for quality control

4. **Data Management**
   - Regular backups
   - Clear category organization
   - Periodic cleanup of unused files
