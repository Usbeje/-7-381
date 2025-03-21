import requests

# The Indodax address you want to check
indodax_address = "0x[D17479ad4946665379F19C67572af384A0C2a883]"

# The Etherscan API key
api_key = "PJM2GWCZVCKGD6R61Y2H4GDS548JVF67WK"

# The Etherscan API endpoint for resolving ENS names
url = f"https://api.etherscan.io/api?module=account&action=txlist&address={indodax_address}&startblock=0&endblock=99999999&sort=asc&apikey={api_key}"

# Send the API request
response = requests.get(url)

# Parse the JSON response
data = response.json()

# Check if the response contains a result
if "result" in data:
    # Extract the identity name from the first transaction
    identity_name = data["result"][0]["ens_name"]
    print(f"Identity name for address {indodax_address} is: {identity_name}")
else:
    print(f"No identity name found for address {indodax_address}")
