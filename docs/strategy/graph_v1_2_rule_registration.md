# GRAPH_CLASSIFICATION_V1_2: prospective rule registration (generic shared identifiers)

> DERIVED RESEARCH VIEW - NOT INDEPENDENT EVIDENCE - NO RESEARCH AUTHORITY

**Registered 2026-10-22 on branch `graph-pilot-r4-readiness`, before any holdout fixture for this rule was written.** The rule, its register and this evaluation plan are committed first. The holdout fixtures and their truths are written afterwards, in a later commit, and the rule is not changed after the holdout runs. The v1.1 adversarial set is a development set: the rule is neither tuned nor validated on it, and its record is unchanged.

## Owner policy

Generic shared identifiers (regulators, exchanges, generic institutional roles) are insufficient by themselves to establish an economic connection candidate.

## Rule

- **Default unchanged.** `GRAPH_CLASSIFICATION_V1_1` stays the default. Every v1.1 output and frozen record is unchanged.
- **Opt-in.** `GRAPH_CLASSIFICATION_V1_2` applies per graph (`connections.use_rules`), or per V2 packet snapshot (`pilot snapshot --classification GRAPH_CLASSIFICATION_V1_2`). The snapshot pins the register by hash.

Under V1_2, for any result with an `EXACT_ENTITY_ID` basis:

1. **Collect the shared objects.** These are the identified entities behind that basis: the operator's joining objects, and every match of a `shared` result.
2. **Check each one.** An entity is generic when either:
   - its recorded Discovery Lab type is `REGULATOR` or `GEOGRAPHY`; or
   - its identifier matches a prefix (`MIC:` for ISO 10383 exchanges, `ISO3166:` for geographies) or an exact identifier in [`generic_identifiers_v001.json`](graph/generic_identifiers_v001.json).

   Names never decide genericness.
3. **If every one is generic,** `EXACT_ENTITY_ID` does not ground the item. The class is recomputed from the remaining bases:
   - a documented relationship covering the period still grounds;
   - the same document still grounds;
   - requirement or tag bases give a warning;
   - otherwise the item is `UNSUPPORTED_MATCH`, with the reason `GENERIC_SHARED_IDENTIFIER`.
4. **If any shared object is not generic,** the item is classed exactly as in V1_1.
5. **Nothing is lost.** The item keeps all its recorded bases, its suggestion id, which is independent of the rule, and a `generic_identifier` explanation. Nothing is removed from results.

**Known limits, declared before evaluation:**

- A generic institution recorded with an ordinary type and identifier is not recognised unless it is listed in the register: for example, a central bank recorded as `LEGAL_ENTITY` with an LEI.
- A documented relationship with a generic institution still grounds, even when the relationship is economically thin.

## Holdout plan (declared before any holdout fixture exists)

**Fixtures.** A new fixture module, `holdout_v1_2.py`, with fresh campaign ids, entities, identifiers and wording. Nothing is reused from the adversarial or quality fixtures. Truth for each pair is written from the economics alone, before any system runs.

**Planned case categories** (at least one pair each; truths in brackets):

| Category | Truth |
|---|---|
| Two records sharing only a `REGULATOR`-typed authority | TRIVIAL |
| Two records sharing only an exchange MIC | TRIVIAL |
| Two records sharing only a `GEOGRAPHY` entity | TRIVIAL |
| A documented relationship involving a regulator, covering the period | CONNECTED |
| A shared regulator and a shared non-generic product | CONNECTED |
| A non-generic company whose name sounds institutional ("... Authority Holdings"), typed `LISTED_COMPANY` | CONNECTED when the identifier is shared |
| A generic institution recorded as `LEGAL_ENTITY` with an LEI, not in the register | TRIVIAL; an expected V1_2 miss, reported |
| A genuine shared product identifier with no institution involved | CONNECTED |
| The same document cited by two records about one regulator | CONNECTED_NOT_INDEPENDENT |

**Systems.** V1_1, V1_2 and competent structured search (`baseline.structured_search`), on identical inputs.

**Measures** (each per system):

- true positives and false negatives;
- false positives, by category;
- warnings;
- review load (all items shown);
- identity or timing errors.

**Declared reading:**

- V1_2 **supports the policy on this holdout** only if it presents fewer generic-only false positives than V1_1 and adds no false negatives.
- Any added false negative is reported as a rule failure.
- The expected LEI miss is reported as a limitation, not hidden.

**Independence caveat.** The same implementer wrote the rule and will write the holdout. The ordering (rule committed first) and the fresh fixtures reduce, but do not remove, that dependence. This is not an independent or real-world benchmark.
