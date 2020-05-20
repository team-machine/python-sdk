To update the schema docs:
```
rm -rf docs/schema
graphidocs -e http://localhost:3003/graphql -o ./docs/schema
```