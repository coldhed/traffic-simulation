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

        currentStep = 0

        print(request.form)
        print(timeToSpawn, spawnAmount)
        trafficModel = TrafficModel(timeToSpawn, spawnAmount)

        return jsonify({"message":"Parameters recieved, model initiated."})

@app.route('/getCarPositions', methods=['GET'])
def getCarPositions():
    global trafficModel

    if request.method == 'GET':
        agentPositions = [{"id": str(a.unique_id), "x": x, "y":1, "z":z} for a, (x, z) in trafficModel.grid.coord_iter() if isinstance(a, CarAgent)]

        return jsonify({'positions':agentPositions})
    
@app.route('/getFinishedCars', methods=['GET'])
def getFinishedCars():
    global trafficModel

    if request.method == 'GET':
        finishedCars = trafficModel.finishedCars

        return jsonify({'finishedCars':finishedCars})

@app.route('/getObstacles', methods=['GET'])
def getObstacles():
    global trafficModel

    if request.method == 'GET':
        carPositions = [{"id": str(a.unique_id), "x": x, "y":1, "z":z} for a, (x, z) in trafficModel.grid.coord_iter() if isinstance(a, ObstacleAgent)]

        return jsonify({'positions':carPositions})

@app.route('/update', methods=['GET'])
def updateModel():
    global currentStep, trafficModel
    if request.method == 'GET':
        trafficModel.step()
        currentStep += 1
        return jsonify({'message':f'Model updated to step {currentStep}.', 'currentStep':currentStep})

if __name__=='__main__':
    app.run(host="localhost", port=8585, debug=True)