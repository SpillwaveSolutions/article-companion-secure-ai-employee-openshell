# OpenShell Setup Guide

How to get the examples in this repo running inside NVIDIA OpenShell sandboxes.

## Prerequisites

- macOS (Apple Silicon) or Linux
- Docker Desktop running
- Python 3.11+

## 1. Install OpenShell

```bash
curl -LsSf https://raw.githubusercontent.com/NVIDIA/OpenShell/main/install.sh | sh
```

On macOS this installs via Homebrew and starts a gateway service on port 17670.

Verify:

```bash
openshell --version
openshell doctor check
```

## 2. Fix the JWT Key Issue (macOS Homebrew)

The Homebrew install has a known bug where the gateway's JWT signing keys aren't copied to the runtime directory. Sandboxes will get stuck in `Provisioning` with `no sandbox token source available` in the container logs.

Check if you're affected:

```bash
ls ~/.local/state/openshell/homebrew/tls/jwt/
```

If the `jwt/` directory doesn't exist:

```bash
cp -R /opt/homebrew/var/openshell/tls/jwt ~/.local/state/openshell/homebrew/tls/jwt
brew services restart nvidia/openshell/openshell
```

Verify the fix:

```bash
openshell sandbox create --name smoke-test -- echo "hello from sandbox"
```

You should see `hello from sandbox` printed and the sandbox auto-deleted.

