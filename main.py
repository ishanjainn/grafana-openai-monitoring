import openai
import grafana_openai_monitoring

openai.api_key = "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"
metrics_username = 1139457
logs_username = 668812
access_token = "glc_eyJvIjoiNjUyOTkyIiwibiI6InNkc2EiLCJrIjoiNGpQODlFYXYwMjExQ3RySzE5UXJIbTNnIiwibSI6eyJyIjoicHJvZC11cy1lYXN0LTAifX0="
logs_url = "https://logs-prod-006.grafana.net/loki/api/v1/push"
metrics_url = "https://influx-prod-13-prod-us-east-0.grafana.net/api/v1/push/influx/write"


# Apply the custom decorator to the OpenAI API function
openai.ChatCompletion.create = grafana_openai_monitoring.chatMonitor(openai.ChatCompletion.create, metrics_url, logs_url, metrics_username, logs_username, access_token)

# Now any call to openai.Completion.create will be automatically tracked
response = openai.ChatCompletion.create(model="gpt-3.5-turbo", max_tokens=10, messages=[{"role": "user", "content": "Hello world"}])
print(response)