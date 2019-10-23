# python-sdk
A Python SDK for interacting with the Team Machine API.

## Usage

### Authentication

In order to authenticate the Python SDK, first go to <https://app.teammachine.io/spaces/api-clients> to download a credentials JSON file
containing a client ID and private key used for authenticating your API client.

### GraphQL queries

```
import json
import teammachine as tm

with open("/path/to/credentials.json") as f:
    credentials = json.load(f)

client = tm.Client(**credentials)
result = client.gql.request("""
query {
    Identity {
        tm_id
        name
    }
}
""")

print(result["data"]["Identity"])
```
