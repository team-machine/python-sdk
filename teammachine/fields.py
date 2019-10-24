__all__ = ["Query", "ObjectField", "EventField", "IdentityField", "NodeField"]


def _format_date(value):
    try:
        return value.isoformat()
    except AttributeError:
        return value


def _format_argument(name, value):
    value = _format_date(value)

    if isinstance(value, str):
        value = '"{}"'.format(value)

    return "{name}:{value}".format(name=name, value=value)


def _format_arguments(args):
    args = ", ".join(
        _format_argument(name, value)
        for name, value in args.items()
        if value is not None
    )

    if args:
        args = "(" + args + ")"

    return args


def _format_fields(fields):
    return "\n".join(str(field) for field in fields)


class ObjectField:
    default_fields = ["tm_id", "tm_display_name"]

    def __init__(self, name, *fields):
        if not isinstance(name, str):
            raise ValueError('"name" must be a string')
        self.name = name

        if not fields:
            fields = self.default_fields[:]

        self._fields = list(fields)
        self._args = {}

    def __str__(self):
        return self._to_string(self.name, self._args, self._fields)

    def _to_string(self, name, args, fields):
        return "{name}{args} {{\n{fields}\n}}".format(
            name=name, args=_format_arguments(args), fields=_format_fields(fields)
        )

    def __call__(self, **kwargs):
        instance = self._clone()
        instance._args = {**instance._args, **kwargs}
        return instance

    def _clone(self):
        instance = self.__class__(self.name, *self._fields)
        instance._args = self._args
        return instance

    @property
    def arguments(self):
        return {**self._args}

    @property
    def fields(self):
        return {getattr(x, "name", x): x for x in self._fields}


class Query(ObjectField):
    default_fields = []

    def __init__(self, *queries):
        self.name = "query"
        self._fields = list(queries)
        self._args = {}


class IdentityField(ObjectField):
    default_fields = ["tm_id", "tm_display_name", "is_human"]


class EventField(ObjectField):
    default_fields = [
        "tm_id",
        "tm_display_name",
        "node_type",
        "created_at",
        IdentityField("created_by"),
    ]


class NodeField(ObjectField):
    default_fields = ["tm_id", "tm_display_name", "node_type"]

    def activity(self, start_date=None, end_date=None, **kwargs):
        field = EventField("activity")(
            start_date=start_date, end_date=end_date, **kwargs
        )

        instance = self._clone()
        instance._fields.append(field)

        return instance