See [NVIDIA/OpenShell#1523](https://github.com/NVIDIA/OpenShell/issues/1523) for details.

## 3. Configure Providers

### Anthropic (for LLM inference)

```bash
openshell provider create --name anthropic --type anthropic --from-existing
```

This reads `ANTHROPIC_API_KEY` from your shell environment. If the key isn't set, export it first:

```bash
export ANTHROPIC_API_KEY="sk-ant-..."
```

### Serper (for Google search in the research assistant)

```bash
openshell provider create --name serper --type generic --credential SERPER_API_KEY="your-key"
```

Get a free API key at [serper.dev](https://serper.dev) (2,500 queries on free tier).

### Verify providers

```bash
openshell provider list
```

Should show `anthropic` and `serper`.

## 4. Configure Inference Routing

The privacy router intercepts LLM calls inside sandboxes at `https://inference.local` and forwards them to the configured backend.

```bash
openshell inference set --provider anthropic --model claude-sonnet-4-20250514
```

Verify:

```bash
openshell inference get
```

Inside a sandbox, agents call `https://inference.local` with `api_key="unused"`. The router strips the dummy key, injects the real Anthropic API key, and rewrites the model field.

## 5. Run the Research Assistant Example

```bash
cd examples/research-assistant
./run.sh
```

This will:
1. Create a sandbox with the `research-policy.yaml` network policy
2. Upload `flow.py` and `entrypoint.sh` into the sandbox
3. Install CrewAI inside the sandbox via `uv`
4. Patch CrewAI's strict tools issue (see Gotchas below)
5. Start the Flow, which asks you for a URL to research
6. Scrape the URL, search Google for competitors, write `competitors.csv`

To retrieve the output:

```bash
openshell sandbox download research-assistant /sandbox/app/competitors.csv .
```

## Policy File Structure

OpenShell policies are YAML files with these sections:

```yaml
version: 1

filesystem_policy:          # STATIC - locked at sandbox creation
  include_workdir: true
  read_only: [/usr, /lib, /etc]
  read_write: [/tmp]

landlock:                   # STATIC
  compatibility: best_effort

process:                    # STATIC
  run_as_user: sandbox
  run_as_group: sandbox

network_policies:           # DYNAMIC - hot-reloadable
  my_policy:
    name: "Human-readable name"
    endpoints:
      - host: api.example.com
        port: 443
        protocol: rest
        enforcement: enforce
        access: read-only    # or read-write, or fine-grained rules
    binaries:
      - path: /sandbox/.uv/python/**/python3*
      - path: /sandbox/.venv/bin/python*
```

Static sections are locked at sandbox creation. Dynamic sections (network_policies) can be updated on a running sandbox with `openshell policy update`.

## Gotchas We Hit

### Binary path mismatch

The sandbox's Python binary resolves through symlinks:

```
/sandbox/.venv/bin/python3 -> /sandbox/.uv/python/cpython-3.13.12-linux-aarch64-gnu/bin/python3.13
```

The version number (`3.13.12`) changes when `uv pip install` updates packages. If your policy lists `/sandbox/.venv/bin/python3`, the supervisor resolves it at sandbox creation time, but a subsequent `uv pip install` can change the underlying path.

**Fix**: Use glob patterns in the `binaries` list:

```yaml
binaries:
  - path: /sandbox/.uv/python/**/python3*
  - path: /sandbox/.venv/bin/python*
```

### CrewAI strict tools + Claude Sonnet 4

CrewAI 1.14.x always sends `strict: true` on Anthropic tool definitions. Claude Sonnet 4 (`claude-sonnet-4-20250514`) doesn't support strict tools, returning:

```
'claude-sonnet-4-20250514' does not support strict tools.
```

**Fix**: The `entrypoint.sh` patches this out at runtime:

```bash
/sandbox/.venv/bin/python -c "
import crewai.llms.providers.anthropic.completion as m
import pathlib
p = pathlib.Path(m.__file__)
src = p.read_text()
src = src.replace('anthropic_tool[\"strict\"] = True', 'pass')
p.write_text(src)
"
```

This is a temporary workaround until CrewAI fixes the issue upstream.

### Upload creates nested directories

`openshell sandbox create --upload /path/to/dir:/sandbox/app` preserves the directory name, creating `/sandbox/app/dirname/`. To upload the *contents* of a directory without nesting, `cd` into the directory and use `.`:

```bash
cd my-dir
openshell sandbox create --upload ".:/sandbox/app" -- ...
```

### Inference router format matching

The inference router only accepts API calls matching the configured provider format:
- `anthropic` provider: accepts `/v1/messages` (Anthropic SDK)
- `openai` provider: accepts `/v1/chat/completions` (OpenAI SDK)

If you configure an Anthropic provider but your agent uses the OpenAI SDK, you get `no compatible inference route available`. Match the SDK to the provider type.

### Provider credential tokens

Inside the sandbox, `ANTHROPIC_API_KEY` is set to a lazy-resolve token like `openshell:resolve:env:v123_ANTHROPIC_API_KEY`. The sandbox supervisor resolves this to the real value at runtime. Direct API calls from Python work because the SDK sends this token in the request header, and the proxy intercepts and replaces it.

However, if you try to use the token value directly (e.g., printing it or passing it to a non-SDK HTTP call), it won't be a valid API key. Always use the SDK or the inference router.

### Deny-by-default is inherent

There's no `deny_default: true` key in OpenShell policies. Everything not explicitly allowed is denied. If your agent gets `403 Forbidden` from the proxy, check `openshell logs <sandbox>` for `DENIED` entries showing which endpoint and binary were rejected.

## Useful Commands

```bash
# List sandboxes
openshell sandbox list

# Stream logs from a sandbox
openshell logs <name> --tail

# SSH into a running sandbox
openshell sandbox connect <name>

# Run a command in a running sandbox
openshell sandbox exec --name <name> -- <command>

# Update network policy on a running sandbox
openshell policy update <name> --add-endpoint host:port:protocol --wait

# View current policy
openshell policy get <name>

# Delete a sandbox
openshell sandbox delete <name>

# Check system health
openshell doctor check

# Launch the terminal UI
openshell term
```

## Further Reading

- [OpenShell GitHub](https://github.com/NVIDIA/OpenShell)
- [OpenShell Documentation](https://docs.nvidia.com/openshell/latest/index.html)
- [Article: Inside Alex's Sandbox](https://spillwave.com/blog/categories/opinion/2026-04-29-hiring-alex/)
