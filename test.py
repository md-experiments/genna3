from src.llm_calls import call_ollama, js, create_function_call, call_openai, call_dummy, llm_orchestrate
import yaml
import dotenv
import os
dotenv.load_dotenv()
from src.utils_async import ProgressManager, AsyncFunction


txt = "Interest rates in the US and several other countries continued to decline in the third quarter, with 10-year US Treasury yields falling 85 basis points to a low of 3.6%."

model_name, temperature, custom_function = create_function_call(js, array_format=False)
status, response_msg, response, nr_tokens = call_dummy(model_name, txt, custom_function, temperature, 1024)
model_name = 'qwen2.5:0.5b'
#status, response_msg, response, nr_tokens = call_ollama(model_name, txt, custom_function, temperature, 1024)
#print(status, response_msg)
#print(json.loads(json.dumps(response)))
async_analyze = AsyncFunction()
def load_llm_models():
    """Load available LLM models from yaml file."""
    with open('llm_models.yaml', 'r') as f:
        models = yaml.safe_load(f)
    return models
llm_models = load_llm_models()
def async_orchestrate(record):
    txt = record['txt']

    llm_client = 'dummy'
    model_proper_name = llm_models['dummy']['model_name']
    status, response_msg, _, _ = llm_orchestrate(model_proper_name, txt, custom_function, temperature, llm_client)
    return {
        'status': status,
        'response': response_msg,
        'record_id': 1,
        'file': 'file'
    }

def test(text):
    return {
        'status': 'status',
        'response': 'response_msg',
        'record_id': 1,
        'file': 'file'
    }
all_records = [
    {'txt': 'one text'},
    {'txt': 'another text'},
    {'txt': 'yet another text'},
    {'txt': 'one more text'},
    {'txt': 'last text'}
]
#all_records = ['text','text','text','text','text']

def main():
    all_annotations = async_analyze.process_texts(all_records, async_orchestrate, progress_id = '1')

if __name__ == '__main__':
    main()