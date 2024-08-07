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
    parser.add_argument('-d', help='Directories or file patterns containing data', dest="directories_or_patterns", nargs='+')
    parser.add_argument('-p', type=int, default=8081, dest="port")
    parser.add_argument('--frostid', help="Load data from frost, using this ID")
    parser.add_argument('--debug', help="Bokeh server in debug mode",  action="store_true")

    args = parser.parse_args()
    run(**vars(args))

def run(directories_or_patterns, port, frostid, debug):
    app_handle = lambda doc: application(doc, directories_or_patterns, frostid)
    server = Server(
            app_handle,  # list of Bokeh applications
            port=port,
            allow_websocket_origin=[f"localhost:{port}"],
            debug=debug,
        )

    # start timers and services and immediately return
    server.start()
    print(f'Opening Bokeh application on http://localhost:{port}/')
    server.io_loop.add_callback(server.show, "/")
    server.io_loop.start()
    # titantuner.run.main()

def application(doc, directories_or_patterns, frostid=None):
    if frostid is not None:
        source = titantuner.source.FrostSource(frostid)
    elif directories_or_patterns is None:
        source = titantuner.source.TitanSource([titantuner.source.TitanSource.get_default_data_dir()])
    else:
        source = titantuner.source.TitanSource(directories_or_patterns)
    application = titantuner.app.App(source, doc)

if __name__ == "__main__":
    main()
