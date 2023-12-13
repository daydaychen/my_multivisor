import json
import logging
import os
import random
from http import HTTPStatus

from flask import Response, jsonify, render_template, request, session
from gevent.pywsgi import WSGIServer
from multivisor.multivisor import Multivisor, Supervisor
from multivisor.server.web import Dispatcher, app, get_parser, log
from multivisor.util import sanitize_url


def new_catch_all(path):
    session["exclude"] = request.args.getlist("exclude")
    return render_template("index.html")


def new_data():
    conf = app.multivisor.safe_config
    conf["exclude"] = exclude = session.get("exclude", [])
    if not exclude:
        return jsonify(conf)

    conf = json.loads(json.dumps(conf))
    for detail in conf["supervisors"].values():
        processes_list = list(detail["processes"].keys())
        for proc_name in processes_list:
            short_name = proc_name.split(":")[-1]
            if short_name in exclude:
                detail["processes"].pop(proc_name)

    return jsonify(conf)


app.secret_key = "my_salt"
app.view_functions["catch_all"] = new_catch_all
app.view_functions["data"] = new_data


def is_registered(addr):
    return addr in [s.url for s in app.multivisor.config["supervisors"].values()]


@app.route("/api/admin/supervisor/info", methods=["POST"])
def get_supervisor_info():
    addr = request.form.get("addr")
    if is_registered(addr):
        return Response(status=HTTPStatus.CONFLICT)
    return Response(status=HTTPStatus.NOT_FOUND)


@app.route("/api/admin/register", methods=["POST"])
def register():
    hostname = request.form.get("hostname", "unknown")
    addr = request.form.get("addr")

    if not addr:
        return Response(
            response="form field[addr] is required", status=HTTPStatus.BAD_REQUEST
        )

    if is_registered(addr):
        return Response(
            response=f"{hostname} already exists",
            status=HTTPStatus.CONFLICT,
        )

    hostname = f"{hostname}_{int(random.random() * 1000)}"

    app.multivisor.config["supervisors"][hostname] = Supervisor(hostname, addr)

    return Response(response=f"{hostname} register success", status=HTTPStatus.OK)


def main(args=None):
    parser = get_parser(args)
    options = parser.parse_args(args)

    log_level = getattr(logging, options.log_level.upper())
    log_fmt = "%(levelname)s %(asctime)-15s %(name)s: %(message)s"
    logging.basicConfig(level=log_level, format=log_fmt)

    if not os.path.exists(options.config_file):
        parser.exit(
            status=2, message="configuration file does not exist. Bailing out!\n"
        )

    bind = sanitize_url(options.bind, host="*", port=22000)["url"]

    app.dispatcher = Dispatcher()
    app.multivisor = Multivisor(options)

    if app.multivisor.use_authentication:
        secret_key = os.environ.get("MULTIVISOR_SECRET_KEY")
        if not secret_key:
            raise ValueError(
                '"MULTIVISOR_SECRET_KEY" environmental variable must be set '
                "when authentication is enabled"
            )
        app.secret_key = secret_key

    http_server = WSGIServer(bind, application=app)
    logging.info(f"Start accepting requests, Serving on http://{bind}")
    try:
        http_server.serve_forever()
    except KeyboardInterrupt:
        log.info("Ctrl-C pressed. Bailing out")


if __name__ == "__main__":
    main()
