from environs import Env

env = Env()
env.read_env()

# vk settings
VK_LOGIN = env.str("VK_LOGIN")
VK_PASS = env.str("VK_PASS")
VK_WALL_ID = env.int("VK_WALL_ID")

# telegram settings
TARGET_CHANNEL = env.int("TARGET_CHANNEL")
TEST_CHANNEL = env.int("TEST_CHANNEL")
TG_BOT_TOKEN = env.str("TG_BOT_TOKEN")
TG_ME = env.int("TG_ME")
