import os
from ollama import Client
import json
from src.utils import num_tokens_from_string, log_traceback

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
"""
custom_functions:
  - name: themes
    description: "Extract information about the themes discussed in the text"
    parameters:
      properties:
        themes: 
          type: array
          items:
            type: "object"
            properties:
              theme:
                description: This is one of the significant themes discussed from the text. This is the main topic of the entity that is being discussed in the text. For example, if the text discusses revenue, margins or profitability these can be the themese. Other themes may discuss specific products and their performance, for instance "iPad market share" or risks to the business like "supply chain disruption". The themes can be any topic that is a significant part of the discussion or mentioned as very important. The themes can be a single word or a phrase that describes the main topic of the entity being discussed.
                type: string
              theme_category:
                description: 'This is the category of the theme, this can be a general category that the theme falls under. For instance, if the theme is "revenue" or "financial metrics" and "balance sheet performance", the category can be "financials". If the theme is "product launch", the category can be "product". If the theme is "market share" or "market environment", the category can be "market". If the topic is about new research or innovation, the category can be "research_innovation". If the theme is about competition or competitive landscape, the category can be "competition". If the theme is about management or leadership, the category can be "management". If the theme does not fall into any of these categories, the category can be "other".'
                type: string
                enum:
                  - "financials"
                  - "product"
                  - "market"
                  - "strategy"
                  - "operations"
                  - "regulatory"
                  - "research_innovation"
                  - "competition"
                  - "transformation"
                  - "management"
                  - "other"
      required:
        - theme
        - theme_description
        - significant_change
        - future_past
"""

def create_function_call(model_settings, array_format=False):
    model_name = model_settings['model_name']
    function_name = model_settings['name']
    main_prompt = model_settings['prompt']
    temperature = model_settings['temperature']
    assert all([not a in model_name for a in list(', ./\\')])
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
    """
    custom_functions = [{
        'description': main_prompt,
        'name': function_name,
        'parameters': {
            'properties': {
                function_name: {
                    'type': 'array',
                    'items': items
                }
            },
            'required': ls_fields,
            'type': 'object'
        }
        }]"""
    return model_name, temperature, custom_functions

def call_openai(model_name, user_message, custom_functions, temperature, max_tokens=1024):
    from openai import OpenAI
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
    except:
        print('Error in JSON conversion')
        print(log_traceback())
        return None, None, None

    nr_tokens = {
        'completion_tokens': response.usage.completion_tokens,
        'total_tokens': response.usage.total_tokens,
        'prompt_tokens': response.usage.prompt_tokens
    }
    return response_msg, response, nr_tokens

def call_ollama(model_name, user_message, custom_functions, temperature, max_tokens=1024):
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
        #message = response['message']['content']
        #completion_tokens = num_tokens_from_string(message)
    prompt_tokens = num_tokens_from_string(json.dumps(messages))
    nr_tokens = {
        'completion_tokens': completion_tokens,
        'total_tokens': completion_tokens + prompt_tokens,
        'prompt_tokens': prompt_tokens
    }
    return message, response, nr_tokens