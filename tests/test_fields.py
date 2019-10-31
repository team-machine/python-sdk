import pytest

import teammachine as tm


class TestField:
    def test_default_to_string(self):
        assert str(tm.Field()) == ""

    def test_with_arguments(self):
        assert str(tm.Field().arguments(a=1)) == "(a:1)"

    def test_call(self):
        assert str(tm.Field()(a=1)) == "(a:1)"

    def test_with_multiple_arguments(self):
        field = tm.Field().arguments(a=1, b="2").arguments(c=3)
        assert str(field) == '(a:1, b:"2", c:3)'

    def test_with_object_arguments(self):
        field = tm.Field().arguments(a={"b": "1", "c": 2})
        assert str(field) == '(a:{b:"1", c:2})'

    def test_frequency(self):
        field = tm.Field().arguments(a={"frequency": tm.Frequency("month")})
        assert str(field) == "(a:{frequency:month})"


class TestObjectField:
    def default_fields(self, indent=1):
        return "\n".join(
            "  " * indent + field for field in tm.ObjectField.default_fields
        )

    def test_default_to_string(self):
        field = tm.ObjectField()

        assert str(field) == "{{\n{fields}\n}}".format(fields=self.default_fields())

    def test_with_arguments(self):
        field = tm.ObjectField().arguments(a=1)

        assert str(field) == "(a:1){{\n{fields}\n}}".format(
            fields=self.default_fields()
        )

    def test_call(self):
        assert str(tm.ObjectField()(a=1)) == "(a:1){{\n{fields}\n}}".format(
            fields=self.default_fields()
        )

    def test_with_multiple_arguments(self):
        field = tm.ObjectField().arguments(a=1, b=2).arguments(c=3)

        assert str(field) == "(a:1, b:2, c:3){{\n{fields}\n}}".format(
            fields=self.default_fields()
        )

    def test_multiple_argument_updates(self):
        a = tm.ObjectField().arguments(a=1)
        b = a.arguments(b="2")

        assert a != b
        assert str(a) == "(a:1){{\n{fields}\n}}".format(fields=self.default_fields())
        assert str(b) == '(a:1, b:"2"){{\n{fields}\n}}'.format(
            fields=self.default_fields()
        )

    def test_initialise_fields(self):
        field = tm.ObjectField("a", b=tm.Field(), c=tm.ObjectField())

        expected = "{{\n  a\n  b\n  c{{\n{fields}\n  }}\n}}".format(
            fields=self.default_fields(indent=2)
        )
        assert str(field) == expected

    def test_invalid_fields(self):
        """Fields should have names but allow strings converted into a Field"""
        with pytest.raises(ValueError):
            tm.ObjectField(tm.Field())

    def test_add_fields(self):
        field = tm.ObjectField("a").fields("b", c=tm.ObjectField())

        expected = "{{\n  b\n  a\n  c{{\n{fields}\n  }}\n}}".format(
            fields=self.default_fields(indent=2)
        )
        assert str(field) == expected

    def test_remove_fields(self):
        field = tm.ObjectField("a", "b", "c").fields(b=None, c=None)
        assert str(field) == "{\n  a\n}"

    def test_multiple_field_updates(self):
        a = tm.ObjectField("a")
        b = a.fields("b")

        assert a != b
        assert str(a) == "{\n  a\n}"
        assert str(b) == "{\n  b\n  a\n}"


class TestQuery:
    def test_default_to_string(self):
        assert str(tm.Query()) == "query {\n\n}"

    def test_query(self):
        query = tm.Query(A=tm.ObjectField("a", "b"))

        assert str(query) == "query {\n  A{\n    a\n    b\n  }\n}"
