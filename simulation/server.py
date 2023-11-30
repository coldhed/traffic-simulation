# TC2008B. Sistemas Multiagentes y Gráficas Computacionales
# Python flask server to interact with Unity. Based on the code provided by Sergio Ruiz.
# Octavio Navarro. October 2023git 

from flask import Flask, request, jsonify
from trafficAgents.model import TrafficModel
from trafficAgents.agent import CarAgent, StoplightAgent

# Size of the board:
timeToSpawn = 1
spawnAmount = 4 # max 4
trafficModel = None
currentStep = 0

app = Flask("Traffic example")

@app.route('/init', methods=['POST'])
def initModel():
    global currentStep, trafficModel, number_agents, width, height

    if request.method == 'POST':
        timeToSpawn = int(request.form.get('timeToSpawn'))
        spawnAmount = int(request.form.get('spawnAmount'))
        sendsData = request.form.get('sendsData') == "True"
        
        currentStep = 0

        trafficModel = TrafficModel(timeToSpawn, spawnAmount, sendsData)

        return jsonify({"message":"Parameters recieved, model initiated."})

@app.route('/carPositions', methods=['GET'])
def getCarPositions():
    global trafficModel

    if request.method == 'GET':
        agentPositions = [{"id": str(a.unique_id), "x": a.pos[0], "y":1, "z": a.pos[1]} for a in trafficModel.schedule.agents if isinstance(a, CarAgent)]

        return jsonify({'positions':agentPositions})
    
@app.route('/finishedCars', methods=['GET'])
def getFinishedCars():
    global trafficModel

    if request.method == 'GET':
        finishedCars = [{"id": str(carID), "x": 0, "y":1, "z": 0} for carID in trafficModel.finishedCars]
        print(finishedCars)

        return jsonify({'positions':finishedCars})


@app.route('/update', methods=['GET'])
def updateModel():
    global currentStep, trafficModel
    if request.method == 'GET':
        trafficModel.step()
        currentStep += 1
        print("step: ", currentStep)
        return jsonify({'message':f'Model updated to step {currentStep}.', 'currentStep':currentStep})

@app.route('/stopLightStatus', methods=['GET'])
def getStopLights():
    global trafficModel

    if request.method == 'GET':
        stoplights = [{"id": str(a.pos[0]) + "," + str(a.pos[1]), "x": a.pos[0], "y":1, "z": a.pos[1], "color": a.color, "direction": a.direction} for a in trafficModel.schedule.agents if isinstance(a, StoplightAgent)]
        return jsonify({'stopLights':stoplights})


if __name__=='__main__':
    app.run(host="localhost", port=8585, debug=True)