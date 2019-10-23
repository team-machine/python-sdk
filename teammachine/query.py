class Query:
    def __init__(self, node_type, gql):
        self.node_type = node_type
        self._gql = gql

    def activity(self, start_date, end_date, **kwargs):
        query_params = {"start_date": start_date, "end_date": end_date, **kwargs}
        query_filter = ", ".join(
            '{name}:"{value}"'.format(name=name, value=value)
            for name, value in query_params.items()
            if value is not None
        )
        if query_filter:
            query_filter = "(" + query_filter + ")"

        return self._activity_request(query_filter)

    def _activity_request(self, query_filter):
        result = self._gql.request(
            """
            query {{
                {node_type} {{
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
                    }}
                }}
            }}
        """.format(
                node_type=self.node_type, query_filter=query_filter
            )
        )

        return result["data"][self.node_type]


class SlackQuery(Query):
    def _activity_request(self, query_filter):
        result = self._gql.request(
            """
            query {{
                {node_type} {{
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
        """.format(
                node_type=self.node_type, query_filter=query_filter
            )
        )

        return result["data"][self.node_type]
