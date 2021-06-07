import logging
import math
import time
import xmlrpc.client

from ctypes import c_int, Structure

logger = logging.getLogger("Driving controller")

MovementPhaseState_permissive_Movement_Allowed = 5
MovementPhaseState_caution_Conflicting_Traffic = 9

class LevelCrossingState(Structure):
    _fields_ = [
        ('eventState', c_int),
        ('minEndTime', c_int),
        ('maxEndTime', c_int)
    ]

def enterDrivingLoop(mobility_id, sharedLCState, period_sec=1):
    driving_direction = None
    car_is_controlled_by_simulation = False

    while(True):
        start_time = time.time()
        mobility_provider = xmlrpc.client.ServerProxy("http://host:23404/", allow_none=True)

        try:
            # Ask for information
            vehicle_status = mobility_provider.getVehicleDetails(mobility_id)
            is_active = vehicle_status["isVehicleActive"]
            longitude = vehicle_status["position3d"][0]
            latitude = vehicle_status["position3d"][1]
            speed = vehicle_status["speed"]
            
            if is_active:

                if (not driving_direction):
                    # We know the layout of the streets and rail tracks already. The RSU is at (0, 0)
                    # In real-world this information can be acquired from MAPEM messages
                    driving_direction = "NW" if longitude < 0 else "SE"
                    car_is_controlled_by_simulation = True

                if driving_direction == "NW" and longitude >= 0 or \
                    driving_direction == "SE" and longitude <= 0:
                        # logger.info(f"Car already passed level crossing")
                        pass

                else:
                    if sharedLCState.eventState == MovementPhaseState_caution_Conflicting_Traffic:
                        if car_is_controlled_by_simulation:
                            if speed == 0:
                                # Vehicle stopped, e.g. because of traffic jam or preceding vehicles
                                # -> no stop needs to be schedules
                                pass

                            elif sharedLCState.maxEndTime > 0:
                                distance_to_rsu = math.sqrt(longitude ** 2 + latitude ** 2)
                                expected_arrival_time = distance_to_rsu / speed
                                
                                if expected_arrival_time < sharedLCState.maxEndTime:
                                    logger.info("Will stop at level crossing")
                                    mobility_provider.stopAtEndOfCurrentSegment(mobility_id, sharedLCState.maxEndTime - expected_arrival_time)
                                    car_is_controlled_by_simulation = False
                                else:
                                    # We will arrive after the level crossing will be opened again
                                    pass
                            else:
                                logger.info("Will stop at level crossing")
                                # Set duration to a very large value -> vehicle will resume when "movement allowed" message will be receivede
                                mobility_provider.stopAtEndOfCurrentSegment(mobility_id, 1000000000)
                                car_is_controlled_by_simulation = False
                        else:
                            # The car is already instructed to wait for the train to pass
                            pass
                    
                    if sharedLCState.eventState == MovementPhaseState_permissive_Movement_Allowed:
                        if not car_is_controlled_by_simulation:
                            logger.info("Starting car")
                            # We might not have reached or stop, e.g. if the preceding vehicle blocked the stop point
                            # In this case simply remove the planed stop
                            # If we have reached the stop position: resume vehicle
                            mobility_provider.resumeOrCancelStop(mobility_id)
                            car_is_controlled_by_simulation = True
        except ConnectionRefusedError:
            # Simply wait for the mobility provider server to become ready
            pass
                    
        end_time = time.time()

        time.sleep(max(0, period_sec - (end_time - start_time)))
