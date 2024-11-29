from flask import Flask, render_template, request, jsonify, send_from_directory
import pandas as pd
import json
import os
import yaml
from collections import OrderedDict
from src.logger import logger
import time
from src.utils import log_traceback, update_nested_dict
from src.llm_calls import create_function_call, llm_orchestrate
from src.llm_annotation_utils import create_annotation_records
from src.utils_async import ProgressManager, AsyncFunction

app = Flask(__name__)

BASE_DIR = 'data'
ANNOTATIONS_DIR = 'annotations'

def load_llm_models():
    """Load available LLM models from yaml file."""
    with open('llm_models.yaml', 'r') as f:
        models = yaml.safe_load(f)
    return models

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
    models = list(load_llm_models().keys())
    
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

def get_annotations(project_annotations_dir, annotation_filename):
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
    return annotation_data

@app.route('/save_annotations/<project>', methods=['POST'])
def save_annotations(project):
    data = request.json
    #project = data['project']
    #print(data)
    csv_filename = data['csv_filename']
    annotations = data['manual_annotations']
        
    annotation_filename = f"{os.path.splitext(csv_filename)[0]}_annotations.json"
    project_annotations_dir = os.path.join(BASE_DIR, project, ANNOTATIONS_DIR)
    annotation_data = get_annotations(project_annotations_dir, annotation_filename)
    model_id = list(data['manual_annotations'].keys())[0]
    row = list(data['manual_annotations'][model_id].keys())[0]
    field_name = list(data['manual_annotations'][model_id][row].keys())[0]
    annotation_data = update_nested_dict(annotation_data, ['manual_annotations',model_id, row, field_name], data['manual_annotations'][model_id][row][field_name])
    
    with open(os.path.join(project_annotations_dir, annotation_filename), 'w') as f:
            json.dump(annotation_data, f, indent=2)
    
    return jsonify({'message': 'Annotations saved successfully'})

@app.route('/load_annotations/<project>/<csv_filename>')
def load_annotations(project, csv_filename):
    annotation_filename = f"{os.path.splitext(csv_filename)[0]}_annotations.json"
    project_annotations_dir = os.path.join(BASE_DIR, project, ANNOTATIONS_DIR)
    annotation_data = get_annotations(project_annotations_dir, annotation_filename)
    return jsonify(annotation_data)

@app.route('/dummy_request', methods=['POST'])
def dummy_request():
    data = request.json
    time.sleep(1)
    return jsonify({'message': data['text'][:10]})

# Initialize spell checker with your function
def async_orchestrate(record):
    txt = record['txt']
    llm_client = record['llm_client']
    model_proper_name = record['model_proper_name']
    temperature = record['temperature']
    custom_function = record['custom_function']
    status, response_msg, _, _ = llm_orchestrate(model_proper_name, txt, custom_function, temperature, llm_client)
    return {
        'status': status,
        'response': response_msg,
        'id': record['id'],
        'file': record['file']
    }

async_analyze = AsyncFunction(max_workers=4)

@app.route('/annotate/<project>', methods=['POST'])
def annotate_model_async(project):
    data = request.json
    print(data)
    project_dir = os.path.join(BASE_DIR, project)
    project_annotations_dir = os.path.join(BASE_DIR, project, ANNOTATIONS_DIR)
    os.makedirs(project_annotations_dir, exist_ok=True)
    #print(data)
    model_id = data['annotator_id']
    task_id = data['annotator_id']
    settings = get_project_settings(project)
    llm_models = load_llm_models()
    if 'selected_annotators' in data:
        model0 = data['selected_annotators']['first']['id']
        model1 = data['selected_annotators']['second']['id']
        field_name = data['selected_annotators']['field_name']
        task_id = f"{model_id}_M0:{model0}_M1:{model1}_FLD:{field_name}"
        #return jsonify({'message': "Judges model vs model not implemented yet",'status': 'error'})
        all_records = create_annotation_records(project_dir, llm_models, annotator_id = data['annotator_id'], 
                                                settings = settings, judges = [model0, model1], field_name = field_name)
    else:
    
        all_records = create_annotation_records(project_dir, llm_models, annotator_id = data['annotator_id'], 
                                                settings = settings)
    if not all_records:
        return jsonify({'error': 'Model not found'})
    all_annotations = async_analyze.process_texts(all_records, async_orchestrate, progress_id = task_id)
    #print(all_annotations)
    annotation_results = {}
    for i, record in enumerate(all_annotations):
        if record['status'] == 'error':
            continue
        current_file = record['file']
        response_msg = record['response']
        if response_msg:
            annotation_results[str(record['id'])] = response_msg
        if i < len(all_records)-1:
            active_file = all_records[i+1]['file']
        else:
            active_file = ''
        if active_file != current_file:
            annotation_data = get_annotations(project_annotations_dir, f"{current_file}_annotations.json")
            annotation_data = update_nested_dict(annotation_data, ['ai_annotations', model_id], annotation_results)
            with open(os.path.join(project_annotations_dir, f"{current_file}_annotations.json"), 'w') as f:
                json.dump(annotation_data, f, indent=2)
            annotation_results = {}
    return jsonify({'status': 'completed'})


