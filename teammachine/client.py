import types
from time import time
from uuid import uuid4

import networkx as nx

import jwt
import requests
from requests.auth import AuthBase

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

    @property
    def slack_channel(self):
        return Query("SlackChannel", self.gql)


class Query:
    def __init__(self, node_type, gql):
        self.node_type = node_type
        self._gql = gql

    def activity(self, start_date, end_date, **kwargs):
        query_params = {"start_date": start_date, "end_date": end_date, **kwargs}
        query_filter = ", ".join(
            f'{name}:"{value}"'
            for name, value in query_params.items()
            if value is not None
        )
        if query_filter:
            query_filter = f"({query_filter})"

        result = self._gql.request(
            f"""
            query {{
                {self.node_type} {{
                    tm_id
                    tm_display_name
                    node_type
                    activity{query_filter} {{
                        tm_id
                        tm_display_name
                        node_type
                        created_at
                        url
                        created_by {{
                            tm_id
                            tm_display_name
                            is_human
                        }}
                        mentions {{
                            tm_id
                            tm_display_name
                            is_human
                        }}
                    }}
                }}
            }}
        """
        )

        return result["data"][self.node_type]


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
                f'{name}:"{value}"'
                for name, value in query_params.items()
                if value is not None
            )
            if query_filter:
                query_filter = f"({query_filter})"

            result = self._gql.request(
                f"""
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
            """
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
