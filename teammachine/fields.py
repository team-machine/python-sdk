from collections import Mapping

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


def _format_field(name, field):
    if name == field:
        return name
    else:
        return name + str(field)


def _format_fields(fields):
    return "\n".join(_format_field(name, field) for name, field in fields.items())


def _create_object_field(value):
    args = []
    kwargs = {}

    for field in value:
        if isinstance(field, (str, ObjectField)) or field is None:
            args.append(field)
        elif isinstance(field, Mapping):
            kwargs.update(field)
        else:
            raise ValueError(
                "Invalid field: %s. Must be str, dict or subclass of Field" % field
            )
    return ObjectField(*args, **kwargs)


def _create_fields(obj):
    result = {}

    for name, value in obj.items():
        if isinstance(value, (str, ObjectField)) or value is None:
            result[name] = value
        elif isinstance(value, list):
            result[name] = _create_object_field(value)
        else:
            raise ValueError(
                "Invalid field: %s. Must be str, dict or subclass of Field" % value
            )

    return result


class ObjectField:
    default_fields = {"tm_id": "tm_id", "tm_display_name": "tm_display_name"}

    def __init__(self, *fields, **kwargs):
        if not all(isinstance(field, str) for field in fields):
            raise ValueError("fields passed in as *args must be strings")

        fields = {x: x for x in fields}
        fields.update(_create_fields(kwargs))

        if not fields:
            fields = {**self.default_fields}

        self._fields = {k: v for k, v in fields.items() if v is not None}
        self._fields_view = FieldsView(self)
        self._args = {}
        self._args_view = ArgsView(self)

    def __str__(self):
        return self._to_string(self._args, self._fields)

    def _to_string(self, args, fields):
        return "{args} {{\n{fields}\n}}".format(
            args=_format_arguments(args), fields=_format_fields(fields)
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
    def arguments(self):
        return self._args_view

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

    def _to_string(self, args, fields):
        return "query {{\n{fields}\n}}".format(fields=_format_fields(fields))


class IdentityField(ObjectField):
    default_fields = {
        "tm_id": "tm_id",
        "tm_display_name": "tm_display_name",
        "is_human": "is_human",
    }


class EventField(ObjectField):
    default_fields = {
        "tm_id": "tm_id",
        "tm_display_name": "tm_display_name",
        "node_type": "node_type",
        "created_at": "created_at",
        "created_by": IdentityField(),
    }


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