@app.route('/annotation_status/<project>/<annotator_id>')
def annotation_status(project, annotator_id):
    progress = async_analyze.get_progress(annotator_id)
    if progress:
        #print(f"data: {json.dumps(progress)}\n\n")
        if (progress['current'] >= progress['total']) and (progress['total'] > 0):
            async_analyze.clean_up_progress(annotator_id)
            return jsonify({'message': 'Completed', 'status': 'completed'})
        return jsonify({'message': f'{progress["percentage"]}% complete', 'status': 'ongoing'})
    return jsonify({'message': 'Waiting...', 'status': 'ongoing'})


@app.route('/annotation_status/<project>/<annotator_id>/<model_id0>/<model_id1>/<field_name>')
def annotation_status_judge(project, annotator_id, model_id0, model_id1, field_name):
    progress_id = f"{annotator_id}_M0:{model_id0}_M1:{model_id1}_FLD:{field_name}"
    progress = async_analyze.get_progress(progress_id)
    #return jsonify({'message': "Judges model vs model not implemented yet",'status': 'error'})
    if progress:
        print(f"data: {json.dumps(progress)}\n\n")
        if (progress['current'] >= progress['total']) and (progress['total'] > 0):
            async_analyze.clean_up_progress(progress_id)
            return jsonify({'message': 'Completed', 'status': 'completed'})
        return jsonify({'message': f'{progress["percentage"]}% complete', 'status': 'ongoing'})
    return jsonify({'message': 'Waiting...', 'status': 'ongoing'})

@app.route('/scores/<project>/<annotator_id>')
def get_scores(project, annotator_id):

    annotation_path = os.path.join(BASE_DIR, project, ANNOTATIONS_DIR) 
    os.makedirs(annotation_path, exist_ok=True)
    annotation_files = [f for f in os.listdir(annotation_path) if f.endswith('_annotations.json')]
    if len(annotation_files) == 0:
        return jsonify({'Scores': 'No annotations yet'})
    scores = {
            'totals': {},
            'correct': {},
            'manual': {}
        }
    for file in annotation_files:
        with open(os.path.join(annotation_path, file), 'r') as f:
            annotation_data = json.load(f)

        if annotator_id in annotation_data['ai_annotations']:
            manual_annotations = annotation_data['manual_annotations'].get(annotator_id, {})
            for record in annotation_data['ai_annotations'][annotator_id]:
                for field in annotation_data['ai_annotations'][annotator_id][record]:
                    scores['totals'][field] = scores['totals'].get(field, 0) + 1
                    if record in manual_annotations and field in manual_annotations[record]:
                        scores['manual'][field] = scores['manual'].get(field, 0) + 1
                        if manual_annotations[record][field]:
                            scores['correct'][field] = scores['correct'].get(field, 0) + 1
    formatted_scores = {}
    for field in scores['totals']:
        correct_score = scores['correct'].get(field,0) / scores['manual'].get(field,0) if scores['manual'].get(field,0) > 0 else 0
        if scores['manual'].get(field,0) == 0:
            formatted_scores[field] = f'{scores["totals"][field]} model, no manual annotations'
        else:
            formatted_scores[field] = f'{correct_score:.2f} ({scores["totals"][field]} model, {scores["manual"].get(field,0)} manual annotations)'

    return jsonify(formatted_scores)

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
    app.run(debug=True, port=40000)
