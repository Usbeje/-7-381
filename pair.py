import requests

# Replace [ID] with the actual address ID you want to query
address_id = "[0xD17479ad4946665379F19C67572af384A0C2a883]"

# URL for the Indodax API
url = f"https://indodax.com/api/balance/{address_id}"

# Make the API request
response = requests.get(url)

# Check if the request was successful
if response.status_code == 200:
    # Parse the JSON response
    data = response.json()
    
    # Extract the balance information and address name
    balance_data = data["balance"]
    address_name = data["name"]
    
    # Print the balance information and address name
    print(f"Balance Information for Address: {address_name}")
    for currency, balance in balance_data.items():
        print(f"{currency}: {balance}")
else:
    print("Failed to retrieve balance information.")
