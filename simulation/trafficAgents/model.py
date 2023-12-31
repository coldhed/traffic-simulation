import os
import random
import json
import requests

from mesa import Model, agent
from mesa.time import RandomActivation
from mesa.space import MultiGrid
from .agent import CarAgent, ObstacleAgent, StoplightAgent, StreetAgent, TargetAgent

class TrafficModel(Model):
    """ 
    Creates a new model with random agents.
    Args:
        N: Number of agents in the simulation
        height, width: The size of the grid to model
    """
    def __init__(self, timeToSpawn, spawnAmount, sendsData = False):

        # RandomActivation is a scheduler that activates each agent once per step, in random order.
        self.schedule = RandomActivation(self)
        
        self.running = True
        
        self.destinations = []

        self.readMap("maps/2023.txt")
        
        # Multigrid is a special type of grid where each cell can contain multiple agents.
        self.grid = MultiGrid(len(self.map[0]), len(self.map), torus = False) 
        
        self.populateGrid()
        self.readGraph("maps/2023_Graph.json")
        
        self.carCount = 0
        self.spawnPoints = [(0, 0), (0, len(self.map)- 1), (len(self.map[0]) - 1, 0), (len(self.map[0]) - 1, len(self.map) - 1)]
        
        self.timeToSpawn = timeToSpawn
        self.spawnAmount = spawnAmount
        self.timeSinceLastSpawn = 0
        
        self.finishedCars = [] # used by Unity to know which cars to remove, so it's reset every step
        self.totalFinishedCars = [] # used by the server to know how many cars have finished
        
        self.sendsData = sendsData
        self.timeToSendData = 100
        self.stepsSinceLastData = 0
        self.URI = "http://52.1.3.19:8585/api"
        self.ep = "/attempts"
        self.steps = 0
        
        
    def readMap(self, filename):
        """
        Given a filename, read the map
        """
        self.map = []
        with open(os.path.join(os.path.dirname(__file__), filename), 'r') as f:
            for line in f:
                # insert at the beginning of the list so that the first line is at the top of the map
                self.map.insert(0, [*line.strip()])
    
    def populateGrid(self):
        """
        Given the map of characters, iterate through it and add agents to the grid
        """
        for h in range(self.grid.height):
            for w in range(self.grid.width):
                if (self.map[h][w] == '#'):
                    agent = ObstacleAgent(f"{h}_{w}", self)
                elif (self.map[h][w] == 'S'):
                    agent = StoplightAgent(f"{h}_{w}", self, "horizontal")
                    self.schedule.add(agent)
                elif (self.map[h][w] == 's'):
                    agent = StoplightAgent(f"{h}_{w}", self, "vertical")
                    self.schedule.add(agent)
                elif (self.map[h][w] == 'D'):
                    agent = TargetAgent(f"{h}_{w}", self)
                    self.destinations.append((w, h))
                else:
                    # agent is a street, find it's directions
                    d = self.map[h][w]
                    
                    if d == '^':
                        directions = ["up"]
                    elif d == 'v':
                        directions = ["down"]
                    elif d == '>':
                        directions = ["right"]
                    elif d == '<':
                        directions = ["left"]
                    elif d == 'q':
                        directions = ["up", "left"]
                    elif d == 'e':
                        directions = ["up", "right"]
                    elif d == 'z':
                        directions = ["down", "left"]
                    elif d == 'c':
                        directions = ["down", "right"]
                    else:
                        # shouldn't get here but just in case
                        directions = ["up", "down", "left", "right"]
                        
                    agent = StreetAgent(f"{h}_{w}", self, directions)
                
                self.grid.place_agent(agent, (w, h))

    def readGraph(self, filename):
        """
        Given a filename, read the graph
        Since the json is done manually, do this to check if it's correct:
            verify number of nodes
            verify number of cells in total that are nodes
            verify number of nodes with edges
            verify that for all nodes, the number of directions is the same as the number of edges
        """
        with open(os.path.join(os.path.dirname(__file__), filename), 'r') as f:
            self.graph = json.load(f)

            # dictionary mapping nodes to cells
            self.nodeToCells = {}
            # dictionary mapping cells to nodes
            self.cellToNode = {}
            # dictionary mapping nodes to directions
            self.nodeToDirections = {}
            
            for node in self.graph["nodes"]:
                self.nodeToDirections[node["id"]] = node["directions"]
                
                self.nodeToCells[node["id"]] = [(cell["x"], cell["y"]) for cell in node["cells"]]
            
                for cell in node["cells"]:
                    self.cellToNode[(cell["x"], cell["y"])] = node["id"]
            
            # create an adjacency list | + 1 because the nodes are 1-indexed
            self.adList = {}
            
            for edge in self.graph["edges"]:
                source = edge["from"]
                edge.pop("from")
                
                if source in self.adList:
                    self.adList[source].append(edge)
                else:
                    self.adList[source] = [edge]
                

    def step(self):
        '''Advance the model by one step.'''
        self.timeSinceLastSpawn += 1
        if self.timeSinceLastSpawn >= self.timeToSpawn:
            self.timeSinceLastSpawn = 0
            self.spawnCars()
            
        if self.sendsData:
            self.stepsSinceLastData += 1
            
            if self.steps >= 1000:
                self.running = False
                self.sendData()
            
            elif self.stepsSinceLastData >= self.timeToSendData:
                self.stepsSinceLastData = 0
                self.sendData()
        
        if self.running:
            self.finishedCars = []
            self.schedule.step()
            print("cars on the road: ", len([agent for agent in self.schedule.agents if isinstance(agent, CarAgent)]))
            print("total finished cars: ", len(self.totalFinishedCars))
            
        self.steps += 1
    
    def spawnCars(self):
        spawnPointsCopy = self.spawnPoints.copy()
        
        carsSpawned = 0
        while len(spawnPointsCopy) and carsSpawned < self.spawnAmount:
            pos = random.choice(spawnPointsCopy)
            spawnPointsCopy.remove(pos)
            if not any(isinstance(agent, CarAgent) for agent in self.grid[pos[0]][pos[1]]):
                car = CarAgent(f"car{self.carCount}", self, random.choice(self.destinations))
                self.carCount += 1
                self.grid.place_agent(car, pos)
                self.schedule.add(car)
                carsSpawned += 1
        
        if carsSpawned == 0:
            print("No cars spawned")
            self.running = False
            
    def sendData(self):
        data = {
            "year": 2023,
            "classroom": 302,
            "name": "Mariel y Sant",
            "num_cars": len(self.totalFinishedCars),
        }
        
        print("Sending data: ", data)
        
        headers = {
            "Content-Type": "application/json"
        }
        
        try:
            response = requests.post(self.URI + self.ep, data=json.dumps(data), headers=headers)
        
            print("Request " + "successful" if response.status_code == 200 else "failed", "Status code:", response.status_code)
            print("Response:", response.json())
        except:
            print("Request failed")
