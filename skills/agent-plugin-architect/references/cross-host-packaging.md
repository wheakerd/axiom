# Cross-Host Packaging

Use one shared `skills/` tree when Codex and Claude Code can discover it from
their manifests. Keep both manifest versions synchronized for a release. Leave
other manifest fields and marketplace wrappers unchanged unless the actual
package contract requires a host-specific difference.

For each host, distinguish:

- static package shape and manifest parsing;
- offline host validation;
- authenticated discovery and loading;
- trigger selection and lifecycle behavior;
- model-specific behavior;
- marketplace or portal behavior.

Static parity proves only static parity. It does not prove installation,
activation, host discovery, runtime routing, authentication, marketplace
acceptance, or cross-model compatibility. Prefer Codex-native metadata and
behavior when a portable abstraction would weaken the Codex experience.

Do not install or activate a plugin, contact a marketplace, sign in, publish,
or deploy under this route. Those are separate effects with separate owners
and evidence.
