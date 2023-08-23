import openai
from src.ishan_openi_monitoring.monitor import monitor

openai.api_key = "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"
metrics_username = 1139457
logs_username = 668812
access_token = "glc_eyJvIjoiNjUyOTkyIiwibiI6InNkc2EiLCJrIjoiNGpQODlFYXYwMjExQ3RySzE5UXJIbTNnIiwibSI6eyJyIjoicHJvZC11cy1lYXN0LTAifX0="
logs_url = "https://logs-prod-006.grafana.net/loki/api/v1/push"
metrics_url = "https://influx-prod-13-prod-us-east-0.grafana.net/api/v1/push/influx/write"


# Apply the custom decorator to the OpenAI API function
openai.ChatCompletion.create = monitor.chatV2(openai.ChatCompletion.create, metrics_url, logs_url, metrics_username, logs_username, access_token)

# Now any call to openai.Completion.create will be automatically tracked
response = openai.ChatCompletion.create(model="gpt-4", max_tokens=1000, messages=[{"role": "user", "content": "What is it so tough to reach south pole of moon?"}])
print(response)