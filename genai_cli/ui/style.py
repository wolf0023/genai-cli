from prompt_toolkit.styles import Style
from rich.theme import Theme

# Catppuccin color palette for the Mocha flavor.
class Mocha():
    rosewater="#f5e0dc"
    flamingo="#f2cdcd"
    pink="#f5c2e7"
    mauve="#cba6f7"
    red="#f38ba8"
    maroon="#eba0ac"
    peach="#fab387"
    yellow="#f9e2af"
    green="#a6e3a1"
    teal="#94e2d5"
    sky="#89dceb"
    sapphire="#74c7ec"
    blue="#89b4fa"
    lavender="#b4befe"
    text="#cdd6f4"
    subtext1="#bac2de"
    subtext0="#a6adc8"
    overlay2="#9399b2"
    overlay1="#7f849c"
    overlay0="#6c7086"
    surface2="#585b70"
    surface1="#45475a"
    surface0="#313244"
    base="#1e1e2e"
    mantle="#181825"
    crust="#11111b"

# Define a custom style for the chat UI using prompt_toolkit's Style class.
STYLE = Style.from_dict({
    # Main UI components
    "input-field": f"bg:default fg:{Mocha.text}",
    "waiting-indicator": f"bg:default fg:{Mocha.yellow} bold",
    "vi-mode-normal": f"bg:default fg:{Mocha.blue} bold",
    "vi-mode-insert": f"bg:default fg:{Mocha.green} bold",
    "vi-mode-replace": f"bg:default fg:{Mocha.red} bold",
    "model-name-field": f"bg:default fg:{Mocha.yellow} bold",
    "session-title-field": f"bg:default fg:{Mocha.yellow} bold",
    "info-field": f"bg:default fg:{Mocha.blue}",
    "separator": f"bg:default fg:{Mocha.blue}",

    # Completions menu
    'completion-menu': 'bg:default fg:default noinherit',
    'completion-menu.completion.current': 'bg:default fg:ansiblue bold noinherit',
})

# Define a custom style for the Rich library using the Catppuccin palette.
RICH_THEME = Theme({
    "welcome-logo": f"bold {Mocha.blue}",
    "welcome-message": f"bold {Mocha.text}",
    "exit-message": f"bold {Mocha.red}",
    "user-input": f"bold {Mocha.blue} on {Mocha.base}",
    "command-input": f"bold {Mocha.peach} on {Mocha.base}",
    "command-input-decoration": f"bold {Mocha.base}",
    "command-header": f"bold {Mocha.peach}",
    "command-output": f"{Mocha.lavender}",
    "command-output-emphasis": f"bold {Mocha.yellow}",
    "command-list": f"{Mocha.text}",
    "error": f"bold {Mocha.red}",
    # Markdown elements
    "markdown.block_quote": Mocha.maroon,
    "markdown.code": f"{Mocha.green}",
    "markdown.code_block": f"{Mocha.mauve}",
    "markdown.em": "italic",
    "markdown.emph": "italic",
    "markdown.h1": f"bold underline {Mocha.red}",
    "markdown.h1.border": "none",
    "markdown.h2": f"underline {Mocha.peach}",
    "markdown.h3": f"bold {Mocha.yellow}",
    "markdown.h4": f"italic {Mocha.green}",
    "markdown.h5": f"italic {Mocha.teal}",
    "markdown.h6": f"italic {Mocha.sapphire}",
    "markdown.h7": f"italic {Mocha.text}",
    "markdown.hr": Mocha.overlay1,
    "markdown.item": "none",
    "markdown.item.bullet": f"bold {Mocha.sky}",
    "markdown.item.number": Mocha.sky,
    "markdown.link": Mocha.blue,
    "markdown.link_url": f"underline {Mocha.blue}",
    "markdown.list": Mocha.sky,
    "markdown.paragraph": Mocha.text,
    "markdown.s": "strike",
    "markdown.strong": "bold",
    "markdown.table.border": Mocha.sky,
    "markdown.table.header": f"not bold {Mocha.sky}",
    "markdown.text": Mocha.text,
})
