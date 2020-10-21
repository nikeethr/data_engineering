import os
import configparser


# tsdb config
DIR = os.path.dirname(os.path.abspath(__file__))
CONFIG_PATH = os.path.join(DIR, "stf_tsdb.cfg")
CONFIG = configparser.ConfigParser()
CONFIG.read(CONFIG_PATH)
CONNECTION = "postgres://{user}:{passwd}@{hostname}:{port}/{dbname}".format(
    user=CONFIG["tsdb"]["user"],
    passwd=CONFIG["tsdb"]["passwd"],
    hostname=CONFIG["tsdb"]["hostname"],
    port=CONFIG["tsdb"]["port"],
    dbname=CONFIG["tsdb"]["dbname"]
)
