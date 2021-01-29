from environs import Env

env = Env()
env.read_env()

# vk settings
VK_TOKEN = env.str("VK_TOKEN")
VK_WALL_ID = env.int("VK_WALL_ID")
# telegram settings
TARGET_CHANNEL = env.int("TARGET_CHANNEL")
TEST_CHANNEL = env.int("TEST_CHANNEL", 0)
TG_BOT_TOKEN = env.str("TG_BOT_TOKEN")
TG_ME = env.int("TG_ME")
LOG_CHANNEL = env.int("LOG_CHANNEL", TG_ME)
