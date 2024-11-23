from flask import Flask, render_template, request, jsonify, send_from_directory
import pandas as pd
import json
import os
import yaml
from collections import OrderedDict
import time
from src.utils import log_traceback
app = Flask(__name__)

BASE_DIR = 'data'
ANNOTATIONS_DIR = 'annotations'

def load_llm_models():
    """Load available LLM models from yaml file."""
    with open('llm_models.yaml', 'r') as f:
        models = yaml.safe_load(f)
    return list(models.keys())

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
        json.dump(settings, f, indent=2)

@app.route('/')
def index():
    return render_template('projects.html')

@app.route('/<project>')
def project_view(project):
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
    
    # Get visible columns
    visible_columns = [col for col in columns if settings['columns'][col].get('show', True)]
    
    return render_template('index.html', 
                         project=project,
                         objective=settings.get('objective', ''),
                         columns=columns,
                         visible_columns=visible_columns,
                         column_settings=settings['columns'],
                         models=settings.get('ai_annotators', []))

@app.route('/settings/<project>')
def project_settings(project):
    return render_template('settings.html', project=project)

@app.route('/get_project_settings/<project>')
def get_settings(project):
    settings = get_project_settings(project)
    columns = get_project_columns(project)
    models = load_llm_models()
    
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
                'filter': False,
                'label_type': 'text'  # Default type for labels
            }
    
    return jsonify({
        'settings': settings,
        'columns': columns,
        'available_models': models
    })

@app.route('/save_project_settings/<project>', methods=['POST'])
def save_settings(project):
    settings = request.json
    save_project_settings(project, settings)
    return jsonify({'success': True, 'message': 'Settings saved successfully'})

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
        
        return jsonify({
            'data': filtered_data,
            'columns': visible_columns,
            'column_settings': settings['columns'],
            'ai_annotators': settings.get('ai_annotators', [])
        })
    return jsonify({'error': 'File not found'})

@app.route('/save_annotations/<project>', methods=['POST'])
def save_annotations(project):
    data = request.json
    #project = data['project']
    print(data)
    csv_filename = data['csv_filename']
    annotations = data['manual_annotations']
        
    annotation_filename = f"{os.path.splitext(csv_filename)[0]}_annotations.json"
    project_annotations_dir = os.path.join(BASE_DIR, project, ANNOTATIONS_DIR)
    os.makedirs(project_annotations_dir, exist_ok=True)
    if os.path.exists(os.path.join(project_annotations_dir, annotation_filename)):
        with open(os.path.join(project_annotations_dir, annotation_filename), 'r') as f:
            annotation_data = json.load(f)
    else:
        annotation_data = {
        'manual_annotations': {},
        'ai_annotations': {},
        'metadata': {
            'last_updated': pd.Timestamp.now().isoformat(),
            'version': '2.0'
        }
    }
    row = list(data['manual_annotations'].keys())[0]
    model_id = data['manual_annotations'][row]['model_id']
    field_name = list(data['manual_annotations'][row].keys())[0]
    annotation_data['manual_annotations'][model_id][row][field_name] = data['manual_annotations'][row][field_name]

    with open(os.path.join(project_annotations_dir, annotation_filename), 'w') as f:
            json.dump(annotation_data, f, indent=2)
    
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

@app.route('/annotate/<project>', methods=['POST'])
def annotate_model(project):
    data = request.json
    print(data)
    project_annotations_dir = os.path.join(BASE_DIR, project, ANNOTATIONS_DIR)
    os.makedirs(project_annotations_dir, exist_ok=True)
    #print(data)
    if 'selected_annotators' in data:
        model0 = data['selected_annotators']['first']['id']
        model1 = data['selected_annotators']['second']['id']
    def update_status(status, status_update, annotation_status_file):
        if 'selected_annotators' in data:
            status['judges'].get(model0, {model1: {}})[model1] = status_update
        else:
            status = status_update
        with open(annotation_status_file, 'w') as f:
            json.dump(status, f, indent=2)
    annotation_status_file = os.path.join(BASE_DIR, project, ANNOTATIONS_DIR, f"{data['annotator_id']}_annotation_status.json")
    status_update = {'message': f'Starting...', 'status': 'ongoing'}
    if os.path.exists(annotation_status_file):
        with open(annotation_status_file, 'r') as f:
            status = json.load(f)
    else:
        status = {'judges': {model0:{model1: status_update}}} if 'selected_annotators' in data else status_update
    update_status(status, status_update, annotation_status_file)
    for i in range(10):
        status_update = {'message': f'{int(100*i/10)}% complete', 'status': 'ongoing'}
        update_status(status, status_update, annotation_status_file)
        time.sleep(0.25)
    status_update = {'message': f'Completed', 'status': 'completed'}
    update_status(status, status_update, annotation_status_file)
    return jsonify({'status': 'completed'})

@app.route('/annotation_status/<project>/<annotator_id>')
def annotation_status(project, annotator_id):
    annotation_status_file = os.path.join(BASE_DIR, project, ANNOTATIONS_DIR, f"{annotator_id}_annotation_status.json") 
    if os.path.exists(annotation_status_file):
        with open(annotation_status_file, 'r') as f:
            return jsonify(json.load(f))
    else:
        return jsonify({'message': f'Starting', 'status': 'ongoing'})

@app.route('/annotation_status/<project>/<annotator_id>/<model_id0>/<model_id1>')
def annotation_status_judge(project, annotator_id, model_id0, model_id1):
    annotation_status_file = os.path.join(BASE_DIR, project, ANNOTATIONS_DIR, f"{annotator_id}_annotation_status.json") 
    if os.path.exists(annotation_status_file):
        if ('judges' in json.load(open(annotation_status_file, 'r'))):
            return jsonify(json.load(open(annotation_status_file, 'r'))['judges'][model_id0][model_id1])
        else:
            return jsonify({'message': f'Starting', 'status': 'ongoing'})
    else:
        return jsonify({'message': f'Starting', 'status': 'ongoing'})

@app.route('/scores/<project>/<annotator_id>')
def get_scores(project, annotator_id):
    annotation_status_file = os.path.join(BASE_DIR, project, ANNOTATIONS_DIR, f"{annotator_id}_annotation_scores.json") 
    if os.path.exists(annotation_status_file):
        with open(annotation_status_file, 'r') as f:
            return jsonify(json.load(f))
    return jsonify({'test': 1,'tes2t': 2})

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
