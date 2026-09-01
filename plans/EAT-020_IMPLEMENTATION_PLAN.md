# EAT-020 — Remove Palantir integration and record ontology decision

Asana: [EAT-020](https://app.asana.com/1/9789386902387/project/1217790716964797/task/1218037528278102)

Status: complete — [PR #50](https://github.com/carlwelchdesign/earth-atlas-ai/pull/50)

## Outcome

Remove the Palantir SDK, runtime probe, backend projection/package tooling, hosted-product language, and dedicated feasibility artifacts. EchoAtlas remains a standalone deterministic geospatial application built around its validated analysis-bundle contract.

## Ontology decision

Free and open-source options were checked before removing the platform layer:

| Option | What it provides | Fit now |
| --- | --- | --- |
| [RDFLib](https://github.com/RDFLib/rdflib) | Python RDF graphs, serializers, and SPARQL | Best future fit for standards-based interchange, but there is no current RDF/SPARQL requirement. |
| [Oxigraph](https://github.com/oxigraph/oxigraph) | MIT/Apache-2.0 RDF/SPARQL toolkit and persistent graph database | Strong embedded store, but persistence and semantic queries would duplicate the bounded bundle workflow. |
| [Apache Jena](https://jena.apache.org/) | Apache-licensed RDF, OWL, SHACL, GeoSPARQL, inference, and SPARQL services | Capable but introduces a Java service and semantics the product does not use. |
| [NetworkX](https://networkx.org/) | BSD-licensed in-memory graph algorithms | Useful only if EchoAtlas gains an actual graph-analysis problem; it is not an ontology layer. |

Decision: add none. The analysis bundle already supplies stable object identities, typed records, explicit relationships, provenance, and runtime/schema validation. A new ontology dependency would be speculative infrastructure. Revisit RDFLib first only when a concrete requirement appears for standards-based linked-data export, cross-domain semantic queries, reasoning, or interoperability with an external RDF system.

## Implementation

1. Remove the browser OSDK/OAuth probe and its dependencies, state, UI, and tests.
2. Remove the Python Palantir projection/package commands, modules, exports, and tests.
3. Delete dedicated platform-spike documents; retain only a concise superseded decision in the durable decision log and Asana history.
4. Replace active platform-specific boundaries with vendor-neutral portability language.
5. Regenerate dependency locks and run focused tests, full `make check`, build, and secret/reference scans.

## Non-goals

- Deleting Carl's external Foundry account or enrollment resources.
- Adding a replacement graph database without a product requirement.
- Changing the analysis-bundle schema or SAR candidate semantics.
- Deploying Vercel; that is EAT-021.

## Completion evidence

- [x] Dedicated branch and merged PR #50.
- [x] No Palantir/OSDK runtime dependency or application code remains.
- [x] Active documentation records no Palantir product path.
- [x] `make check` passed: 109 backend tests, 74 workbench tests, static analysis, production build, and secret scan.
