import os
import sys
import argparse
import numpy as np
from bokeh.server.server import Server


import titantuner


def main():
    parser = argparse.ArgumentParser(description='Launches a titantuner server')
    parser.add_argument('-d', help='Directory with data', dest="directory")
    parser.add_argument('-p', type=int, default=8081, dest="port")

    if len(sys.argv) == 1:
        parser.print_help()
        sys.exit(1)

    args = parser.parse_args()
    run(**vars(args))

def run(directory, port):
    app_handle = lambda doc: application(doc, directory)
    server = Server(
            app_handle,  # list of Bokeh applications
            port=port,
            allow_websocket_origin=[f"localhost:{port}"],
        )

    # start timers and services and immediately return
    server.start()
    print(f'Opening Bokeh application on http://localhost:{port}/')
    server.io_loop.add_callback(server.show, "/")
    server.io_loop.start()
    # titantuner.run.main()

def application(doc, directory):
    if directory is None:
        datasets = titantuner.dataset.load_default()
    else:
        datasets = titantuner.dataset.load(directory)
    application = titantuner.app.App(datasets, doc)

if __name__ == "__main__":
    main()
