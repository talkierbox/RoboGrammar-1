import requests

url = "http://127.0.0.1:5555/simulate"
payload = {
    "task": "RidgedTerrainTask",
    "grammar_file": "data/designs/grammar_apr30.dot",
    "rule_sequence": [0],
    "jobs": 8,
    "optim": True,
    "episodes": 1, # using multiple episodes causes FCValueEstimator to crash apparently
    "episode_len": 128
}

try:
    response = requests.post(url, json=payload)
    print("Status Code:", response.status_code)
    print("Response:", response.text)
    data = response.json()  # Convert the JSON response into a Python dict
    optimization_result = data["optimization_result"]  # Extract the optimization_result value
    print("Optimization Result:", optimization_result)
except Exception as e:
    print("Oops! Something went wrong:", e)
