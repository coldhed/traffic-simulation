import os
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
    def __init__(self):

        # RandomActivation is a scheduler that activates each agent once per step, in random order.
        self.schedule = RandomActivation(self)
        
        self.running = True
        
        self.destinations = []

        self.readMap("maps/2022.txt")
        
        # Multigrid is a special type of grid where each cell can contain multiple agents.
        self.grid = MultiGrid(len(self.map[0]), len(self.map), torus = False) 
        
        self.populateGrid()
        
        self.carCount = 0
        car = CarAgent(f"car{self.carCount}", self)
        self.grid.place_agent(car, (0, 0))
        self.schedule.add(car)
        
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

    def step(self):
        '''Advance the model by one step.'''
        self.schedule.step()