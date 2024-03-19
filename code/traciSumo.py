import os
import sys
import optparse
import traci
import sumolib
import numpy as np
from random import randint
import matplotlib.pyplot as plt
import pandas as pd
import tkinter as tk
import csv
from tkinter import ttk

class TraciSumo:
    def __init__(self, int=1, vehicle_id=None, sens=True):
        self.controlSumo()
        self.options = self.getOptions()
        self.run(int, vehicle_id, sens)

    def controlSumo(self):
        # we need to import some python modules from the $SUMO_HOME/tools directory
        if 'SUMO_HOME' in os.environ:
            tools = os.path.join(os.environ['SUMO_HOME'], 'tools')
            sys.path.append(tools)
        else:
            sys.exit("please declare environment variable 'SUMO_HOME'")

    def getOptions(self):
        opt_parser = optparse.OptionParser()
        opt_parser.add_option("--nogui", action="store_true", default=False, help="Run without using SUMO-gui")
        options, args = opt_parser.parse_args()
        return options

    def getAllEdge(self):
        self.edges = {}     # Keys: Edge | Values: Node & Connected Road

        def getNet_xml():
            filePath = os.path.join(os.getcwd(), "sim\\traffic.net.xml")
            return sumolib.net.readNet(filePath)
        
        net = getNet_xml()

        lanes = traci.lane.getIDList()
        edges = traci.edge.getIDList()
        for edge in edges:
            if '_' not in edge:
                try:
                    self.edges[edge]
                except:
                    self.edges[edge] = {}
                finally:
                    matching_lanes = [lane for lane in lanes if lane.startswith(f"{edge}_") and not lane.endswith("_0")]
                    matching_lanes = [len(traci.lane.getLinks(lane)) for lane in matching_lanes]

                    self.edges[edge]["Node"] = net.getEdge(edge).getToNode().getID()           
                    self.edges[edge]["Connected"] = sum(matching_lanes)
            
            elif "_c" in edge:
                try:
                    self.edges[edge]
                except:
                    self.edges[edge] = {}
                finally:
                    node = edge[edge.index(":") + 1 : edge.index("_")]
                    self.edges[edge]["Node"] = node

    def getAllVehicle(self):
        self.vehicles = []

        file_path = os.path.join(os.getcwd(), "sim\\traffic.rou.xml")
        vehicles = sumolib.xml.parse(file_path, "trip")
        for vehicle in vehicles:
            self.vehicles.append({"id": vehicle.id, "type":vehicle.type})

    def getAllNode(self):
        nodes = {}
        for edge, data in self.edges.items():
            node = data["Node"]
            if node in nodes:
                nodes[node].append(edge)
            else:
                nodes[node] = [edge]

        self.nodes = {}
        for node, connectRoad in nodes.items():
            if len(connectRoad) > 1:
                self.nodes[node] = connectRoad

    def calculateVehicle(self, calculateId=1, targetStep=None):
        # Data
        self.roadVehicleCount = {}

        # calculateId = 1
        def vehicleCount():
            #? Vehicle Count
            road_ids = traci.lane.getIDList()
            self.roadVehicleCount[targetStep] = {}
            for road_id in road_ids:
                #? Calculate Vehicle Count in Edges
                vehicle_count = traci.lane.getLastStepVehicleNumber(road_id)
                edge, lane_id = road_id.split("_")[0], road_id.split("_")[1]
                if (edge in self.edges.keys()) and (int(lane_id) != 0):
                    try:
                        self.roadVehicleCount[targetStep][edge] += vehicle_count
                    except:
                        self.roadVehicleCount[targetStep][edge] = vehicle_count

        if targetStep is not None:
            traci.simulationStep(targetStep)
            if calculateId == 1:
                vehicleCount()
        else:
            step = 0
            while traci.simulation.getMinExpectedNumber() > 0:
                traci.simulationStep(step=step)

                if calculateId == 1:
                    vehicleCount()
                step += 1

    def calculateOccupancyInNode(self, step, node, nodeList, sens=True):
        occupancy = {}
        self.calculateVehicle(calculateId=1, targetStep=step)
        for edge in nodeList:
            occupancy[edge] = self.roadVehicleCount[step][edge]
        # print(step)
        try:
            self.maxEdge[node]
        except:
            self.maxEdge[node] = ""
        finally:
            sorted_occupancy = sorted(occupancy.items(), key=lambda x: x[1], reverse=True)
            # print(sorted_occupancy)
            if self.maxEdge[node] == max(occupancy, key=occupancy.get):
                self.maxEdge[node] = sorted_occupancy[1][0]
                # print(sorted_occupancy[1][0])
            else:
                self.maxEdge[node] = max(occupancy, key=occupancy.get)

            if sens:
                for edge, vehicleCount in sorted_occupancy:
                    for vehicle in traci.edge.getLastStepVehicleIDs(edge):
                        # print(step, node, edge, traci.vehicle.getTypeID(vehicle))
                        if "vehicle_emergency" == traci.vehicle.getTypeID(vehicle):
                            self.maxEdge[node] = f"emergency_{edge}"
                            break

        return self.maxEdge[node]

    def vehicleSpeed(self, step, vehicleID):
        #? Vehicle (id) - Speed Data
        if vehicleID is not None:
            self.vehicleID_data = vehicleID
        else:
            self.vehicleID_data

        if self.vehicleID_data in traci.vehicle.getIDList():
            speedVehicle = traci.vehicle.getSpeed(self.vehicleID_data)
            try:
                self.vehicleState[vehicleID]
            except:
                self.vehicleState[vehicleID] = {
                    "step" : [],
                    "speed" : []
                }
            finally:
                try:
                    self.vehicleState[vehicleID]["step"].append(step)
                    self.vehicleState[vehicleID]["speed"].append(speedVehicle) 
                except:
                    print("hata")

    def decideRoad(self, vehicleID, sens):
        self.vehicleID_data = self.vehicles[randint(0, len(self.vehicles)-1)]["id"]
        self.maxEdge = {}

        def updateTrafficLamb(targetStep, targetNode, nodeList):
            roadList = [road for road in nodeList if not road.startswith(":")]
            crossList = [crosswalk for crosswalk in nodeList if crosswalk.startswith(":")]

            trafficLambList = traci.trafficlight.getControlledLanes(targetNode)

            time = 0

            decide_edge = self.calculateOccupancyInNode(step=targetStep, node=targetNode, nodeList=roadList, sens=sens)
            if decide_edge.startswith("emergency_"):
                decide_edge = decide_edge.split("_")[1]
                time = self.roadVehicleCount[targetStep][decide_edge] * 2
            else:
                road_count = len(roadList)
                for edge in roadList:
                    if decide_edge is not edge:
                        time -= (self.roadVehicleCount[targetStep][edge] * 5 / (road_count-1))     # (Vehicle Count in Edge) * 5 sn / (road_count-1)
                    elif decide_edge is edge:
                        time += (self.roadVehicleCount[targetStep][edge] * 5)     # (Vehicle Count in Edge) * 5 sn

            if time != 0:
                trafficState = map(lambda lane: 'G' if lane.startswith(decide_edge) else 'r', trafficLambList)
                trafficLamb = ''.join(trafficState)
                traci.trafficlight.setRedYellowGreenState(targetNode, trafficLamb)
                return time

            else:
                crossCount = len(crossList)
                lane = 0  
                for road in roadList:
                    lane += self.edges[road]["Connected"]
                
                trafficLamb = "r" * lane + "G" * crossCount
                traci.trafficlight.setRedYellowGreenState(targetNode, trafficLamb)
                return 3

        step = 0
        timer = {node: {"start":0, "stop":0, "step":0} for node, nodeList in self.nodes.items()}
        while traci.simulation.getMinExpectedNumber() > 0:

            # Sayaç değişim olduğunda funk çağır
            for node, nodeList in self.nodes.items():
                if step < timer[node]["stop"]:
                    traci.simulationStep(step=step)
                else:
                    timer[node]["step"] =  updateTrafficLamb(targetStep=step, targetNode=node, nodeList=nodeList)
                    # timer[node]["step"] = traci.trafficlight.getPhaseDuration(node)
                    # print(node, traci.trafficlight.getPhaseDuration(node))
                    timer[node]["start"] = step
                    timer[node]["stop"] = timer[node]["start"] + timer[node]["step"]

            if vehicleID is not None:
                if vehicleID == "All" or vehicleID == "all":
                    for vehicle in traci.vehicle.getIDList():
                        self.vehicleSpeed(step=step, vehicleID=vehicle)
                else:
                    self.vehicleSpeed(step=step, vehicleID=vehicleID)
            else:
                self.vehicleSpeed(step=step)

            step += 1

    def simulation(self, vehicleID):
        self.vehicleID_data = self.vehicles[randint(0, len(self.vehicles)-1)]["id"]

        step = 0
        while traci.simulation.getMinExpectedNumber() > 0:
            
            print(traci.trafficlight.getPhaseDuration("K1"))

            # if traci.trafficlight.getPhaseDuration("K1") == 10:
            #     traci.trafficlight.setPhaseDuration("K1", 5)
            
            traci.simulationStep(step=step)

            if vehicleID is not None:
                if vehicleID == "All" or vehicleID == "all":
                    for vehicle in traci.vehicle.getIDList():
                        # print(vehicle)
                        self.vehicleSpeed(step=step, vehicleID=vehicle)
                else:
                    self.vehicleSpeed(step=step, vehicleID=vehicleID)
            else:
                self.vehicleSpeed(step=step)
            step += 1

    def chartTraffic(self, chartID=1, vehicle_id=None, sens=True):

        def pltDataVehicle(vehicle_id=None):
            self.simulation(vehicleID=vehicle_id)

            if vehicle_id == "All" or vehicle_id == "all":
                filePath = os.path.join(os.getcwd(), "code\\dataVehicleState_normal.txt")
                with open(filePath, 'w+') as file:
                    file.write(f'Normal Simulation\n')
                    for vehicle in self.vehicles:
                        if vehicle["type"] == "vehicle_emergency":
                            file.write(f'Vehicle ID: {vehicle["id"]} (Emergency)\n')
                        else:
                            file.write(f'Vehicle ID: {vehicle["id"]}\n')
                        # print(self.vehicleState[vehicle["id"]]["step"])
                        for index in range(len(self.vehicleState[vehicle["id"]]["step"])):
                            file.write(f'Step: {self.vehicleState[vehicle["id"]]["step"][index]}\t- Speed : {self.vehicleState[vehicle["id"]]["speed"][index]}\n')
            else:
                # Graph
                fig, ax = plt.subplots(1)
                ax.plot(self.vehicleState[vehicle_id]["step"], self.vehicleState[vehicle_id]["speed"], label='Speed for step', color='red', ls='-')

                ax.legend(loc='upper left')

                ax.set_title(f"Vehicle ID: {self.vehicleID_data}")
                ax.set_xlabel('Steps')
                ax.set_ylabel('Speeds')
                ax.grid()

                # Grafiği görüntüleyin
                plt.show()
        
        def pltDataVehicle_2(vehicle_id=None):
            self.decideRoad(vehicleID=vehicle_id, sens=sens)

            if vehicle_id == "All" or vehicle_id == "all":
                filePath = os.path.join(os.getcwd(), "code\\dataVehicleState_decide.txt")
                with open(filePath, 'w+') as file:
                    file.write(f'Decide Simulation\n')
                    for vehicle in self.vehicles:
                        if vehicle["type"] == "vehicle_emergency":
                            file.write(f'Vehicle ID: {vehicle["id"]} (Emergency)\n')
                        else:
                            file.write(f'Vehicle ID: {vehicle["id"]}\n')
                        for index in range(len(self.vehicleState[vehicle["id"]]["step"])):
                            file.write(f'Step: {self.vehicleState[vehicle["id"]]["step"][index]}\t- Speed : {self.vehicleState[vehicle["id"]]["speed"][index]}\n')
            else:
                # Graph
                fig, ax = plt.subplots(1)
                ax.plot(self.vehicleState[vehicle_id]["step"], self.vehicleState[vehicle_id]["speed"], label='Speed for step', color='green', ls='-')

                ax.legend(loc='upper left')

                ax.set_title(f"Vehicle ID: {self.vehicleID_data}")
                ax.set_xlabel('Steps')
                ax.set_ylabel('Speeds')
                ax.grid()

                # Grafiği görüntüleyin
                plt.show()

        if chartID == 1:
            pltDataVehicle(vehicle_id=vehicle_id)
        elif chartID == 2:
            pltDataVehicle_2(vehicle_id=vehicle_id)
        else:
            pass

    def run(self, int, vehicle_id, sens):
        if self.options.nogui:
            sumoBinary = "sumo"
        else:
            sumoBinary = "sumo-gui"

        filePath = os.path.join(os.getcwd(), "sim\\traffic.sumocfg")
        traci.start([sumoBinary, "-c", filePath, "--tripinfo-output", "sumoTrafficInfo.xml"])
        
        self.getAllEdge()
        self.getAllVehicle()
        self.getAllNode()
        self.vehicleState = {}

        self.chartTraffic(chartID=int, vehicle_id=vehicle_id, sens=sens)

        traci.close()
        sys.stdout.flush()

