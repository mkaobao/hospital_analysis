import json

data = json.loads('{"test":true}')

print type(data['test'])