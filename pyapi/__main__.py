#
#    Copyright 2023 - Carlos A. <https://github.com/dealfonso>
#
#    Licensed under the Apache License, Version 2.0 (the "License");
#    you may not use this file except in compliance with the License.
#    You may obtain a copy of the License at
#
#        http://www.apache.org/licenses/LICENSE-2.0
#
#    Unless required by applicable law or agreed to in writing, software
#    distributed under the License is distributed on an "AS IS" BASIS,
#    WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#    See the License for the specific language governing permissions and
#    limitations under the License.
#

def main():
    import uvicorn
    import argparse
    import os
    import traceback
    import sys
    from uvicorn.config import LOGGING_CONFIG
    from .version import VERSION, SHORTNAME
    from .debug import p_fatal, p_info, p_log
    import logging

    parser = argparse.ArgumentParser(allow_abbrev=False)

    parser.add_argument("-p", "--port", help="port in which to listen", default=None, type=int, dest="port")
    parser.add_argument("-v", "--verbose", help="verbose", action="store_true", dest="verbose")
    parser.add_argument("-vv", "--verbose-more", help="verbose more", action="store_true", dest="verbose_more")
    parser.add_argument("-i", "--ip", help="ip address in which to listen", default=None, type=str, dest="ip")
    parser.add_argument("-d", "--database-file", help="database file", default=None, type=str, dest="database_file")
    parser.add_argument("--version", action="version", version=VERSION)
    parser.add_argument("-c", "--config", help="configuration file", default=None, type=str, dest="config_file")
    parser.add_argument("-N", "--no-run", help="do not run the server", action="store_true", dest="no_run")
    parser.add_argument("-q", "--quiet", help="suppress console output", action="store_true", dest="quiet")
    parser.add_argument("-l", "--log-file", help="the log file", default=None, type=str, dest="log_file")

    args = parser.parse_args()
    import pyapi.config as config

    # Read the config files
    config_files = [ f"{SHORTNAME}.conf", f"etc/{SHORTNAME}.conf", f"/etc/{SHORTNAME}.conf", f"/etc/{SHORTNAME}/{SHORTNAME}.conf", f"/usr/local/etc/{SHORTNAME}.conf"]

    # If a config file is supplied, use it as the first option
    if args.config_file is not None:
        config_files = [ args.config_file ] + config_files

    # The name of the config file found
    config_file_used = None
    config_file_success = True

    # Now read the config files
    for config_file in config_files:
        if os.path.isfile(config_file):
            config_file_used = config_file
            config_file_success = config.load(config_file)
            break

    # Override commandline options
    if args.verbose:
        config.LOG_LEVEL = "DEBUG"

    if args.verbose_more:
        config.LOG_LEVEL = "TRACE"

    if args.log_file is not None:
        config.LOG_FILE = args.log_file

    if args.quiet:
        config.QUIET = True

    if args.database_file is not None:
        config.DATABASE_FILE = args.database_file

    if args.port is not None:
        config.PORT = args.port

    # If we used a config file, it is now the moment of informing (now that the overridable options are applied)
    if config_file_used is not None:
        if not config_file_success:
            p_fatal(f"Error loading configuration file: {config_file_used}")
        else:
            p_info(f"Loaded configuration file: {config_file_used}")

    if args.ip is not None:
        import ipaddress
        try:
            ipaddress.ip_address(args.ip)
            config.IP_ADDRESS = args.ip
        except:
            p_fatal("Invalid IP address: %s" % args.ip)

    # Now we are configuring uvicorn log system so that it uses our own log system
    #   The mechanism is very simple: we create a filter that will print the log message
    #   using our own log system and then we return False so that the message is not logged
    #   by uvicorn
    class LogFilter(logging.Filter):
        def __init__(self, name: str = "", log = True) -> None:
            super().__init__(name)
            self._log = log

        def filter(self, record):
            if self._log:
                message = record.getMessage()
                p_log(record.levelname, message)

                # If there is an exception (because it is handling it during the logs), we print it
                info = sys.exc_info()
                if info[2] is not None:
                    p_log(record.levelname, "".join(traceback.format_tb(info[2], -5)))
            return config.MUTE_UVICORN_LOGS
        
    LOGGING_CONFIG["filters"] = {
        'filter_default': {
            '()': LogFilter
        },
        'filter_access': {
            '()': LogFilter,
            'log': config.LOG_API_CALLS
        }
    }

    LOGGING_CONFIG["handlers"]["default"]["filters"] = ["filter_default"]
    LOGGING_CONFIG["handlers"]["access"]["filters"] = ["filter_access"]

    if not args.no_run:
        from .api import api
        uvicorn.run(api, host=config.IP_ADDRESS, port=config.PORT, log_config=LOGGING_CONFIG, log_level=config.LOG_LEVEL.lower())

if __name__ == "__main__":
    main()
