# pydantic-settings-utils

## Usage

```python
$$$ cat examples/basic.py
```

```sh
$ uv run examples/basic.py -h
$$$ sh -c "uv run examples/basic.py -h | sed -E 's/\/home\/[^/]*\//\/home\/example\//'"
```

### Subcommand: example-config

```sh
$ uv run examples/basic.py example-config
$$$ uv run examples/basic.py example-config
```

### Subcommand: current-config

```sh
$ uv run examples/basic.py --duration 1d current-config
$$$ uv run examples/basic.py --duration 1d current-config
```

### YAML config file

```sh
$ cat examples/basic.yaml
$$$ cat examples/basic.yaml

$ uv run examples/basic.py -c examples/basic.yaml current-config
$$$ uv run examples/basic.py -c examples/basic.yaml current-config
```

### Subprograms

```python
$$$ cat examples/subprogram.py
```

```sh
$ uv run examples/subprogram.py -h
$$$ uv run examples/subprogram.py -h

$ uv run examples/subprogram.py subprogram -h
$$$ sh -c 'uv run examples/subprogram.py subprogram -h | head -n3'

...
```

## Development

Enable git hooks to format staged code and generate README pre-commit:

```sh
git config core.hooksPath .githooks
```
