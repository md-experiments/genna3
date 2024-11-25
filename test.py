from src.llm_calls import call_ollama, js, create_function_call, call_openai, call_dummy
import json
import dotenv
import os
dotenv.load_dotenv()


txt = "Interest rates in the US and several other countries continued to decline in the third quarter, with 10-year US Treasury yields falling 85 basis points to a low of 3.6%."

model_name, temperature, custom_function = create_function_call(js, array_format=False)
response_msg, response, nr_tokens = call_dummy(model_name, txt, custom_function, temperature, 1024)
#model_name = 'qwen2.5:0.5b'
#response_msg, response, nr_tokens = call_ollama(model_name, txt, custom_function, temperature, 1024)
print(response_msg)
#print(json.loads(json.dumps(response)))