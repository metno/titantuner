import os
import sys
import argparse
import numpy as np
from bokeh.server.server import Server


import titantuner
import titantuner.source
import titantuner.source.titan
import titantuner.source.frost


def main():
    parser = argparse.ArgumentParser(description='Launches a titantuner server')
    parser.add_argument('-d', help='Directory with data', dest="directory")
    parser.add_argument('-p', type=int, default=8081, dest="port")
    parser.add_argument('--frostid', help="Load data from frost, using this ID")

    args = parser.parse_args()
    run(**vars(args))

def run(directory, port, frostid):
    app_handle = lambda doc: application(doc, directory, frostid)
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

def application(doc, directory, frostid=None):
    if frostid is not None:
        source = titantuner.source.frost.FrostSource(frostid)
    elif directory is None:
        source = titantuner.source.titan.TitanSource(titantuner.source.titan.get_default_data_dir())
    else:
        source = titantuner.source.titan.TitanSource(directory)
    application = titantuner.app.App(source, doc)

if __name__ == "__main__":
    main()
