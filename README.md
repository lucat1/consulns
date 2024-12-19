TODO

# Development

This assumes you have a virtual environment running the reuquired Python version.
You can find the minimum required python version in the `pyproject.tonml` file.
Install the package locally with its dependencies, using:

```
$ pip install -e ".[dev,lint]"
```

Then, to test the server:

```
$ cnsd
```

Or to test the client:

```
$ cnsc
```
