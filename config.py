from environs import Env

env = Env()
env.read_env()

WEBSITE_LOGIN = env.str("WEBSITE_LOGIN")
WEBSITE_PASSWORD = env.str("WEBSITE_PASSWORD")
DB_USER = env.str("DB_USER")
DB_PASS = env.str("DB_PASS")
DB_NAME = env.str("DB_NAME")
DB_HOST = env.str("DB_HOST")
CHROMEDRIVER_PATH = env.str("CHROMEDRIVER_PATH")
