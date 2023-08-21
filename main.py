import openai
from grafana_openai_monitoring import monitor

openai.api_key = "sk-xx"
metrics_username = 1139457
logs_username = 668812
access_token = "glc_eyJvIjoiNjUyOTkyIiwibiI6InNkc2EiLCJrIjoiNGpQODlFYXYwMjExQ3RySzE5UXJIbTNnIiwibSI6eyJyIjoicHJvZC11cy1lYXN0LTAifX0="
logs_url = "https://logs-prod-006.grafana.net/loki/api/v1/push"
metrics_url = "https://influx-prod-13-prod-us-east-0.grafana.net/api/v1/push/influx/write"


# Apply the custom decorator to the OpenAI API function
openai.ChatCompletion.create = monitor.chat(openai.ChatCompletion.create, metrics_url, logs_url, metrics_username, logs_username, access_token)

# Now any call to openai.Completion.create will be automatically tracked
response = openai.ChatCompletion.create(model="gpt-3.5-turbo", max_tokens=100, messages=[{"role": "user", "content": "Grafana is better than DataDog right?"}])
print(response)