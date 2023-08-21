import requests
import time

# Function to calculate the cost based on the model, prompt tokens, and sampled tokens
def calculate_cost(model, prompt_tokens, sampled_tokens):
    # Define the pricing information for different models
    prices = {
        "ada": (0.0004, 0.0004),
        "babbage": (0.0005, 0.0005),
        "curie": (0.0020, 0.0020),
        "davinci": (0.0200, 0.0200),
        "gpt-3.5-turbo": (0.002, 0.002),
        "gpt-3.5-turbo-16k": (0.003,0.004),
        "gpt-4": (0.03, 0.06),
        "gpt-gpt-4-32k": (0.06, 0.12),
    }
    
    prompt_price, sampled_price = prices.get(model, (0, 0))
    
    # Calculate the total cost based on prompt and sampled tokens
    cost = (prompt_tokens / 1000) * prompt_price + (sampled_tokens / 1000) * sampled_price
    
    return cost

# Function to send logs to the specified logs URL
def send_logs(logs_url, logs_username, access_token, logs):
    try:
        response = requests.post(logs_url, auth=(logs_username, access_token), json=logs, headers={"Content-Type": "application/json"})
        response.raise_for_status()  # Raise an exception for non-2xx status codes
        return response
    except requests.exceptions.RequestException as e:
        print("Error sending logs:", e)
        print("Response content:", response.content if response else "No response")
        return None

# Function to send metrics to the specified metrics URL
def send_metrics(metrics_url, metrics_username, access_token, metrics):
    try:
        body = '\n'.join(metrics)
        response = requests.post(metrics_url, headers={'Content-Type': 'text/plain'}, data=str(body), auth=(metrics_username, access_token))
        response.raise_for_status()  # Raise an exception for non-2xx status codes
        return response
    except requests.exceptions.RequestException as e:
        print("Error sending metrics:", e)
        print("Response content:", response.content if response else "No response")
        return None

class monitor():
    # Decorator function to monitor chat completion
    def chat(func, metrics_url, logs_url, metrics_username, logs_username, access_token):
        def wrapper(*args, **kwargs):
            start_time = time.time()
            response = func(*args, **kwargs)
            end_time = time.time()
            duration = end_time - start_time

            # Determine prompt and model from args or kwargs
            prompt = args[1] if args and len(args) > 1 and isinstance(args[1], str) else kwargs.get('messages', [{"content": "No prompt provided"}])[0]['content']
            model = args[2] if len(args) > 2 and isinstance(args[2], str) else kwargs.get('model', "No model provided")
            
            # Calculate the cost based on the response's usage
            cost = calculate_cost(model, response.usage.prompt_tokens, response.usage.completion_tokens)
            print(cost)
            
            # Prepare logs to be sent
            logs = {
                "streams": [
                {
                        "stream": {
                            "integration": "openai", 
                            "prompt": prompt, 
                            "model": response.model, 
                            "role": response["choices"][0]['message']["role"],
                            "finish_reason": response["choices"][0]["finish_reason"],
                            "prompt_tokens": str(response.usage.prompt_tokens), 
                            "completion_tokens": str(response.usage.completion_tokens), 
                            "total_tokens": str(response.usage.total_tokens)
                        },
                        "values": [[str(int(time.time()) * 1000000000), response["choices"][0]['message']["content"]]]
                    }
                ]
            }
            
            # Send logs to the specified logs URL
            loki_response = send_logs(logs_url=logs_url, logs_username=logs_username, access_token=access_token, logs=logs)
            
            # Prepare metrics to be sent
            metrics = [
                # Metric to track the number of completion tokens used in the response
                f'openai,integration=openai,source=python,model={response.model} completionTokens={response.usage.completion_tokens}',
                
                # Metric to track the number of prompt tokens used in the response
                f'openai,integration=openai,source=python,model={response.model} promptTokens={response.usage.prompt_tokens}',
                
                # Metric to track the total number of tokens (prompt + completion) used in the response
                f'openai,integration=openai,source=python,model={response.model} totalTokens={response.usage.total_tokens}',
                
                # Metric to track the usage cost based on the model, prompt tokens, and completion tokens
                f'openai,integration=openai,source=python,model={response.model} usageCost={cost}',
                
                # Metric to track the duration of the API request and response cycle
                f'openai,integration=openai,source=python,model={response.model} requestDuration={duration}',
            ]
            
            # Send metrics to the specified metrics URL
            prometheus_response = send_metrics(metrics_url=metrics_url, metrics_username=metrics_username, access_token=access_token, metrics=metrics)
            
            return response
        
        return wrapper