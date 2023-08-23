"""
grafana-openai-monitoring
-----------

This module provides functions for monitoring chat completions using the OpenAI API.
It facilitates sending metrics and logs to Grafana Cloud, enabling you to track and analyze
API usage and responses.
"""

import time
import requests

# Function to check if all required arguments are provided and modify metrics and logs URLs
def __check(metrics_url, logs_url, metrics_username, logs_username, access_token):
    # Check if all required parameters are provided
    if not all([metrics_url, logs_url, metrics_username, logs_username, access_token]):
        raise ValueError("All parameters (metrics_url, logs_url, metrics_username, "
                         "logs_username, access_token) must be provided")


    # Check if 'api/prom' is present in the metrics URL
    if "api/prom" not in metrics_url:
        raise ValueError("Invalid metrics URL format. It should contain 'api/prom' in the URL.")

    # Convert metrics_url to use the influx line protocol url
    if "prometheus" in metrics_url:
        metrics_url = metrics_url.replace("prometheus", "influx")
        metrics_url = metrics_url.replace("api/prom", "api/v1/push/influx/write")

        # Special case exception for prometheus-us-central1
        if "-us-central1" in metrics_url:
            metrics_url = metrics_url.replace("-us-central1", "-prod-06-prod-us-central-0")

    # Return metrics_url and logs_url without the trailing slash
    return (
        metrics_url[:-1] if metrics_url.endswith('/') else metrics_url,
        logs_url[:-1] if logs_url.endswith('/') else logs_url
    )


# Function to calculate the cost based on the model, prompt tokens, and sampled tokens
def __calculate_cost(model, prompt_tokens, sampled_tokens):
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
def __send_logs(logs_url, logs_username, access_token, logs):
    try:
        response = requests.post(logs_url,
                                 auth=(logs_username, access_token),
                                 json=logs,
                                 headers={"Content-Type": "application/json"},
                                 timeout=60
                                )
        response.raise_for_status()  # Raise an exception for non-2xx status codes
        return response
    except requests.exceptions.RequestException as err:
        raise requests.exceptions.RequestException(f"Error sending Logs: {err}")

# Function to send metrics to the specified metrics URL
def __send_metrics(metrics_url, metrics_username, access_token, metrics):
    try:
        body = '\n'.join(metrics)
        response = requests.post(metrics_url,
                                 headers={'Content-Type': 'text/plain'},
                                 data=str(body),
                                 auth=(metrics_username, access_token),
                                 timeout=60
                            )
        response.raise_for_status()  # Raise an exception for non-2xx status codes
        return response
    except requests.exceptions.RequestException as err:
        raise requests.exceptions.RequestException(f"Error sending Metrics: {err}")

# Decorator function to monitor chat completion
def chat_v2(func, metrics_url, logs_url, metrics_username, logs_username, access_token): # pylint: disable=too-many-arguments
    """
    A decorator function to monitor chat completions using the OpenAI API.

    This decorator wraps an OpenAI API function and enhances it with monitoring
    capabilities by sending metrics and logs to specified endpoints.

    Args:
        func (callable): The OpenAI API function to be monitored.
        metrics_url (str): The URL where Prometheus metrics will be sent.
        logs_url (str): The URL where Loki logs will be sent.
        metrics_username (str): The username for accessing Prometheus metrics.
        logs_username (str): The username for accessing Loki logs.
        access_token (str): The access token required for authentication.

    Returns:
        callable: The decorated function that monitors the API call and sends metrics/logs.

    Note:
        This decorator allows you to provide configuration parameters either as positional
        arguments or as keyword arguments. If using positional arguments, make sure to
        provide at least five arguments in the order specified above.
    """

    metrics_url, logs_url = __check(metrics_url,
                                    logs_url,
                                    metrics_username,
                                    logs_username,
                                    access_token
                            )

    def wrapper(*args, **kwargs):
        start_time = time.time()
        response = func(*args, **kwargs)
        end_time = time.time()
        duration = end_time - start_time

        # Determine prompt and model from args or kwargs
        prompt = (
            args[1] if args and len(args) > 1 and isinstance(args[1], str)
            else kwargs.get('messages', [{"content": "No prompt provided"}])[0]['content']
        )

        model = (
            args[2] if len(args) > 2 and isinstance(args[2], str)
            else kwargs.get('model', "No model provided")
        )

        # Calculate the cost based on the response's usage
        cost = __calculate_cost(model,
                                response.usage.prompt_tokens,
                                response.usage.completion_tokens
                )

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
                    "values": [
                        [
                            str(int(time.time()) * 1000000000),
                            response["choices"][0]['message']["content"]
                        ]
                    ]

                }
            ]
        }

        # Send logs to the specified logs URL
        __send_logs(logs_url=logs_url,
                    logs_username=logs_username,
                    access_token=access_token,
                    logs=logs
        )

        # Prepare metrics to be sent
        metrics = [
            # Metric to track the number of completion tokens used in the response
            f'openai,integration=openai,'
            f'source=python,model={response.model} '
            f'completionTokens={response.usage.completion_tokens}',

            # Metric to track the number of prompt tokens used in the response
            f'openai,integration=openai,'
            f'source=python,model={response.model} '
            f'promptTokens={response.usage.prompt_tokens}',

            # Metric to track the total number of tokens used in the response
            f'openai,integration=openai,'
            f'source=python,model={response.model} '
            f'totalTokens={response.usage.total_tokens}',

            # Metric to track the usage cost based on the model and token usage
            f'openai,integration=openai,'
            f'source=python,model={response.model} '
            f'usageCost={cost}',

            # Metric to track the duration of the API request and response cycle
            f'openai,integration=openai,'
            f'source=python,model={response.model} '
            f'requestDuration={duration}',
        ]


        # Send metrics to the specified metrics URL
        __send_metrics(metrics_url=metrics_url,
                       metrics_username=metrics_username,
                       access_token=access_token,
                       metrics=metrics)

        return response

    return wrapper
