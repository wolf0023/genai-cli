from prompt_toolkit.styles import Style

# Define a custom style for the chat UI using prompt_toolkit's Style class.
STYLE = Style.from_dict({
    # Main UI components
    "input-field": "bg:default fg:ansiwhite",
    "waiting-indicator": "bg:default fg:ansiyellow bold",
    "vi-mode-normal": "bg:default fg:ansiblue bold",
    "vi-mode-insert": "bg:default fg:ansigreen bold",
    "vi-mode-replace": "bg:default fg:ansired bold",
    "info-field": "bg:default fg:ansiwhite",
    "separator": "bg:default fg:ansiblue",

    # Completions menu
    'completion-menu': 'bg:default fg:default noinherit',
    'completion-menu.completion.current': 'bg:default fg:ansiblue bold noinherit',
})

