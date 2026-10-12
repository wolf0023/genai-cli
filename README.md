# genai-cli
genai-cli is a simple CLI chat tool that uses [LiteLLM](https://github.com/BerriAI/litellm). It allows you to chat via the CLI using the APIs of various providers.

## Getting started

### 1. Install genai-cli

```bash
git clone https://github.com/wolf0023/genai-cli.git
cd genai-cli
pip install .
```

### 2. Configuring the API

You need to set the API as an environment variable, either by placing a `.env` file directly in the project directory or by using a shell.

If using `.env`, the project directory structure will look like this:

```bash
.
├── .env
...
├── LICENSE
├── README.md
├── genai_cli
└── pyproject.toml
```

For further details, please refer to the [LiteLLM documentation](https://docs.litellm.ai/docs/set_keys#environment-variables).

### 3. Execution

With your installed environment (such as venv) active, run the following command:

```
genai-cli
```

There are no specific arguments required.

## Application Configuration

### 1. General Settings

You can modify settings in `~/.config/genai-cli/config.json` (assuming Linux).

Currently, only the `default_model` and `system_prompt` settings are supported. Any other settings specified will not be applied (support for these is planned for future updates).

### 2. Model Configuration

> [!NOTE]
> With the default settings, some model versions may be outdated and no longer supported.

You can configure models via `~/.config/genai-cli/models.json` (assuming Linux).

The syntax is as follows.

```json
{
    "models": {
        "Model name within the application": {
            "model_id": "Model ID supported by LiteLLM",
            "thinking": "low|medium|high|none|null"
        }
    }
}
```

Set `"thinking": null` if the model does not support `reasoning_effort`.

## Important Notes

### Regarding paths to configuration files, etc.

As [platformdirs](https://github.com/tox-dev/platformdirs) is used, the directory locations differ between operating systems.

- Linux
    - Configuration directory: `/home/<you>/.config/genai-cli`
    - Logs and history directory: `/home/<you>/.local/share/genai-cli`
- macOS
    - Configuration directory: `/Users/<you>/Library/Application Support/genai-cli`
    - Logs and history directory: `/Users/<you>/Library/Application Support/genai-cli`

- Windows
    - Configuration directory: `\Users\<username>\AppData\Local\genai-cli\genai-cli`
    - Logs and history directory: `\Users\<username>\AppData\Local\genai-cli\genai-cli`
