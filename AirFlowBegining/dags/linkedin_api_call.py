import requests
from kafka_stream  import load_data_to_json
import json

url = "https://linkedin-api8.p.rapidapi.com/search-jobs"

querystring = {"keywords":"python","locationId":"113837942","datePosted":"anyTime","sort":"mostRelevant"}

headers = {
	"x-rapidapi-key": "951e69819dmsh02ec868e20d51cap1c661djsn4816dd8168a3",
	"x-rapidapi-host": "linkedin-api8.p.rapidapi.com"
}

response = requests.get(url, headers=headers, params=querystring)

print(response.json()) 

load_data_to_json(response.json(), 'data\linkedin_data.txt')
url = "https://linkedin-data-api.p.rapidapi.com/search-locations"
  
querystring = {"keyword":"ho chi minh"}

headers = {
	"x-rapidapi-key": "951e69819dmsh02ec868e20d51cap1c661djsn4816dd8168a3",
	"x-rapidapi-host": "linkedin-data-api.p.rapidapi.com"
}

# response = requests.get(url, headers=headers, params=querystring)

# print(response.json())