<h1><img alt='Genna logo' src='static/logo.png' width='40' align='left' style="padding:1px 5px 1px 1px;"/>Genna - Generative Annotation System </h1>
  
Genna (GENerative ANNotation) is a LLM-centric text annotation system designed for efficient text annotation and comparison of AI model outputs.
Genna makes it easy to test out different LLMs, prompts, temperature and scalability of structured calls.

[![Genna Demo Tutorial](https://img.youtube.com/vi/96vzQGtxzoA/0.jpg)](https://youtu.be/96vzQGtxzoA)


## Key Features at a Glance
- 🤖 **AI Model Integration**: Configure multiple AI models as annotators: supports OpenAI, Anthropic and Ollama
- 📊 **Custom Dataset Management**: Evolve your dataset, add new files, remove files, while keeping track of metrics
- 📋 **Human Annotation Interface**: 
  - Interactive annotation with thumbs up/down feedback
  - Real-time disagreement detection between AI models
  - Expandable annotation view for each row
  - Dark mode support for comfortable viewing
- 🔍 **Smart Filtering**:
  - Filter by content across any column
  - Show only rows with AI model disagreements
  - Category-based multi-filtering
- 📈 **Annotation Analysis**:
  - Visual indicators for model agreements/disagreements
  - Summary view showing differences between model outputs
  - Quick toggle to show/hide all annotations





## Setup
1. Start and environment and install requirements: 
```
conda create --name genna
conda activate genna
pip install -r requirements.txt
```
2. Start the application 
```
python app.py
```
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

### Using the Annotation Interface
1. Select a file to annotate
2. Use the expand/collapse buttons to view annotations
3. Review AI model outputs
4. Provide feedback using thumbs up/down
5. Use filters to focus on specific content:
   - Text search in any column
   - Show only rows with model disagreements
   - Category-based filtering
6. Toggle dark mode for comfortable viewing
7. Use bulk actions to show/hide all annotations

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
   - Real-time visual feedback for model agreements/disagreements
   - Interactive thumbs up/down interface for manual annotation

2. **Annotation Interface**
   - Expandable rows showing all model annotations
   - Summary row indicating differences between model outputs
   - Dark mode support for reduced eye strain
   - Quick filters to show only rows with disagreements
   - Bulk show/hide annotations across all rows

3. **Judges**
   - Special AI models that evaluate annotations
   - Compare annotations from two different annotators
   - Selected dynamically at annotation time
   - Help evaluate annotation quality and consistency

### Category Columns
- Filter data using category columns
- Multi-select filtering capabilities
- Organize and manage annotations by categories
- Quick text search within any column

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

3. **Annotation Review**
   - Use the disagreement filter to focus on problematic cases
   - Review all model outputs before providing feedback
   - Pay attention to the summary indicators
   - Regular evaluation using judges

4. **Data Management**
   - Regular backups
   - Clear category organization
   - Periodic cleanup of unused files
   - Use filters effectively to manage large datasets
