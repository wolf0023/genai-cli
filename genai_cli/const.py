from platformdirs import user_config_dir, user_data_dir

# Constants for genai-cli
# Directory paths
CONFIG_DIR = user_config_dir("genai-cli")
HISTORY_DIR = user_data_dir("genai-cli") + "/history"
LOG_DIR = user_data_dir("genai-cli") + "/logs"

# File names
MODELS_FILE = "models.json"
CONFIG_FILE = "config.json"

# Logging configuration
LOG_FORMAT = "[%(asctime)s] [%(levelname)s]: %(message)s"
LOG_TIME_FORMAT = "%Y-%m-%d_%H-%M-%S"

# Other constants
TITLE_MAX_LENGTH = 30
COMMAND_PREFIX = "/"
DEFAULT_SESSION_TITLE = "New Conversation"
SCROLL_AMOUNT = 3 # Number of lines to scroll
FULL_WIDTH_CHAR_SIZE = 2
HALF_WIDTH_CHAR_SIZE = 1
