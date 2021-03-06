from collections.abc import Mapping
from enum import Enum

__all__ = [
    "Query",
    "Field",
    "ObjectField",
    "EventField",
    "IdentityField",
    "WorkContainerField",
    "NodeField",
    "NetworkField",
    "Frequency",
]


class Frequency(Enum):
    DAY = "day"
    WEEK = "week"
    MONTH = "month"

    def __str__(self):
        return self.value


def _format_date(value):
    try:
        return value.isoformat()
    except AttributeError:
        return value


def _format_argument(name, value):
    value = _format_date(value)

    if isinstance(value, str):
        value = '"{}"'.format(value)
    elif isinstance(value, bool):
        value = "{}".format("true" if value else "false")
    elif isinstance(value, Mapping):
        args = ", ".join(_format_argument(k, v) for k, v in value.items())
        value = "{%s}" % args

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


def _format_field(name, field, indent=0):
    return "  " * indent + name + field._to_string(indent=indent)


def _format_fields(fields, indent=0):
    return "\n".join(
        _format_field(name, field, indent) for name, field in fields.items()
    )


def _create_fields(obj):
    result = {}

    for name, value in obj.items():
        if isinstance(value, str):
            result[name] = Field()
        elif isinstance(value, Field) or value is None:
            result[name] = value
        else:
            raise ValueError(
                "Invalid field: %s. Must be str, dict or subclass of Field" % value
            )

    return result


class Field:
    def __init__(self):
        self._args = {}
        self._args_view = ArgsView(self)

    def __str__(self):
        return self._to_string()

    def _to_string(self, indent=0):
        return "{args}".format(args=_format_arguments(self._args))

    def __call__(self, **kwargs):
        instance = self._clone()
        instance._args = {**instance._args, **kwargs}
        return instance

    def _clone(self, *args, **kwargs):
        instance = self.__class__()
        instance._args = self._args
        return instance

    @property
    def arguments(self):
        return self._args_view


class ObjectField(Field):
    default_fields = {"tm_id": "tm_id", "tm_display_name": "tm_display_name"}

    def __init__(self, *fields, **kwargs):
        if not all(isinstance(field, str) for field in fields):
            raise ValueError("fields passed in as *args must be strings")

        fields = _create_fields({x: x for x in fields})
        fields.update(_create_fields(kwargs))

        if not fields:
            fields = _create_fields(self.default_fields)

        self._fields = {k: v for k, v in fields.items() if v is not None}
        self._fields_view = FieldsView(self)
        self._args = {}
        self._args_view = ArgsView(self)

    def __str__(self):
        return self._to_string()

    def _to_string(self, indent=0):
        return "{args}{{\n{fields}\n{indent}}}".format(
            args=_format_arguments(self._args),
            fields=_format_fields(self._fields, indent + 1),
            indent="  " * indent,
        )

    def __call__(self, **kwargs):
        instance = self._clone()
        instance._args = {**instance._args, **kwargs}
        return instance

    def _clone(self, *args, **kwargs):
        instance = self.__class__(*args, **{**self._fields, **kwargs})
        instance._args = self._args
        return instance

    @property
    def fields(self):
        return self._fields_view


class FieldView(Mapping):
    def __init__(self, parent_field):
        self._parent = parent_field

    def __iter__(self):
        return iter(self._data)

    def __len__(self):
        return len(self._data)

    def __repr__(self):
        return self._data.__repr__()

    def __str__(self):
        return self._data.__str__()


class ArgsView(FieldView):
    @property
    def _data(self):
        return {**self._parent._args}

    def __getitem__(self, key):
        return self._fields[key]

    def __call__(self, *args, **kwargs):
        return self._parent(*args, **kwargs)


class FieldsView(FieldView):
    @property
    def _data(self):
        return {k: str(v) for k, v in self._parent._fields.items()}

    def __getitem__(self, key):
        return self._data[key]

    def __call__(self, *args, **kwargs):
        return self._parent._clone(*args, **kwargs)


class Query(ObjectField):
    default_fields = {}

    def __call__(self, *args, **kwargs):
        return self

    def _to_string(self, indent=0):
        return "query {{\n{fields}\n}}".format(
            fields=_format_fields(self._fields, indent + 1)
        )


class NodeField(ObjectField):
    default_fields = {
        "tm_id": "tm_id",
        "tm_display_name": "tm_display_name",
        "node_type": "node_type",
    }

    def activity(self, start_date=None, end_date=None, **kwargs):
        return self.fields(
            activity=EventField().arguments(
                start_date=start_date, end_date=end_date, **kwargs
            )
        )

    def activity_count(self, start_date, end_date, **kwargs):
        return self.fields(
            activity_count=ObjectField("count", "date").arguments(
                start_date=start_date, end_date=end_date, **kwargs
            )
        )


class IdentityField(NodeField):
    default_fields = {
        "tm_id": "tm_id",
        "tm_display_name": "tm_display_name",
        "is_human": "is_human",
    }

    def containers(self, start_date=None, end_date=None, **kwargs):
        return self.fields(
            containers=WorkContainerField().arguments(
                start_date=start_date, end_date=end_date, **kwargs
            )
        )


class WorkContainerField(NodeField):
    def contributors(self, start_date=None, end_date=None, only_humans=False, **kwargs):
        return self.fields(
            contributors=IdentityField().arguments(
                start_date=start_date,
                end_date=end_date,
                only_humans=only_humans,
                **kwargs
            )
        )


class EventField(ObjectField):
    default_fields = {
        "tm_id": "tm_id",
        "tm_display_name": "tm_display_name",
        "node_type": "node_type",
        "created_at": "created_at",
        "created_by": IdentityField(),
    }


class NetworkField(ObjectField):
    default_fields = {
        "nodes": NodeField(),
        "links": ObjectField("source", "target", "weight", "type"),
    }
