import argparse
import logging
import os
import pathlib
import signal
import time

from ctypes import CDLL, c_char_p, c_int, c_void_p

logger = logging.getLogger("CAM generator")

def parseArgs():
    parser = argparse.ArgumentParser()
    parser.add_argument('--interface', '-i',
            default='v2x',
            help='the interface to read messages from. Default: v2x')
    parser.add_argument('--log-file', '-l',
            default='',
            help='the location of the log file. If not specified, stderr is used. Default: stderr is used')
    parser.add_argument('--interval', '-v',
        default=1,
        help='the time in seconds between CAM messages')

    return parser.parse_args()

def prepareItsFunctions():
    generator_path = str(pathlib.Path(__file__).parent.absolute())
    its_functions = CDLL(generator_path + "/itsLib.so")

    # Prepare functions
    prepare_socket = its_functions.prepareSocket
    prepare_socket.argtypes = [c_char_p]
    prepare_socket.restype = c_void_p

    start_cam_service = its_functions.startCamService
    start_cam_service.argtypes = [c_void_p, c_char_p, c_int]
    start_cam_service.restype = c_int

    close_socket = its_functions.closeSocket
    close_socket.argtypes = [c_void_p]

    return prepare_socket, start_cam_service, close_socket

def main():
    args = parseArgs()

    if len(args.log_file) > 0:
        logging.basicConfig(level=logging.DEBUG,
                            format='%(asctime)s %(name)-12s %(levelname)-8s %(message)s',
                            datefmt='%m-%d-%y %H:%M:%S',
                            filename=args.log_file,
                            filemode='w')
    else:
        logging.basicConfig(level=logging.DEBUG,
                            format='%(asctime)s %(name)-12s %(levelname)-8s %(message)s',
                            datefmt='%m-%d-%y %H:%M:%S')

    if "MOBILITY_ID" not in os.environ:
        logger.error("Could not find MOBILITY_ID in environment variables.")
        exit(-1)

    prepare_socket, start_cam_service, close_socket = prepareItsFunctions()
    
    mobility_id = os.environ["MOBILITY_ID"]
    socket = prepare_socket(args.interface.encode())

    pid_cam_service = start_cam_service(socket, mobility_id.encode(), 1)

    print(f"PID CAM SERVICE is {pid_cam_service}")

    try:
        # Sleep or do other tasks, e.g. control the train (autonomous driving)
        time.sleep(10000000)
    except signal.SIGTERM:
        logger.info("Received keyboard interrupt, doing cleanup now")
        os.kill(pid_cam_service, signal.SIGTERM) 
        close_socket(socket)

main()
