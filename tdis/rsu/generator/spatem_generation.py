import logging
import pathlib
import time

from ctypes import CDLL, c_char_p, c_int, c_void_p, Structure, POINTER

logger = logging.getLogger("SPATEM generator")

class SpatemInfo(Structure):
    _fields_ = [
        ('stationId', c_int),
        ('intersectionId', c_int),
        ('revision', c_int),
        ('intersectionStatus', c_int),
        ('signalGroup', c_int),
        ('eventState', c_int),
        # negative value for indicates that minEndTime will not be part of the SPATEM message
        ('minEndTime', c_int),
        # negative value for indicates that maxEndTime will not be part of the SPATEM message
        # requires minEndTime >= 0
        ('maxEndTime', c_int)
    ]

def periodicallySendSpatem(if_name, sharedSpatemInfo, period_sec=1):
    prepare_socket, generate_and_send_cam, close_socket = _prepareItsFunctions()
    
    socket = prepare_socket(if_name.encode())
    try:
        _enterSpatemLoop(socket, generate_and_send_cam, sharedSpatemInfo, period_sec)
    except KeyboardInterrupt:
        logger.info("Received keyboard interrupt, doing cleanup now")
        close_socket(socket)


def _prepareItsFunctions():
    generator_path = str(pathlib.Path(__file__).parent.absolute())
    its_functions = CDLL(generator_path + "/itsLib.so")

    # Prepare functions
    prepare_socket = its_functions.prepareSocket
    prepare_socket.argtypes = [c_char_p]
    prepare_socket.restype = c_void_p

    generate_and_send_spatem = its_functions.generateAndSendSpatem
    generate_and_send_spatem.argtypes = [c_void_p, POINTER(SpatemInfo)]
    generate_and_send_spatem.restype = c_int

    close_socket = its_functions.closeSocket
    close_socket.argtypes = [c_void_p]

    return prepare_socket, generate_and_send_spatem, close_socket

def _enterSpatemLoop(socket, generate_and_send_spatem, sharedSpatemInfo, period_sec=1):
    while(True):
        start_time = time.time()
        result_send = generate_and_send_spatem(socket, sharedSpatemInfo)
        # if (result_send < 0):
        #     logger.debug("Failed to send SPATEM message") 
        # else:
        #     logger.debug(f"Successfully sent SPATEM message of size {result_send} bytes")
        end_time = time.time()
        time.sleep(max(0, period_sec - (end_time - start_time)))
