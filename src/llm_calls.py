import os
import json
from src.utils import num_tokens_from_string, log_traceback
from ollama import Client
import anthropic
from openai import OpenAI
from src.logger import logger
import time
js = {
    'annotator_id': 'Z3B0LTRvLW1pbmktMS1jb21wYW55X2ltcGFjdCx0ZXh0LWZ1dHVyZV9wYXN0LHRleHQtdGhlbWVfbWV0cmljLHRleHQtcGdyZmF6OHR5MGk', 
    'label_prompts': {
        'theme_category': 'This is the category of the theme, this can be a general category that the theme falls under. For instance, if the theme is "revenue" or "financial metrics" and "balance sheet performance", the category can be "financials". If the theme is "product launch", the category can be "product". If the theme is "market share" or "market environment", the category can be "market". If the topic is about new research or innovation, the category can be "research_innovation". If the theme is about competition or competitive landscape, the category can be "competition". If the theme is about management or leadership, the category can be "management". If the theme does not fall into any of these categories, the category can be "other".', 
        'theme': 'This is one of the significant themes discussed from the text. This is the main topic of the entity that is being discussed in the text. For example, if the text discusses revenue, margins or profitability these can be the themese. Other themes may discuss specific products and their performance, for instance "iPad market share" or risks to the business like "supply chain disruption". The themes can be any topic that is a significant part of the discussion or mentioned as very important. The themes can be a single word or a phrase that describes the main topic of the entity being discussed. ENUM: financials, product, market, strategy, operations, regulatory, research_innovation, competition, transformation, management, other'
        }, 
    'label_types': {
        'theme_category': 'text', 
        'theme': 'text', 
        }, 
    'model_name': 'gpt-4o-mini', 
    'name': 'themes-gpt', 
    'prompt': 'You are a very experienced financial analyst. Extract information about the themes discussed in the text', 
    'roles': ['annotator'], 
    'temperature': 1
    }

def llm_orchestrate(model_name, user_message, custom_functions, temperature, llm_client):
    if llm_client == 'ollama':
        return call_ollama(model_name, user_message, custom_functions, temperature)
    elif llm_client == 'openai':
        return call_openai(model_name, user_message, custom_functions, temperature)
    elif llm_client == 'anthropic':
        return call_anthropic(model_name, user_message, custom_functions, temperature)
    elif llm_client == 'dummy':
        return call_dummy(model_name, user_message, custom_functions, temperature)
    else:
        raise ValueError(f"Unknown LLM client {llm_client}")
    
def create_user_message(data_record, content_columns: list):
    user_message = ' '.join([f"{col}: {data_record[col]}" for col in content_columns])
    return user_message

def create_function_call(model_settings, array_format=False):
    model_name = model_settings['model_name']
    function_name = model_settings['name']
    main_prompt = model_settings['prompt']
    temperature = model_settings['temperature']
    items = {
        'type': 'object',
        'properties': {}
    }
    label_prompts = model_settings['label_prompts']
    label_types = model_settings['label_types']
    for prompt, type in zip(label_prompts, label_types):

        assert prompt == type, f"Field prompts: Expect {prompt} and {type} to be the same for {model_name}"
        description = label_prompts[prompt]
        prompt_type = label_types[type]
        type_mapping = {
            'text': 'string',
            'number': 'number',
            'date': 'string',
            'boolean': 'boolean'
        }
        extract_field = {
            'description': description,
            'type': type_mapping[prompt_type]
        }
        if 'ENUM:' in description:
            enum = description.split("ENUM:")[1].strip().split(',')
            enum = [e.strip() for e in enum if len(e.strip())>0]
            if len(enum):
                extract_field['enum'] = enum
                description = description.split("ENUM:")[0].strip()
                extract_field['description'] = description
            
        items['properties'][prompt] = extract_field
    ls_fields = list(label_prompts.keys())
    assert(len(ls_fields))
    
    if array_format:
        items = {
            'properties': {
                function_name: {
                    'type': 'array',
                    'items': items
                }
            }
        }
    custom_functions = [{
        'description': main_prompt,
        'name': function_name,
        'parameters': {
            **items,
            **{'required': ls_fields,
            'type': 'object'}
        }
        }]
    return model_name, temperature, custom_functions

