import re
import types
from collections import Mapping
from time import time
from uuid import uuid4

import networkx as nx

import jwt
import requests
from requests.auth import AuthBase

from .fields import NodeField, Query

try:
    import pandas as pd

    has_pandas = True
except ModuleNotFoundError:
    has_pandas = False


QUERY_URL = "https://app-query.teammachine.io/graphql"
AUTHORIZATION_URL = "https://app-svc.teammachine.io/svc/v1/tokens"


class Auth(AuthBase):
    def __init__(self, client_id, private_key, authorization_url=AUTHORIZATION_URL):
        self._client_id = client_id
        self._private_key = private_key
        self._authorization_url = authorization_url
        self._access_token = None

    def __call__(self, r):
        r.headers["Authorization"] = self.get_access_token()
        return r

    def get_access_token(self):
        if not self._access_token or self._expired():
            response = requests.post(
                self._authorization_url,
                params={"grant_type": "client_credentials"},
                json=self._client_assertion(),
            )
            response.raise_for_status()

            self._access_token = response.json()["access_token"]

        return self._access_token

    def _expired(self):
        if not self._access_token:
            return True

        decoded = jwt.decode(self._access_token, verify=False)
        return decoded["exp"] - time() < 30

    def _client_assertion(self):
        claims = {
            "sub": self._client_id,
            "iss": self._client_id,
            "aud": "teammachine",
            "jti": uuid4().hex,
            "exp": int(time() + 60),
        }
        assertion = jwt.encode(claims, self._private_key, algorithm="RS256")

        return {
            "client_assertion_type": "urn:ietf:params:oauth:client-assertion-type:jwt-bearer",
            "client_assertion": assertion.decode("utf-8"),
        }


# TODO: generate from gql schema
_node_types = {
    "slack_channel": "SlackChannel",
    "identity": "Identity",
    "code_repo": "CodeRepo",
    "code_folder": "CodeFolder",
    "code_file": "CodeFile",
    "jira_project": "JiraProject",
    "jira_issue": "JiraIssue",
    "dropbox_folder": "DropboxFolder",
    "dropbox_file": "DropboxFile",
    "work_container": "WorkContainer",
}


class Client:
    def __init__(
        self,
        client_id,
        private_key,
        query_url=QUERY_URL,
        authorization_url=AUTHORIZATION_URL,
    ):
        self._query_url = query_url
        self.auth = Auth(client_id, private_key, authorization_url)

        self.gql = GQL(query_url, self.auth)
        self.networks = Networks(self.gql)

        for k, v in _node_types.items():
            setattr(self, k, ClientQuery(v, self.gql))


class ClientQuery(NodeField):
    def __init__(self, name, gql, *fields, **object_fields):
        self._name = name
        self._gql = gql
        super(ClientQuery, self).__init__(*fields, **object_fields)

    def _clone(self, *args, **kwargs):
        instance = self.__class__(
            self._name, self._gql, *args, **{**self._fields, **kwargs}
        )
        instance._args = self._args
        return instance

    def request(self):
        query = Query(**{self._name: self})
        result = self._gql.request(str(query))
        return QueryResult(result["data"], query)


class GQL:
    def __init__(self, query_url, auth):
        self.query_url = query_url
        self.auth = auth

    def request(self, query):
        response = requests.post(self.query_url, json={"query": query}, auth=self.auth)

        try:
            response.raise_for_status()
        except requests.exceptions.HTTPError:
            raise requests.exceptions.HTTPError(
                response.status_code, response.text, query
            )

        return response.json()


class Networks:
    NETWORKS = {
        "backbone": "backbone",
        "code": "codeNetwork",
        "collaboration": "collaborationNetwork",
        "contribution": "contributionNetwork",
        "conversations": "conversationsNetwork",
        "files": "fileHierarchy",
        "edited_files": "editedFiles",
    }

    def __init__(self, gql):
        self._gql = gql

        for method_name, query_name in self.NETWORKS.items():
            method = types.MethodType(self._wrap_query(method_name, query_name), self)
            setattr(self, method_name, method)

    def _wrap_query(self, method_name, query_name):
        # TODO: get method signature from schema
        def wrapper(self, start_date=None, end_date=None, **kwargs):
            query_params = {"start_date": start_date, "end_date": end_date, **kwargs}
            query_filter = ", ".join(
                '{name}:"{value}"'.format(name=name, value=value)
                for name, value in query_params.items()
                if value is not None
            )
            if query_filter:
                query_filter = "(" + query_filter + ")"

            result = self._gql.request(
                """
                query {{
                    {query_name}{query_filter} {{
                        nodes {{
                            tm_id
                            tm_display_name
                            node_type
                            url
                        }}
                        links {{
                            source
                            target
                            weight
                            type
                        }}
                    }}
                }}
            """.format(
                    query_name=query_name, query_filter=query_filter
                )
            )

            data = result["data"][query_name]
            return Network(data["nodes"], data["links"])

        return wrapper


class Network:
    def __init__(self, nodes, edges):
        self.nodes = nodes
        self.edges = edges

        self.graph = nx.DiGraph()

        for node in self.nodes:
            self.graph.add_node(node["tm_id"], **node)

        for edge in self.edges:
            self.graph.add_edge(
                edge["source"], edge["target"], weight=edge["weight"], type=edge["type"]
            )


class QueryResult(Mapping):
    def __init__(self, data, query):
        self.query = query
        self._data = data

    def __getitem__(self, key):
        return self._data[key]

    def __iter__(self):
        return iter(self._data)

    def __len__(self):
        return len(self._data)

    def __repr__(self):
        return self._data.__repr__()

    def __str__(self):
        return self._data.__str__()

    @property
    def dataframes(self):
        if not has_pandas:
            raise ModuleNotFoundError("Install 'pandas' to construct dataframes")

        if not hasattr(self, "_dataframes"):
            self._dataframes = DataFrames(self._data)

        return self._dataframes


class DataFrames:
    def __init__(self, data):
        self._frames = []
        for k, v in create_dataframes(data).items():
            setattr(self, k, v)
            self._frames.append(k)

    def __repr__(self):
        return "<DataFrames: %s>" % ", ".join(self._frames)


def snake_case(name):
    s1 = re.sub("(.)([A-Z][a-z]+)", r"\1_\2", name)
    return re.sub("([a-z0-9])([A-Z])", r"\1_\2", s1).lower()


def create_dataframes(obj):
    dataframes = {}

    def flatten_obj(obj, parent_key=None):
        def items():
            for i, (key, value) in enumerate(obj.items()):
                key = snake_case(key)

                if isinstance(value, list):
                    df = pd.DataFrame([flatten_obj(x, key) for x in value])

                    if i > 0:
                        columns = df.columns
                        parent_id = obj.get("tm_id", obj.get("id", i))
                        parent_id_key = (parent_key or key) + "_id"
                        df[parent_id_key] = parent_id
                        df = df[[parent_id_key] + list(columns)]

                    df_key = parent_key + "_" + key if parent_key else key

                    if df_key in dataframes:
                        dataframes[df_key] = pd.concat(
                            [dataframes[df_key], df], sort=False
                        ).reindex()
                    else:
                        dataframes[df_key] = df

                elif isinstance(value, dict):
                    for (subkey, subvalue) in flatten_obj(value, key).items():
                        yield (key + "_" + subkey, subvalue)
                else:
                    yield (key, value)

        return dict(items())

    flatten_obj(obj)
    return dataframes
