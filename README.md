# ConsulNS

A PowerDNS Remote Backend that connects to Consul to retrieve DNS records
from both the KV store as well as the Services API. Records can either be static
or with dynamic data composed from the Services API. DNSSEC should be supported.

## Development

This assumes you have a virtual environment running the reuquired Python version.
You can find the minimum required python version in the `pyproject.tonml` file.
Install the package locally with its dependencies, using:

```
$ pip install -e ".[dev,lint]"
```

### Running the client

Then you can use the consulns client (cnsc) with the CLI interface:

```
$ cnsc
```

Note that a running Consul KV server is required to operate cnsc.
You can start an testing instance with the following command:

```
$ consul agent -dev -data-dir=example/consul
```

### Running the daemon

Assuming you have a local Consul instance running, you can run the consulns
daemon (cnsd) and a PowerDNS instance to test actual DNS queries:

```
$ cnsd ./example/consulns.socket
```
In a separate terminal:
```
$ pdns_server --config-dir=example
```
