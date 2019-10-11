# python-sdk
A Python SDK for interacting with the Team Machine API.

## Usage

### GraphQL queries

```
import teammachine as tm

client_id = "YOUR CLIENT ID"
private_key = "YOUR PRIVATE KEY"

client = tm.Client(client_id, private_key)
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
