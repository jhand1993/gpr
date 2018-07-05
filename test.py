import json
import requests
authJson = {"auth":{"identity":{"password":{"user":{"name":"jhand1993","password":"N1ceJ@cket"}}}}}

data = json.dumps(authJson)
print(data)

