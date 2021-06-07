import os
import random

from marvis.channel.wifi import WiFiChannel
from marvis.mobility_input import SUMOMobilityInput
from marvis import ArgumentParser, Network, DockerNode, Scenario

def main():
    scenario = Scenario()

    net = Network("10.0.0.0", "255.255.255.0")

    train = DockerNode('train', docker_build_dir='./train', environment_variables=["MOBILITY_ID=train"])
    rsu = DockerNode('rsu', docker_build_dir='./rsu')
    cars = []
    for i in range(22):
        cars.append(DockerNode(f'car_{i}', docker_build_dir='./car', environment_variables=[f"MOBILITY_ID=car_{i}"]))

    v2x_channel = net.create_channel(channel_type=WiFiChannel, frequency=5855, channel_width=10, tx_power=25.0,
                standard=WiFiChannel.WiFiStandard.WIFI_802_11p, data_rate=WiFiChannel.WiFiDataRate.OFDM_RATE_BW_6Mbps)

    v2x_channel.connect(train, ifname="v2x")
    v2x_channel.connect(rsu, ifname="v2x")
    for car in cars:
        v2x_channel.connect(car, ifname="v2x")

    scenario.add_network(net)

    sumo = SUMOMobilityInput(sumo_cmd=f"{os.environ['SUMO_HOME']}/bin/sumo-gui", config_path="./scenario/paper.sumocfg", step_length=0.5, rpc_server_config=("172.17.0.1", 23404, False))
    # Map the docker containers to SUMO objects
    sumo.add_node_to_mapping(train, 'train')
    sumo.add_node_to_mapping(rsu, 'gneJ1', obj_type='junction')
    for car in cars:
        sumo.add_node_to_mapping(car, car.name)

    scenario.add_mobility_input(sumo)
    
    with scenario as sim:
        # To simulate forever, just do not specifiy the simulation_time parameter.
        sim.simulate(simulation_time=210)

if __name__ == "__main__":
    parser = ArgumentParser()
    parser.run(main)

def generate_routefile():
    random.seed(42)  # make tests reproducible
    N = 100  # number of time steps
    # demand per second from different directions
    pNW_SE = 1. / 10
    pSE_NW = 1. / 11
    train_departure = 55
    with open("scenario/paper.rou.xml", "w") as routes:
        print("""<routes>
        <route id="train_ne_sw" edges="ne_center center_sw" />
        <route id="car_nw_se" edges="nw_center center_se" />
        <route id="car_se_nw" edges="se_center center_nw" />

        <vType id="car" type="passenger" minGap="2.5" maxSpeed="55.56" accel="2.6" decel="4.5" sigma="0.5" tau="1.0" />
        <vType id="rail" vClass="rail" type="rail" length="200" accel="5" decel="10" sigma="1.0" maxSpeed="100" />
        """, file=routes)
        vehNr = 0
        for i in range(N):
            if random.uniform(0, 1) < pNW_SE:
                print(f'    <vehicle id="car_{vehNr}" type="car" route="car_nw_se" depart="{i}" />', file=routes)
                vehNr += 1
            if random.uniform(0, 1) < pSE_NW:
                print(f'    <vehicle id="car_{vehNr}" type="car" route="car_se_nw" depart="{i}" />', file=routes)
                vehNr += 1
            if i == train_departure:
                print(f'    <vehicle id="train" type="rail" route="train_ne_sw" depart="{train_departure}" />', file=routes)
        print("</routes>", file=routes)
