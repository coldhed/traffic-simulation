/* 
C# client to interact with Python. Based on the code provided by Sergio Ruiz and Octavio Navarro.

Mariel Gómez
Santiago Rodríguez
*/
using System;
using System.Collections;
using System.Collections.Generic;
using UnityEditor;
using UnityEngine;
using UnityEngine.Networking;

[Serializable]
public class AgentData
{
    /*
    The AgentData class is used to store the data of each agent.
    
    Attributes:
        id (string): The id of the agent.
        x (float): The x coordinate of the agent.
        y (float): The y coordinate of the agent.
        z (float): The z coordinate of the agent.
    */
    public string id;
    public float x, y, z;

    public AgentData(string id, float x, float y, float z)
    {
        this.id = id;
        this.x = x;
        this.y = y;
        this.z = z;
    }
}

[Serializable]

public class AgentsData
{
    /*
    The AgentsData class is used to store the data of all the agents.

    Attributes:
        positions (list): A list of AgentData objects.
    */
    public List<AgentData> positions;

    public AgentsData() => this.positions = new List<AgentData>();
}

public class ModelController : MonoBehaviour
{
    /*
    The AgentController class is used to control the agents in the simulation.

    Attributes:
        serverUrl (string): The url of the server.
        getAgentsEndpoint (string): The endpoint to get the agents data.
        getObstaclesEndpoint (string): The endpoint to get the obstacles data.
        sendConfigEndpoint (string): The endpoint to send the configuration.
        updateEndpoint (string): The endpoint to update the simulation.
        carsData (AgentsData): The data of the agents.
        obstacleData (AgentsData): The data of the obstacles.
        agents (Dictionary<string, GameObject>): A dictionary of the agents.
        prevPositions (Dictionary<string, Vector3>): A dictionary of the previous positions of the agents.
        currPositions (Dictionary<string, Vector3>): A dictionary of the current positions of the agents.
        updated (bool): A boolean to know if the simulation has been updated.
        started (bool): A boolean to know if the simulation has started.
        agentPrefab (GameObject): The prefab of the agents.
        obstaclePrefab (GameObject): The prefab of the obstacles.
        floor (GameObject): The floor of the simulation.
        NAgents (int): The number of agents.
        width (int): The width of the simulation.
        height (int): The height of the simulation.
        timeToUpdate (float): The time to update the simulation.
        timer (float): The timer to update the simulation.
        dt (float): The delta time.
    */
    string serverUrl = "http://localhost:8585";
    string getCarsEndpoint = "/carPositions";
    string sendConfigEndpoint = "/init";
    string updateEndpoint = "/update";
    AgentsData carsData;
    Dictionary<string, GameObject> cars;


    public GameObject[] carPrefabs;
    public GameObject floor;
    public int timeToSpawn, spawnAmount;
    public float timeToUpdate = 5.0f;
    public float tileSize = 10f;
    private float timer, dt;

    void Start()
    {
        carsData = new AgentsData();

        cars = new Dictionary<string, GameObject>();

        // floor.transform.localScale = new Vector3((float)width / 10, 1, (float)height / 10);
        // floor.transform.localPosition = new Vector3((float)width / 2 - 0.5f, 0, (float)height / 2 - 0.5f);

        timer = timeToUpdate;

        // Launches a couroutine to send the configuration to the server.
        StartCoroutine(SendConfiguration());
    }

    private void Update()
    {
        timer -= Time.deltaTime;

        if (timer < 0)
        {
            timer = timeToUpdate;
            StartCoroutine(UpdateSimulation());
        }
    }

    IEnumerator UpdateSimulation()
    {
        UnityWebRequest www = UnityWebRequest.Get(serverUrl + updateEndpoint);
        yield return www.SendWebRequest();

        if (www.result != UnityWebRequest.Result.Success)
            Debug.Log(www.error);
        else
        {
            StartCoroutine(GetCarsData());
        }
    }

    IEnumerator SendConfiguration()
    {
        /*
        The SendConfiguration method is used to send the configuration to the server.

        It uses a WWWForm to send the data to the server, and then it uses a UnityWebRequest to send the form.
        */
        WWWForm form = new WWWForm();

        form.AddField("timeToSpawn", timeToSpawn.ToString());
        form.AddField("spawnAmount", spawnAmount.ToString());

        UnityWebRequest www = UnityWebRequest.Post(serverUrl + sendConfigEndpoint, form);
        www.SetRequestHeader("Content-Type", "application/x-www-form-urlencoded");

        yield return www.SendWebRequest();

        if (www.result != UnityWebRequest.Result.Success)
        {
            Debug.Log(www.error);
        }
        else
        {
            Debug.Log("Configuration upload complete!");
            Debug.Log("Getting Agents positions");

            // Once the configuration has been sent, it launches a coroutine to get the agents data.
            StartCoroutine(GetCarsData());
        }
    }

    IEnumerator GetCarsData()
    {
        // The GetCarsData method is used to get the agents data from the server.

        UnityWebRequest www = UnityWebRequest.Get(serverUrl + getCarsEndpoint);
        yield return www.SendWebRequest();

        if (www.result != UnityWebRequest.Result.Success)
            Debug.Log(www.error);
        else
        {
            // Once the data has been received, it is stored in the carsData variable.
            carsData = JsonUtility.FromJson<AgentsData>(www.downloadHandler.text);

            foreach (AgentData agent in carsData.positions)
            {
                Vector3 pos = new Vector3(agent.x * tileSize, agent.y, agent.z * tileSize - tileSize);
                GameObject car;
                if (cars.TryGetValue(agent.id, out car))
                {
                    // get the car controller
                    CarController carController = car.GetComponent<CarController>();
                    carController.SetNextWaypoint(pos);
                }
                else
                {
                    car = Instantiate(carPrefabs[UnityEngine.Random.Range(0, carPrefabs.Length)], pos, Quaternion.identity);
                    cars[agent.id] = car;

                    // get the car controller
                    CarController carController = car.GetComponent<CarController>();
                    carController.SetNextWaypoint(pos);
                    carController.SetMovementTime(timeToUpdate);
                }
            }

            // // Once the data has been received, it is stored in the carsData variable.
            // // Then, it iterates over the carsData.positions list to update the agents positions.
            // carsData = JsonUtility.FromJson<AgentsData>(www.downloadHandler.text);

            // foreach (AgentData agent in carsData.positions)
            // {
            //     Vector3 newAgentPosition = new Vector3(agent.x, agent.y, agent.z);

            //     if (!started)
            //     {
            //         prevPositions[agent.id] = newAgentPosition;
            //         agents[agent.id] = Instantiate(agentPrefab, newAgentPosition, Quaternion.identity);
            //     }
            //     else
            //     {
            //         Vector3 currentPosition = new Vector3();
            //         if (currPositions.TryGetValue(agent.id, out currentPosition))
            //             prevPositions[agent.id] = currentPosition;
            //         currPositions[agent.id] = newAgentPosition;
            //     }
            // }

            // updated = true;
            // if (!started) started = true;
        }
    }
}
