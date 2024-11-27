import os
import sys
import argparse
import numpy as np
from bokeh.server.server import Server


import titantuner
import titantuner.source
import titantuner.source.titan
import titantuner.source.frost
import glob
import os

#import ptvsd

# TO DO set the debugger while using the interactive interface
# see https://gist.github.com/kylrth/148f061c1f4126dca2bd73cb9ad33007
# https://discourse.bokeh.org/t/debugging-recommendations/3934/6
# attach to VS Code debugger if this script was run with BOKEH_VS_DEBUG=true
#if os.environ['BOKEH_VS_DEBUG'] == 'true':
#    # 5678 is the default attach port in the VS Code debug configurations
#    print('Waiting for debugger attach')
#    ptvsd.enable_attach(address=('localhost', 5678), redirect_output=True)
#    ptvsd.wait_for_attach()

def validate_path(path):
    """Check if the path is a valid directory or file pattern."""
    if not os.path.isdir(path) and not glob.glob(path):  # If it's a file pattern (e.g., *.txt)
        raise argparse.ArgumentTypeError(f"'{path}' is not a valid directory or file pattern.")

def main():
    parser = argparse.ArgumentParser(description='Launches a titantuner server')
    parser.add_argument('-d', help='Directories or file patterns containing data', dest="directories_or_patterns", nargs='+')
    parser.add_argument('-p', type=int, default=8081, dest="port")
    parser.add_argument('--frostid', help="Load data from frost, using this ID")
    parser.add_argument('--debug', help="Bokeh server in debug mode",  action="store_true")
    # protection against writing for instance -debug, read as -d ebug
    args = parser.parse_args()
    if args.directories_or_patterns:
        for path in args.directories_or_patterns:
            validate_path(path)
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
