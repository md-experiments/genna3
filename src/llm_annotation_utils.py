import os
import pandas as pd
from src.llm_calls import create_function_call
from src.logger import logger

def create_text_from_record(record, columns):
    txt = ''
    read_columns = [col for col in columns if columns[col].get('content', False)]
    missing_columns = set(read_columns).difference(set(record.keys()))
    if missing_columns:
        logger.error(f"Record is missing the following columns: {missing_columns}")
        return None
    for col in read_columns:
        if col in record:
            txt += f"{col}: {record[col]}\n"
    return txt

def get_annotator_settings(settings, annotator_id):
    model_name, temperature, custom_function = None, None, None
    for model_settings in settings.get('ai_annotators', []):
        if annotator_id == model_settings['annotator_id']:
            model_name, temperature, custom_function = create_function_call(model_settings, array_format=False)
            break
    return model_name, temperature, custom_function

def create_annotation_records(project_dir, llm_models, annotator_id, settings):
    model_name, temperature, custom_function = get_annotator_settings(settings, annotator_id)
    if not model_name:
        logger.error(f"Annotator ID {annotator_id} not found in settings")
        return []
    all_records = []
    if os.path.exists(project_dir):
        for file in os.listdir(project_dir):
            if file.endswith('.csv'):
                file_path = os.path.join(project_dir, file)
                df = pd.read_csv(file_path).fillna('')
                recs = df.to_dict(orient='records')

                for rec_id, rec in enumerate(recs):
                    txt = create_text_from_record(rec, settings['columns'])
                    if not txt:
                        continue
                    all_records.append({
                        'txt': txt,
                        'file': file.replace('.csv', ''),
                        'id': rec_id,
                        'temperature': temperature,
                        'custom_function': custom_function,
                        'llm_client': llm_models[model_name]['client'],
                        'model_proper_name': llm_models[model_name]['model_name']
                    })
    return all_records


####################################################################################################
# SYNCRONOUS ANNOTATION
####################################################################################################
"""
def annotate_model_sync(project):
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
    model_id = data['annotator_id']
    annotation_status_file = os.path.join(BASE_DIR, project, ANNOTATIONS_DIR, f"{model_id}_annotation_status.json")
    status_update = {'message': f'Starting...', 'status': 'ongoing'}

    if os.path.exists(annotation_status_file):
        with open(annotation_status_file, 'r') as f:
            status = json.load(f)
    else:
        status = {'judges': {model0:{model1: status_update}}} if 'selected_annotators' in data else status_update
    
    update_status(status, status_update, annotation_status_file)
    project_dir = os.path.join(BASE_DIR, project)
    settings = get_project_settings(project)
    llm_models = load_llm_models()
    model_name, temperature, custom_function = None, None, None
    for model_settings in settings.get('ai_annotators', []):
        if data['annotator_id'] == model_settings['annotator_id']:
            model_name, temperature, custom_function = create_function_call(model_settings, array_format=False)
            break
    if not model_name:
        return jsonify({'error': 'Model not found'})
    
    all_records = create_annotation_records(project_dir, settings)
    annotation_results = {}
    for i, record in enumerate(all_records):
        current_file = record['file']

        
        txt = record['txt']
        llm_client = llm_models[model_name]['client']
        model_proper_name = llm_models[model_name]['model_name']
        status, response_msg, _, _ = llm_orchestrate(model_proper_name, txt, custom_function, temperature, llm_client)
        if status == 'error':
            status_update = {'message': f'Error: {response_msg}', 'status': 'error'}
            update_status(status, status_update, annotation_status_file)
            return jsonify({'status': 'error', 'message': response_msg})
        else:
            status_update = {'message': f'{int(100*i/len(all_records))}% complete', 'status': 'ongoing'}
            update_status(status, status_update, annotation_status_file)
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
        #time.sleep(0.25)
    status_update = {'message': f'Completed', 'status': 'completed'}
    update_status(status, status_update, annotation_status_file)
    return jsonify({'status': 'completed'})"""