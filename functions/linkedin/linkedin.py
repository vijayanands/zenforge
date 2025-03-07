import json
import logging
import os

import requests
from dotenv import load_dotenv

load_dotenv()

api_key = os.getenv("PROXYCURL_API_KEY")
headers = {"Authorization": "Bearer " + api_key}
api_endpoint = "https://nubela.co/proxycurl/api/v2/linkedin"


def get_linkedin_profile_json(profile):
    params = {
        "linkedin_profile_url": profile,
        "extra": "include",
        "skills": "include",
        "recommendations": "include",
    }
    response = requests.get(api_endpoint, params=params, headers=headers)
    data = response.json()
    keys_to_remove = ["people_also_viewed", "connections"]
    my_dict = {k: v for k, v in data.items() if k not in keys_to_remove}
    logging.debug(json.dumps(response.json(), indent=4))
    return my_dict
