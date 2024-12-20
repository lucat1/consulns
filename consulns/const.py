from xdg_base_dirs import xdg_data_home

CLICK_CONFIG_CTX_KEY = "config"
CLICK_CONSUL_CTX_KEY = "consul"
CLICK_ZONE_CTX_KEY = "zone"
DEFAULT_CONSUL_PORT = 8500

ZONE_STORE_PATH = xdg_data_home() / "cnsc-zone"

CONSUL_BASE_PATH = "consulns"
CONSUL_PATH_ZONES = f"{CONSUL_BASE_PATH}/zones"
CONSUL_PATH_ZONE = f"{CONSUL_PATH_ZONES}/{{zone}}"
CONSUL_PATH_ZONE_INFO = f"{CONSUL_PATH_ZONE}/info"
CONSUL_PATH_ZONE_STAGING = f"{CONSUL_PATH_ZONE}/staging"