def call_dummy(model_name, user_message, custom_functions, temperature, max_tokens=1024):
    try:
        response_msg = {
            key_name: user_message
            for key_name in custom_functions[0]['parameters']['properties']
        }
        time.sleep(0.25)
        nr_tokens = {
            'completion_tokens': 0,
            'total_tokens': 0,
            'prompt_tokens': 0
        }
    except Exception as e:
        logger.error('Error in Dummy call')
        logger.error(log_traceback())
        return 'error', f'Error Dummy: {e}', None, None
    return 'ok',response_msg, None, nr_tokens

def call_anthropic(model_name, user_message, custom_functions, temperature, max_tokens=1024):
    """ Call the Anthropic API

    Args:
        model_name (str): Name of the model
        user_message (str): The user message
        custom_functions (list): List of custom functions
        temperature (float): Temperature
        max_tokens (int): Maximum tokens

    Returns:
        tuple: Tuple containing the status, response message, response object and number of tokens
    
    """
    #logger.info(f'BEGIN {user_message[:30]}')
    try:
        tools = custom_functions.copy()
        assert(len(tools) == 1)
        if 'parameters' in tools[0]:
            tools[0]['input_schema'] = tools[0]['parameters']
            del tools[0]['parameters']
        tool_name = tools[0]['name']
        client = anthropic.Anthropic(
            # defaults to os.environ.get("ANTHROPIC_API_KEY")
            api_key=os.environ.get("ANTHROPIC_API_KEY"),
        )
        response = client.messages.create(
            #system=f'Use the tool {tool_name} to extract information from the text',
            model=model_name,
            max_tokens=max_tokens,
            tools=tools,
            temperature=temperature,
            messages=[{"role": "user", "content": user_message}]
        )
        
        for content in response.content:
            if content.type == "tool_use" and content.name == tool_name:
                response_msg = content.input
                break
            else:
                response_msg = {}
        nr_tokens = {
            "input_tokens": response.usage.input_tokens,
            "output_tokens": response.usage.output_tokens,
            "total_tokens": response.usage.input_tokens + response.usage.output_tokens
            }
        #logger.info(f'END {user_message[:30]}')
    except Exception as e:
        logger.error('Error in Anthropic call')
        logger.error(log_traceback())
        return 'error', f'Error Anthropic: {e}', None, None
    return 'ok', response_msg, response, nr_tokens

def call_openai(model_name, user_message, custom_functions, temperature, max_tokens=1024):
    try:
        #logger.info(f'BEGIN {user_message[:20]}')
        function_name = custom_functions[0]['name']
        client = OpenAI()
        #try:
        messages = [{'role': 'user', 'content': user_message}]
        response = client.chat.completions.create(
            model = model_name,
            messages = messages,
            functions = custom_functions,
            function_call = {"name": function_name},
            temperature=temperature,
            max_tokens=max_tokens
        )
        response_msg = response.choices[0].message.function_call.arguments
        try:
            response_msg = json.loads(response_msg)
        except Exception as e:
            logger.error('Error in JSON conversion')
            logger.error(log_traceback())
            return 'error', f'OpenAI: Error in JSON conversion {e}', None, None

        nr_tokens = {
            'completion_tokens': response.usage.completion_tokens,
            'total_tokens': response.usage.total_tokens,
            'prompt_tokens': response.usage.prompt_tokens
        }
        #logger.info(f'END {user_message[:20]}')
    except Exception as e:
        logger.error('Error in OpenAI call')
        logger.error(log_traceback())
        return 'error', f'Error OpenAI: {e}', None, None
    return 'ok', response_msg, response, nr_tokens

def call_ollama(model_name, user_message, custom_functions, temperature, max_tokens=1024):
    try:
        client = Client(host=f'{os.environ["OLLAMA_HOST"]}')
        messages = [{'role': 'user', 'content': user_message}]
        response = client.chat(model=model_name, messages=messages,
                    tools=[{
                        'type': 'function',
                        'function': custom_functions[0]
                    }]
                    )
        #print(response['message']['tool_calls'][0]['function']['arguments'])
        try:
            message = response['message']['tool_calls'][0]['function']['arguments']
            completion_tokens = num_tokens_from_string(json.dumps(message))
        except:
            print('Error in JSON conversion')
            print(log_traceback())
            return 'ok', None, response, None
        prompt_tokens = num_tokens_from_string(json.dumps(messages))
        nr_tokens = {
            'completion_tokens': completion_tokens,
            'total_tokens': completion_tokens + prompt_tokens,
            'prompt_tokens': prompt_tokens
        }
    except Exception as e:
        logger.error('Error in Ollama call')
        logger.error(log_traceback())
        return 'error', f'Error Ollama: {e}', None, None
    return 'ok', message, response, nr_tokens