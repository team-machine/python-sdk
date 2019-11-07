# python-sdk
A Python SDK for interacting with the Team Machine API.

## Usage

### Authentication

In order to authenticate the Python SDK, first go to <https://app.teammachine.io/spaces/api-clients> to download a credentials JSON file
containing a client ID and private key used for authenticating your API client.

```
import json
import teammachine as tm

with open("/path/to/credentials.json") as f:
    credentials = json.load(f)

client = tm.Client(**credentials)
```

### Queries

Team Machine provides a [GraphQL API](https://graphql.org/) that exposes your company's aggregated data sources. Using GraphQL allows users
to construct flexible queries to answer their specific questions, because no two companies are alike.

See [here](https://htmlpreview.github.io/?https://raw.githubusercontent.com/team-machine/python-sdk/master/docs/schema/index.html) for the API schema documentation.

The API is split into two distinct types of query: node queries and network queries. Node queries allow a user to select a node in the network
and request related data such as commits in a code repository or people working on a Jira project. Network queries return a network of nodes and
links, which show higher level information about the organisation such as collaboration or contributions.

#### Node Queries

Node queries at their simplest will return a list of matching nodes. For example, to get a list of code repositories:

```
result = client.code_repo.request()
```

This will return a `QueryResult` object, which is list of dictionaries that contain `tm_id`, `tm_display_name`, and `node_type`.

Because further analysis of `QueryResults` will often involve Pandas, it's possible to access Pandas a `DataFrame` representation of the result
from the `QueryResult.dataframes` attribute. The names of the dataframes will follow the results of the API e.g. `result.dataframes.code_repo` will
return a `DataFrame` like:

```
   tm_id tm_display_name node_type
0  ghr-a       something  CodeRepo
1  ghr-b  something else  CodeRepo
```


The currently supported top-level node queries are:

- slack_channel
- identity
- code_repo
- code_folder
- code_file
- jira_project
- jira_issue
- dropbox_folder
- dropbox_file
- work_container

##### Query Arguments

Arguments can be passed to the query by calling it or calling the `.arguments` method, e.g. to filter the query to code repositories called "something":

```
query = client.code_repo(name='something')

# equivalent to:
query = client_code_repo.arguments(name='something')
```

##### Query Fields

Additional fields can be requested by calling the `.fields` parameter, e.g. to include the repositories URL:

```
query = client.code_repo.fields('url')
```

You can also request nested objects using an `ObjectField` (or one of it's subclasses: `EventField`, `IdentityField`, `NodeField`), e.g.
to request commits in the code repository:

```
query = client.code_repo.fields(activity=tm.EventField(start_date='2019-01-01'))
```

Because activity is such a commonly requested field node queries include an `activity` method that can be used instead:

```
query = client.code_repo.activity(start_date='2019-01-01')
```

`ObjectFields` are instantiated with the desired fields, and like node queries can be modified with `.arguments` and `.fields` (node queries are in fact `NodeFields` with an additional `.request` conevenience method)

Note that modifying a query will always return a new query so it's easy to create multiple similar queries, e.g.

```
base_query = client.code_repo(name='something')

activity_2018 = base_query.activity(start_date='2018-01-01', end_date='2018-12-31').request()
activity_2019 = base_query.activity(start_date='2019-01-01', end_date='2019-12-31').request()
```


#### GraphQL Queries

Node queries are simply a convenient way to construct GraphQL queries, but in some cases it might be simpler to construct a query as a string and requesting it using `client.gql.request`, e.g. :

```
result = client.gql.request("""
query {
    CodeRepo {
        tm_id
        tm_display_name
        activity(start_date: "2019-01-01") {
            tm_id
            created_at
        }
    }
}
""")
```

Or equivalently using `Query` and field objects instead of a string:

```
result = client.gql.request(tm.Query(CodeRepo=tm.NodeField(
    'tm_id',
    'tm_display_name',
    activity=tm.EventField('tm_id', 'created_at').arguments(start_date='2019-01-01')
)))
```


#### Network Queries

Team Machine provvides some pre-calculated networks for analysis from the API. Supported
networks include:

- backbone
- code
- collaboaration
- contribution
- conversations
- files
- edited_files

Network queries are similar to node queries but return a `NetworkResult` object, which
contains a networkx `DiGraph`

```
import networkx as nx

collaboration = client.networks.collaboration(start_date='2019-01-01').request()
nx.draw(
    collaboration.graph.to_undirected(),
    pos=nx.spring_layout(collaboration.graph),
)
```
