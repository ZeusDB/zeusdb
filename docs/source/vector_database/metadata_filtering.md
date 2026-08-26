# Metadata Filtering

ZeusDB supports rich metadata with full type fidelity. This means your metadata preserves the original Python data types (integers stay integers, floats stay floats, etc.) and enables powerful filtering capabilities.

## Supported Types

The following Python types are supported for metadata and preserved during filtering and retrieval.

| Type | Python Example | Notes |
|------|----------------|-------|
| **String** | `"Alice"` | Text data, IDs, categories |
| **Integer** | `42`, `2024` | Counts, years, IDs |
| **Float** | `4.5`, `29.99` | Ratings, prices, scores |
| **Boolean** | `True`, `False` | Flags, status indicators |
| **Null** | `None` | Missing/empty values |
| **Array** | `["ai", "science"]` | Tags, categories, lists |
| **Nested Object** | `{"key": "value"}` | Structured data |

Integers and floats compare by magnitude across every operator, so a stored integer `10` matches `{"eq": 10.0}` and `{"gte": 10.0}` alike. Booleans and strings do not cross into numbers.

<br/>

### Filter Operators Reference

A filter is a dict whose keys are field names, and all of them must hold. A field maps either to a plain value, which means equality, or to a dict of operators, all of which must hold. Three reserved keys, `$and`, `$or` and `$not`, compose whole filters rather than naming a field; see [Boolean composition](#boolean-composition).

| Operator | Usage | Example | Description |
|----------|-------|---------|-------------|
| **Direct equality** | `{"field": value}` | `{"author": "Alice"}` | Equality for strings, numbers, booleans, null and arrays |
| `eq` | `{"eq": value}` | `{"source": {"eq": {"kind": "web"}}}` | Equality, including for nested objects |
| `ne` | `{"ne": value}` | `{"author": {"ne": "Alice"}}` | Not equal |
| `gt` | `{"gt": value}` | `{"rating": {"gt": 4.0}}` | Greater than (numeric) |
| `gte` | `{"gte": value}` | `{"year": {"gte": 2024}}` | Greater than or equal (numeric) |
| `lt` | `{"lt": value}` | `{"price": {"lt": 30}}` | Less than (numeric) |
| `lte` | `{"lte": value}` | `{"pages": {"lte": 100}}` | Less than or equal (numeric) |
| `contains` | `{"contains": value}` | `{"tags": {"contains": "ai"}}` | String contains substring or array contains value |
| `startswith` | `{"startswith": value}` | `{"title": {"startswith": "The"}}` | String starts with substring |
| `endswith` | `{"endswith": value}` | `{"file": {"endswith": ".pdf"}}` | String ends with substring |
| `in` | `{"in": [values]}` | `{"lang": {"in": ["en", "es"]}}` | Value is in the provided array |
| `nin` | `{"nin": [values]}` | `{"lang": {"nin": ["en", "es"]}}` | Value is not in the provided array |
| `any` | `{"any": [values]}` | `{"tags": {"any": ["ai", "ml"]}}` | Array field shares at least one element with the provided array |
| `all` | `{"all": [values]}` | `{"tags": {"all": ["ai", "ml"]}}` | Array field holds every element of the provided array |
| `exists` | `{"exists": bool}` | `{"lang": {"exists": False}}` | Whether the record carries the field at all |
| `is_missing` | `{"is_missing": bool}` | `{"lang": {"is_missing": True}}` | The complement of `exists` |
| `is_null` | `{"is_null": bool}` | `{"lang": {"is_null": True}}` | The record carries the field and its value is null |

`any` and `all` exist because a field maps to one condition object, so it cannot carry `contains` twice. They ask their question of one field's array, where `$or` and `$and` compose whole filters across fields. On a field holding a plain value rather than an array, both read it as an array of one.

Four behaviours are worth knowing.

**A record that lacks the field never matches, whatever the operator.** That includes `ne` and `nin`. `{"status": {"ne": "archived"}}` does not match a record with no `status` at all, so a filter for "status is not archived" excludes records that never had a status. `{"lang": {"ne": "en"}}` and `{"lang": {"nin": ["en"]}}` agree, because `nin` against a one-element array means what `ne` means.

**`exists`, `is_missing` and `is_null` ask about the field itself**, so they are the exception to the rule above and each is decided before the value is looked up. A missing field and a stored null are different: `{"lang": None}` stores a null and `{"lang": {"exists": False}}` matches only a record with no `lang` key.

```python
from zeusdb import VectorDatabase

selector = VectorDatabase().create("hnsw", dim=2)
selector.add([
    {"id": "has", "values": [1.0, 0.0], "metadata": {"lang": "en"}},
    {"id": "null", "values": [0.0, 1.0], "metadata": {"lang": None}},
    {"id": "none", "values": [1.0, 1.0], "metadata": {}},
])
found = lambda f: sorted(r["id"] for r in selector.search([1.0, 0.0], filter=f, top_k=9))
print(found({"lang": {"exists": True}}))
print(found({"lang": {"is_missing": True}}))
print(found({"lang": {"is_null": True}}))
print(found({"lang": {"exists": True, "is_null": False}}))
```

*Output*
```text
['has', 'null']
['none']
['null']
['has']
```

Each takes `True` or `False` and anything else raises. `is_null: False` is the complement of `is_null: True`, so it matches a record with no field at all; write "present and not null" as the conjunction above.

**A dict value is always read as operators.** Direct equality against a nested object has no plain form, because the two would be indistinguishable, so write it as `{"source": {"eq": {"kind": "web"}}}`. Writing `{"source": {"kind": "web"}}` raises `ValueError: Unknown filter operation: kind`.

**An unrecognised operator raises `ValueError` before the search runs**, rather than quietly matching nothing.

<br/>

## The filter decides which records are ranked

**A filtered search returns the `top_k` nearest of the records the filter matches.** The traversal admits only matching records, so `top_k` is the page size and nothing else. A filter matching five records at `top_k=5` returns all five, and a filter matching fewer records than `top_k` returns that many. There is no need to raise `top_k` when you filter, and code that did so can stop.

Two paths serve a filter and the index chooses between them per search. At or below 5,000 matching records it scores every record that matched and ranks them, which is exact, and that page is ordered by distance and then by id. Above 5,000 the graph traversal runs instead with the filter tested at every node it reaches, and recall there is the graph's own, measured at 0.96 and above on three real 100,000 record sets.

The same filter language serves `search()`, `count(filter)`, `remove_where(filter)` and `delete(where=...)`; see [Useful Utilities](utilities.md).

<br/>

(boolean-composition)=
## Boolean composition

A filter is a conjunction of its keys. Three reserved keys compose whole filters instead of naming a field.

| Key | Takes | Means |
|-----|-------|-------|
| `$and` | a list of filters | every one of them holds |
| `$or` | a list of filters | at least one of them holds |
| `$not` | one filter | that filter does not hold |

**Precedence.** There is none to remember, because the structure is explicit. A mapping is an AND of everything in it, fields and groups alike, so `{"a": 1, "$or": [...]}` means `a == 1` AND the disjunction. A group's branches are each a whole filter, so a branch carrying two fields conjoins them.

**Nesting.** Groups nest to 10 levels, counting the filter itself as level one. A filter deeper than that raises `ValueError` naming the depth.

**Reserved keys.** Exactly `$and`, `$or` and `$not`. The `$` prefix is not reserved, so a field named `$price` still filters. A field literally named `$or`, `$and` or `$not` cannot be filtered on, and a filter naming it raises `ValueError`.

**The empty cases.** `{"$and": []}` matches every record and `{"$or": []}` matches none, which is what `all` and `any` already do with an empty array.

```python
from zeusdb import VectorDatabase

vdb = VectorDatabase()
composed = vdb.create("hnsw", dim=4, space="l2")
composed.add([
    {"id": "d1", "values": [0.1, 0.1, 0.1, 0.1],
     "metadata": {"lang": "en", "tier": "gold", "year": 2024}},
    {"id": "d2", "values": [0.2, 0.2, 0.2, 0.2],
     "metadata": {"lang": "es", "tier": "free", "year": 2023}},
    {"id": "d3", "values": [0.3, 0.3, 0.3, 0.3],
     "metadata": {"lang": "fr", "tier": "gold", "year": 2026}},
    {"id": "d4", "values": [0.4, 0.4, 0.4, 0.4],
     "metadata": {"tier": "free", "year": 2025}},
])
q = [0.1, 0.1, 0.1, 0.1]


def composed_matches(filter):
    return sorted(hit["id"] for hit in composed.search(vector=q, filter=filter, top_k=10))


# Either language. A flat filter cannot ask this, because one field maps to one
# condition and two conditions on it are conjoined.
print(composed_matches({"$or": [{"lang": "en"}, {"lang": "es"}]}))

# Gold tier, and either recent or English. A branch is a whole filter, so the
# second one carries two fields and conjoins them.
print(composed_matches({"tier": "gold",
                        "$or": [{"year": {"gte": 2026}}, {"lang": "en"}]}))

# Not free tier. This is what `ne` does here, since every record has a tier.
print(composed_matches({"$not": {"tier": "free"}}))

# Records with no lang field at all, which no operator can select.
print(composed_matches({"$not": {"lang": {"all": []}}}))

# None of these, which is Qdrant's must_not over a group.
print(composed_matches({"$not": {"$or": [{"lang": "es"}, {"tier": "gold"}]}}))
```

*Output*
```text
['d1', 'd2']
['d1', 'd3']
['d1', 'd3']
['d4']
['d4']
```

<br/>

## What a filtered search costs

**A filter over a field left out of `indexed_fields` reads every record's metadata**, so it costs a great deal more than an unfiltered search. Declaring the field builds a column and removes that cost, which the next section measures.

Measured on three real 100,000 record sets with no field declared, milliseconds per query, minimum of several passes:

| Records matched | Path | sift, 128d | glove, 100d | dbpedia, 1536d |
| --- | --- | --- | --- | --- |
| no filter | graph | 0.30 | 0.29 | 1.16 |
| 50,000 | graph | 3.2 | 3.7 | 5.0 |
| 10,000 | graph | 18.0 | 27.2 | 31.6 |
| 1,000 | exact | 33.1 | 39.4 | 38.4 |
| 100 | exact | 36.1 | 30.8 | 30.8 |
| 1 | exact | 38.3 | 31.6 | 34.7 |

**Declare the fields you filter on**, because undeclared a filtered search over 100,000 records costs tens of milliseconds where an unfiltered one costs a fraction of one, and it grows in proportion to the record count. Filtering on a field that few records carry does not reduce it, since the walk visits every record either way.

<br/>

(declaring-the-fields-you-filter-on)=
## Declaring the fields you filter on

`create(indexed_fields=[...])` builds a column for each field named, so a filter naming only declared fields is answered from those columns rather than by reading every record's metadata. It changes which records come back in no way, only what finding them costs.

```python
from zeusdb import VectorDatabase

catalogue = VectorDatabase().create(
    "hnsw", dim=4, space="l2", indexed_fields=["lang", "tier"]
)
catalogue.add([
    {"id": "c1", "values": [0.1, 0.1, 0.1, 0.1],
     "metadata": {"lang": "en", "tier": "gold", "year": 2024}},
    {"id": "c2", "values": [0.2, 0.2, 0.2, 0.2],
     "metadata": {"lang": "es", "tier": "free", "year": 2023}},
])
query = [0.1, 0.1, 0.1, 0.1]

print(catalogue.indexed_fields)

# Answered from the columns, because every field the filter names is declared.
print([hit["id"] for hit in catalogue.search(vector=query, filter={"tier": "gold"})])

# The same record, found by reading metadata, because year was not declared.
print([hit["id"] for hit in catalogue.search(vector=query, filter={"year": 2023})])
```

*Output*
```text
['lang', 'tier']
['c1']
['c2']
```

The same filter answered both ways, on three real 100,000 record sets, milliseconds per query, minimum of three passes over thirty queries:

| Records matched | Declared | Not declared |
| --- | --- | --- |
| 1 | 0.09 to 0.15 | 28.1 to 73.9 |
| 1,000 | 0.37 to 0.48 | 31.2 to 57.2 |
| 10,000 | 3.5 to 12.6 | 20.5 to 36.9 |
| 50,000 | 0.82 to 4.1 | 3.9 to 15.7 |

**Declare the fields you filter on and leave the rest out.** Up to 32 fields can be declared, each once, and none of the reserved keys. Eight declared fields over 100,000 records cost 6.69 MB, which is 6 percent of what the metadata already costs. A field carrying a distinct value on nearly every record costs 42 bytes a record instead of 4, so declare a document id only if you filter on it.

**A filter naming an undeclared field returns the same records**, finds them by reading metadata rather than from a column, and logs one warning naming the field, at WARNING level, so it is visible on stderr under the default development settings. A filter naming a declared field beside an undeclared one is bounded by the declared branch where that removes at least two thirds of the records. `index.indexed_fields` reads the declaration back and is empty on an index created without it. The declaration is carried in `config.json` and the columns are rebuilt on `load()`, so it survives a save.

<br/>

### Practical Filter Examples

The examples below all run against this index:

```python
from zeusdb import VectorDatabase

vdb = VectorDatabase()
index = vdb.create("hnsw", dim=4, space="l2")
index.add([
    {"id": "doc_1", "values": [0.1, 0.1, 0.1, 0.1], "metadata": {
        "author": "Alice", "rating": 4.5, "year": 2024, "price": 29.99,
        "published": True, "tags": ["ai", "science"], "title": "The Guide",
        "filename": "report.pdf", "lang": "en"}},
    {"id": "doc_2", "values": [0.2, 0.2, 0.2, 0.2], "metadata": {
        "author": "Bob", "rating": 3.0, "year": 2023, "price": 45.00,
        "published": False, "tags": ["cooking"], "title": "A Book",
        "filename": "notes.txt", "lang": "es"}},
    {"id": "doc_3", "values": [0.3, 0.3, 0.3, 0.3], "metadata": {
        "author": "Charlie", "rating": 5.0, "year": 2026, "price": 25.00,
        "published": True, "tags": ["ai"], "title": "Theory",
        "filename": "paper.pdf", "lang": "fr"}},
])
query_embedding = [0.1, 0.1, 0.1, 0.1]

def matched(filter, top_k=10):
    return [hit["id"] for hit in index.search(vector=query_embedding, filter=filter, top_k=top_k)]
```

**Example 1 - The filter chooses what is ranked, so `top_k` is just the page size**

```python
# doc_3 is the furthest of the three from the query, and it is still the only
# thing the filter admits, so it is what a page of one holds
print(matched({"author": "Charlie"}, top_k=1))
print(matched({"author": "Charlie"}, top_k=10))
```

*Output*
```text
['doc_3']
['doc_3']
```

<br />

**Example 2 - Find high-quality recent documents**
```python
print(matched({"published": True, "rating": {"gte": 4.0}, "year": {"gte": 2024}}))
```

*Output*
```text
['doc_1', 'doc_3']
```

<br />

**Example 3 - Find documents by specific authors, or exclude them**
```python
print(matched({"author": {"in": ["Alice", "Bob"]}}))
print(matched({"author": {"nin": ["Alice", "Bob"]}}))
```

*Output*
```text
['doc_1', 'doc_2']
['doc_3']
```

<br />

**Example 4 - Find AI-related content**
```python
print(matched({"tags": {"contains": "ai"}}))
print(matched({"tags": {"any": ["ai", "cooking"]}}))
print(matched({"tags": {"all": ["ai", "science"]}}))
```

*Output*
```text
['doc_1', 'doc_3']
['doc_1', 'doc_2', 'doc_3']
['doc_1']
```

<br />

**Example 5 - Find documents in price range**
```python
print(matched({"price": {"gte": 20.0, "lte": 40.0}}))
```

*Output*
```text
['doc_1', 'doc_3']
```

<br />

**Example 6 - Find documents with specific file types, or a title prefix**
```python
print(matched({"filename": {"endswith": ".pdf"}}))
print(matched({"title": {"startswith": "The"}}))
```

*Output*
```text
['doc_1', 'doc_3']
['doc_1', 'doc_3']
```

<br />

**Example 7 - Exclude an author**
```python
print(matched({"author": {"ne": "Alice"}}))
```

*Output*
```text
['doc_2', 'doc_3']
```

<br />

**Example 8 - Match a whole array**
```python
print(matched({"tags": ["ai"]}))
```

*Output*
```text
['doc_3']
```

<br />

**Example 9 - Either a top rating or a recent year, which needs a disjunction**
```python
print(matched({"$or": [{"rating": {"gte": 5.0}}, {"year": {"gte": 2024}}]}))
```

*Output*
```text
['doc_1', 'doc_3']
```

<br />

**Example 10 - Published, and either English or cheap**
```python
print(matched({"published": True,
               "$or": [{"lang": "en"}, {"price": {"lt": 26.0}}]}))
```

*Output*
```text
['doc_1', 'doc_3']
```

<br />

**Example 11 - Everything except Bob's, including any record with no author at all**
```python
print(matched({"$not": {"author": "Bob"}}))
```

*Output*
```text
['doc_1', 'doc_3']
```


<br/>
