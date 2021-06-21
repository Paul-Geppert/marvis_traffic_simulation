import argparse
import math
import logging

import pyshark
from pyshark.packet.packet import Packet

from multiprocessing import Process
from multiprocessing.sharedctypes import Value

from .spatem_generation import periodicallySendSpatem, SpatemInfo

MovementPhaseState_permissive_Movement_Allowed = 5
MovementPhaseState_caution_Conflicting_Traffic = 9

# Timeframe to close the level crossing before the train arrives
earliest_time_to_close_lc = 15
latest_time_to_close_lc = 8

# Timeframe to open the level crossing after the train crossed the level crossing
earliest_time_to_open_lc = 7
latest_time_to_open_lc = 15

def parseArgs():
    parser = argparse.ArgumentParser()
    parser.add_argument('--interface', '-i',
            default='v2x',
            help='the interface to read messages from. Default: v2x')
    parser.add_argument('--log-file', '-l',
            default='',
            help='the location of the log file. If not specified, stderr is used. Default: stderr is used')

    return parser.parse_args()

def main():
    class MessageCount:

        def restart_from(self, start):
            self.start = start - 1

        def get_range(self, start, end):
            self.last_value = end - 1
            self.start = start
            while self.start != end:
                yield self.start
                self.start += 1

    message_count = MessageCount()
    message_count_range = message_count.get_range(0, 128)

    def handleV2XMessage(packet):
        cam_type_id = 2

        packet: Packet = packet

        if packet.highest_layer != 'ITS_RAW':
            # logger.info(f"This message is not a ITS message: {packet.highest_layer}")
            return

        message_type_id = packet.its.ItsPduHeader_element.messageID.main_field.int_value
        if message_type_id != cam_type_id:
            # logger.info(f"This message is not of type CAM (but type id {message_type_id})")
            return

        # Do calculations
        rev = next(message_count_range)
        if rev == message_count.last_value:
            message_count.restart_from(0)
        
        # Update shared memory
        sharedSpatemInfo.revision = rev

        logger.info("Handling CAM message")

        # Position is the middle of the front of the ITS station
        longitude = packet.its.CoopAwarenessV1_element.camParameters_element.basicContainer_element.referencePosition_element.longitude.int_value
        latitude = packet.its.CoopAwarenessV1_element.camParameters_element.basicContainer_element.referencePosition_element.latitude.int_value
        speed = packet.its.CoopAwarenessV1_element.camParameters_element.highFrequencyContainer_tree.basicVehicleContainerHighFrequency_element.speed_element.speedValue.int_value
        vehicle_length_centimeter = packet.its.CoopAwarenessV1_element.camParameters_element.highFrequencyContainer_tree.basicVehicleContainerHighFrequency_element.vehicleLength_element.vehicleLengthValue.int_value
        vehicle_length_meter = vehicle_length_centimeter / 10

        distance_to_rsu = math.sqrt(longitude ** 2 + latitude ** 2)
        expected_arrival_time = distance_to_rsu / speed

        # For sake of simplicity, do not use timing (minEndTime and maxEndTime) as defined in the standard
        # (indicating the point in time for the current or next hour when the state changes in 1/10 sec)
        # but use it to indicate, when the state will change (time until change in sec)

        if latitude > 0 and longitude > 0:
            if expected_arrival_time < (earliest_time_to_close_lc + 
                                        latest_time_to_close_lc) / 2:
                logger.info("Level crossing is closed")
                sharedSpatemInfo.eventState = MovementPhaseState_caution_Conflicting_Traffic

                time_to_cross = vehicle_length_meter / speed
                expected_crossing_time = expected_arrival_time + time_to_cross
                sharedSpatemInfo.minEndTime = int(expected_crossing_time + earliest_time_to_open_lc)
                sharedSpatemInfo.maxEndTime = int(expected_crossing_time + latest_time_to_open_lc)

            elif sharedSpatemInfo.eventState == MovementPhaseState_permissive_Movement_Allowed:
                logger.info("Level crossing is open")
                sharedSpatemInfo.minEndTime = max(0, int(expected_arrival_time - earliest_time_to_close_lc))
                sharedSpatemInfo.maxEndTime = int(expected_arrival_time - latest_time_to_close_lc)

        if latitude < 0 and longitude < 0:
            # if positive: train is still crossing the level crossing
            # if negative: train crossed the level crossing and is n meters away from it
            remaining_length_to_cross = vehicle_length_meter - distance_to_rsu
            # if positive: time in which the train is expected to completely cross the level crossing
            # if negative: time that passed since the train completely crossed the level crossing
            expected_crossing_time = remaining_length_to_cross / speed
            
            if expected_crossing_time * -1 > earliest_time_to_open_lc:
                logger.info("Level crossing is open")
                sharedSpatemInfo.eventState = MovementPhaseState_permissive_Movement_Allowed
                sharedSpatemInfo.minEndTime = -1
                sharedSpatemInfo.maxEndTime = -1
            
            else:
                logger.info("Level crossing is closed")
                sharedSpatemInfo.minEndTime = int(expected_crossing_time + earliest_time_to_open_lc)
                sharedSpatemInfo.maxEndTime = int(expected_crossing_time + latest_time_to_open_lc)

    logger = logging.getLogger("RSU")
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
                            
    sharedSpatemInfo = Value(SpatemInfo,
        1234,   # stationId
        5678,   # intersectionId
        0,      # revision
        0,      # intersectionStatus
        5,      # signalGroup
        MovementPhaseState_permissive_Movement_Allowed,      # eventState
        -1,      # minEndTime
        -1,      # maxEndTime
        lock=False
    )

    p = Process(target=periodicallySendSpatem, args=(args.interface, sharedSpatemInfo))
    p.start()

    capture = pyshark.LiveCapture(interface=args.interface, include_raw=True, use_json=True)
    capture.apply_on_packets(handleV2XMessage)
