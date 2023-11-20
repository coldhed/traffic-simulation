from model import RandomModel, Roomba, ObstacleAgent, TrashAgent, ChargingStationAgent
from mesa.visualization import CanvasGrid, BarChartModule, PieChartModule
from mesa.visualization import ModularServer
from mesa.visualization import Slider

def agent_portrayal(agent):
    if agent is None: return
    
    portrayal = {"Filled": "true"}
    
    if (isinstance(agent, Roomba)):
        portrayal["Shape"] = "circle"
        portrayal["Layer"] = 1
        # color based on battery 100% = green, 50% = yellow, 0% = red
        red = 255 if agent.battery <= 50 else (255 / 50) * (100 - agent.battery)
        green = 255 if agent.battery > 50 else (255 / 50) * agent.battery
        portrayal["Color"] = "rgb(" + str(red) + ", " + str(green) + ", 0)"
        
        portrayal["r"] = 0.6

    elif (isinstance(agent, ObstacleAgent)):
        portrayal["Shape"] = "rect"
        portrayal["w"] = 0.9,
        portrayal["h"] = 0.9,
        portrayal["Color"] = "black"
        portrayal["Layer"] = 2
        
    elif (isinstance(agent, TrashAgent)):
        portrayal["Shape"] = "circle"
        portrayal["r"] = 0.5
        portrayal["Color"] = "#1f0cc9"
        portrayal["Layer"] = 0
        
    elif (isinstance(agent, ChargingStationAgent)):
        portrayal["Shape"] = "charge.webp"
        portrayal["Layer"] = 0
    

    return portrayal

W = 30
H = 30

model_params = {
    "width": W, 
    "height": H,
    "numRoombas": Slider("Number of Roombas", 5, 1, 10, 1),
    "numObstacles": Slider("Number of Obstacles", 5, 1, int(((W * H) - 2*W - 2*H) / 3), 1),
    "numTrash": Slider("Number of Trash", 5, 1, int(((W * H) - 2*W - 2*H) / 3), 1),
    "stepLimit": Slider("Steps Limit", 2500, 1, 5000, 100)
}

grid = CanvasGrid(agent_portrayal, W, H, 500, 500)

bar_chart = BarChartModule(
    [{"Label":"Steps", "Color":"#AA0000"}], 
    scope="agent", sorting="ascending", sort_by="Steps")

pie_chart = PieChartModule(
    [
        {"Label": "Trash Remaining", "Color": "green"},
        {"Label": "Trash Collected", "Color": "blue"}
    ]
)

server = ModularServer(RandomModel, [grid, bar_chart, pie_chart], "Random Agents", model_params)
                       
server.port = 8521 # The default
server.launch()