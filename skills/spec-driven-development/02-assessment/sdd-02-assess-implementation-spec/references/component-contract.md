# Component inspection

Use the component structure in schemas/normalized-requirements.schema.json. Enumerate only identifiable source components. Each property has status, value, reason and evidence. SPECIFIED needs value and evidence. UNSPECIFIED means absent; NOT_APPLICABLE needs a reason. Do not turn absence into non-applicability.

Inspect responsibility, owner, inputs, input_schema, outputs, output_schema, preconditions, postconditions, invariants, dependencies, failure_modes, error_contract, side_effects, state_mutations, acceptance_criteria, test_fixtures and integration_boundaries.

System contract covers data_flow, compatibility, dependency_order, shared_state, concurrency, integration_boundaries, failure_propagation, external_contracts and acceptance_criteria. Build directed producer/consumer edges. Compare types, required fields, error states and versions. Identify cycles, schema conflicts, undeclared mutation and failure propagation. Put missing or conflicting boundaries into integration_gaps with stable G IDs and source evidence or explicit absence. No unspecified dependency may be silently inferred.
