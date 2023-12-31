from trafficAgents.model import TrafficModel
from trafficAgents.agent import CarAgent, ObstacleAgent, StoplightAgent, StreetAgent, TargetAgent
from mesa.visualization import CanvasGrid, BarChartModule, PieChartModule
from mesa.visualization import ModularServer
from mesa.visualization import Slider, Checkbox

def agent_portrayal(agent):
    if agent is None: return
    
    portrayal = {"Filled": "true"}
    
    if (isinstance(agent, ObstacleAgent)):
        portrayal["Shape"] = "rect"
        portrayal["w"] = 0.9,
        portrayal["h"] = 0.9,
        portrayal["Color"] = "black"
        portrayal["Layer"] = 0
    
    elif (isinstance(agent, StoplightAgent)):
        portrayal["Shape"] = "rect"
        portrayal["w"] = 0.9,
        portrayal["h"] = 0.9,
        # the color will eventually be based on the state of the stoplight, but that's not implemented yet
        portrayal["Color"] = "red" if agent.color == "red" else "green"
        portrayal["Layer"] = 1
    
    elif (isinstance(agent, StreetAgent)):
        portrayal["Shape"] = "rect"
        portrayal["w"] = 1,
        portrayal["h"] = 1,
        portrayal["Color"] = "grey"
        portrayal["Layer"] = 0
    
    elif (isinstance(agent, TargetAgent)):
        portrayal["Shape"] = "rect"
        portrayal["w"] = 0.9,
        portrayal["h"] = 0.9,
        portrayal["Color"] = "blue"
        portrayal["Layer"] = 0

    elif (isinstance(agent, CarAgent)):
        portrayal["Shape"] = "circle"
        portrayal["r"] = 0.7,
        portrayal["Color"] = "#99c0ff"
        portrayal["Layer"] = 2

    return portrayal

W = 24
H = 25

model_params = {
    "timeToSpawn": Slider("Time to Spawn", 10, 1, 50, 1),
    "spawnAmount": Slider("Spawn Amount", 4, 1, 4, 1), # max 4
    "sendsData": Checkbox("Sends Data", False)
}

grid = CanvasGrid(agent_portrayal, W, H, W*20, H*20)

server = ModularServer(TrafficModel, [grid], "Random Agents", model_params)
                       
server.port = 8521 # The default
server.launch()
