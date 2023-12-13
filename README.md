demo

1. Build Docker Image

```bash
$ docker build -t multivisor_fork -f Dockerfile.base .
$ docker build -t multivisor -f Dockerfile.multivisor
$ docker build -t worker -f Dockerfile.supervisord
```

2. Start Multivisor

```bash
$ docker run --rm -it -e MULTIVISOR_ADDR=0.0.0.0:22000 -e MODULE_NAME=multivisor --network host -p 22000:22000 multivisor
```

3. Start Worker

```bash
$ docker run --rm -it -e MULTIVISOR_ADDR=0.0.0.0:22000 -e MODULE_NAME=worker --network host worker
```

4. Open Dasboard in Browser

`http://localhost:22000`

exclude app

`http://localhost:22000/exclude=app_name1&exclude=app_name2`
