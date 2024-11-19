from flask import Flask, render_template, request, jsonify, send_from_directory
import pandas as pd
import json
import os
from collections import OrderedDict

app = Flask(__name__)

BASE_DIR = 'data'
ANNOTATIONS_DIR = 'annotations'

def get_project_settings(project_name):
    settings_file = os.path.join(BASE_DIR, project_name, 'project_settings.json')
    if os.path.exists(settings_file):
        with open(settings_file, 'r') as f:
            return json.load(f)
    return {
        'columns': {},
        'objective': '',
        'ai_annotators': []
    }

def get_project_columns(project_name):
    """Gather unique column names from all CSV files in the project, maintaining order."""
    project_dir = os.path.join(BASE_DIR, project_name)
    seen_columns = OrderedDict()
    
    if os.path.exists(project_dir):
        for file in os.listdir(project_dir):
            if file.endswith('.csv'):
                file_path = os.path.join(project_dir, file)
                try:
                    df = pd.read_csv(file_path)
                    for col in df.columns:
                        seen_columns[col] = None
                except Exception as e:
                    print(f"Error reading {file}: {str(e)}")
    
    return list(seen_columns.keys())

def save_project_settings(project_name, settings):
    settings_file = os.path.join(BASE_DIR, project_name, 'project_settings.json')
    os.makedirs(os.path.dirname(settings_file), exist_ok=True)
    with open(settings_file, 'w') as f:
        json.dump(settings, f)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/settings/<project>')
def project_settings(project):
    return render_template('settings.html', project=project)

@app.route('/get_project_settings/<project>')
def get_settings(project):
    settings = get_project_settings(project)
    columns = get_project_columns(project)
    
    # Initialize column settings if they don't exist
    if 'columns' not in settings:
        settings['columns'] = {}
    
    # Ensure all columns have settings
    for col in columns:
        if col not in settings['columns']:
            settings['columns'][col] = {
                'show': True,
                'label': False,
                'content': False,
                'filter': False
            }
    
    return jsonify({
        'settings': settings,
        'columns': columns
    })

@app.route('/save_project_settings/<project>', methods=['POST'])
def save_settings(project):
    settings = request.json
    save_project_settings(project, settings)
    return jsonify({'success': True, 'message': 'Settings saved successfully'})

# ... [rest of the routes remain unchanged]

@app.route('/get_projects')
def get_projects():
    projects = [d for d in os.listdir(BASE_DIR) if os.path.isdir(os.path.join(BASE_DIR, d))]
    return jsonify(projects)

@app.route('/create_project', methods=['POST'])
def create_project():
    project_name = request.json.get('project_name')
    if project_name:
        project_path = os.path.join(BASE_DIR, project_name)
        if not os.path.exists(project_path):
            os.makedirs(project_path)
            # Initialize default settings
            save_project_settings(project_name, {
                'columns': {},
                'objective': '',
                'ai_annotators': []
            })
            return jsonify({'success': True, 'message': 'Project created successfully'})
        else:
            return jsonify({'success': False, 'message': 'Project already exists'})
    return jsonify({'success': False, 'message': 'Invalid project name'})

@app.route('/get_project_files/<project>')
def get_project_files(project):
    project_dir = os.path.join(BASE_DIR, project)
    files = [f for f in os.listdir(project_dir) if f.endswith('.csv')]
    return jsonify(files)

@app.route('/upload_csv', methods=['POST'])
def upload_csv():
    file = request.files['file']
    project = request.form['project']
    if file and file.filename.endswith('.csv'):
        filename = file.filename
        project_dir = os.path.join(BASE_DIR, project)
        os.makedirs(project_dir, exist_ok=True)
        file_path = os.path.join(project_dir, filename)
        file.save(file_path)
        return jsonify({'message': 'File uploaded successfully', 'filename': filename})
    return jsonify({'error': 'Invalid file format'})

@app.route('/load_csv/<project>/<filename>')
def load_csv(project, filename):
    file_path = os.path.join(BASE_DIR, project, filename)
    if os.path.exists(file_path):
        df = pd.read_csv(file_path).fillna('')
        data = df.to_dict(orient='records')
        columns = df.columns.tolist()
        settings = get_project_settings(project)
        
        # Get visible and filter columns from settings
        visible_columns = [col for col, conf in settings['columns'].items() if conf.get('show', True)]
        filter_columns = [col for col, conf in settings['columns'].items() if conf.get('filter', False)]
        
        # Filter data to only include visible columns
        filtered_data = []
        for row in data:
            filtered_row = {k: v for k, v in row.items() if k in visible_columns}
            filtered_data.append(filtered_row)
        
        # Get categories for filter columns
        categories = {col: df[col].unique().tolist() for col in filter_columns if col in df.columns}
        
        return jsonify({
            'data': filtered_data,
            'columns': visible_columns,
            'categories': categories,
            'ai_annotators': settings.get('ai_annotators', [])
        })
    return jsonify({'error': 'File not found'})

@app.route('/save_annotations', methods=['POST'])
def save_annotations():
    data = request.json
    project = data['project']
    csv_filename = data['csv_filename']
    annotations = data['annotations']
    
    annotation_data = {
        'manual_annotations': annotations,
        'ai_annotations': data.get('ai_annotations', {}),
        'metadata': {
            'last_updated': pd.Timestamp.now().isoformat(),
            'version': '2.0'
        }
    }
    
    annotation_filename = f"{os.path.splitext(csv_filename)[0]}_annotations.json"
    project_annotations_dir = os.path.join(BASE_DIR, project, ANNOTATIONS_DIR)
    os.makedirs(project_annotations_dir, exist_ok=True)
    
    with open(os.path.join(project_annotations_dir, annotation_filename), 'w') as f:
        json.dump(annotation_data, f)
    
    return jsonify({'message': 'Annotations saved successfully'})

@app.route('/load_annotations/<project>/<csv_filename>')
def load_annotations(project, csv_filename):
    annotation_filename = f"{os.path.splitext(csv_filename)[0]}_annotations.json"
    file_path = os.path.join(BASE_DIR, project, ANNOTATIONS_DIR, annotation_filename)
    
    if os.path.exists(file_path):
        with open(file_path, 'r') as f:
            annotation_data = json.load(f)
            
        if isinstance(annotation_data, list):  # Old format
            return jsonify({
                'manual_annotations': annotation_data,
                'ai_annotations': {},
                'metadata': {
                    'last_updated': pd.Timestamp.now().isoformat(),
                    'version': '2.0'
                }
            })
        return jsonify(annotation_data)
    
    return jsonify({
        'manual_annotations': [],
        'ai_annotations': {},
        'metadata': {
            'last_updated': pd.Timestamp.now().isoformat(),
            'version': '2.0'
        }
    })

@app.route('/delete_file', methods=['POST'])
def delete_file():
    data = request.json
    project = data['project']
    filename = data['filename']
    
    csv_path = os.path.join(BASE_DIR, project, filename)
    annotation_path = os.path.join(BASE_DIR, project, ANNOTATIONS_DIR, f"{os.path.splitext(filename)[0]}_annotations.json")
    
    try:
        if os.path.exists(csv_path):
            os.remove(csv_path)
        if os.path.exists(annotation_path):
            os.remove(annotation_path)
        return jsonify({'success': True, 'message': 'File and annotations deleted successfully'})
    except Exception as e:
        return jsonify({'success': False, 'message': f'Error deleting file: {str(e)}'})

if __name__ == '__main__':
    os.makedirs(BASE_DIR, exist_ok=True)
    app.run(debug=True, port=5001)
