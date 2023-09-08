# NOTE: This has been moved to https://github.com/grafana/grafana-openai-monitoring/tree/main

# OpenAI Monitoring: Monitor OpenAI API Usage with Grafana Cloud

`grafana-openai-monitoring` is a Python library that provides a decorator to monitor chat completions using the OpenAI API. It facilitates sending metrics and logs to Grafana Cloud, allowing you to track and analyze OpenAI API usage and responses.

## Installation
You can install grafana-openai-monitoring using pip:

```bash
pip install grafana-openai-monitoring
```

## Usage

```python
import openai
from grafana_openai_monitoring import monitor

# Set your OpenAI API key
openai.api_key = "YOUR_OPENAI_API_KEY"

# Apply the custom decorator to the OpenAI API function
openai.ChatCompletion.create = monitor.chatV2(
    openai.ChatCompletion.create,
    metrics_url="YOUR_PROMETHEUS_METRICS_URL",  # Example: "https://prometheus.grafana.net/api/prom"
    logs_url="YOUR_LOKI_LOGS_URL",  # Example: "https://logs.example.com/loki/api/v1/push/"
    metrics_username="YOUR_METRICS_USERNAME",  # Example: "123456"
    logs_username="YOUR_LOGS_USERNAME",  # Example: "987654"
    access_token="YOUR_ACCESS_TOKEN"  # Example: "glc_eyasdansdjnaxxxxxxxxxxx"
)

# Now any call to openai.Completion.create will be automatically tracked
response = openai.ChatCompletion.create(model="gpt-4", max_tokens=1, messages=[{"role": "user", "content": "What is Grafana?"}])
print(response)
```

## Configuration
To use the grafana-openai-monitoring library effectively, you need to provide the following information:

- **YOUR_OPENAI_API_KEY**: Replace this with your actual OpenAI API key.
- **YOUR_PROMETHEUS_METRICS_URL**: Replace with the URL with your Prometheus URL.
- **YOUR_LOKI_LOGS_URL**: Replace with the URL where you want to send Loki logs.
- **YOUR_METRICS_USERNAME**: Replace with the username for Prometheus.
- **YOUR_LOGS_USERNAME**: Replace with the username for Loki.
- **YOUR_ACCESS_TOKEN**: Replace with the [Cloud Access Policy token](https://grafana.com/docs/grafana-cloud/account-management/authentication-and-permissions/access-policies/) required for authentication.

After configuring the parameters, the monitored API function will automatically log and track the requests and responses to the specified endpoints.

## Compatibility
Python 3.7.1 and above

## Dependencies
Grafana Cloud
openai
requests
time

## License
This project is licensed under the MIT License - see the [LICENSE](LICESNSE.txt) for details.
