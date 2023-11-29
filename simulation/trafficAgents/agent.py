from queue import PriorityQueue
from collections import deque
from mesa import Agent

class CarAgent(Agent):
    """
    Agent that represents a car that moves around the grid.
    
    """
    def __init__(self, unique_id, model, destination):
        """
        Creates a new car agent.
        Args:
        """
        super().__init__(unique_id, model)
        self.destination = destination
        self.prevNode = None
        
        self.path = None
        
        self.laneSpeed = deque([1])
        
        self.lastDirection = None
        
        # speedMatrix[i][j] stores the speed the car has perceived from node i to node j
        self.speedMatrix = [[1] * (len(self.model.nodeToCells) + 1) for _ in range(len(self.model.nodeToCells) + 1)]
        
        self.patienceLimit = 15
        self.stationaryTime = 0
        
    def step(self):
        if self.lastDirection == None:
            # get the direction of the street we are in
            for agent in self.model.grid[self.pos[0]][self.pos[1]]:
                if isinstance(agent, StreetAgent):
                    self.lastDirection = agent.directions[0]
        
        # if we are in our destination, then we are done
        if self.pos == self.destination:
            self.model.schedule.remove(self)
            self.model.grid.remove_agent(self)
            self.model.finishedCars.append(self.unique_id)
            return
        
        # if we are in a node
        if self.pos in self.model.cellToNode:
            # currNode stores the current Node we are in (not the cell)
            # if we are not in a node, it stores the node we are going towards, since we have to calculate the path from there
            self.currNode = self.model.cellToNode[self.pos]
                
            if self.path == None or self.path[0][0] != self.currNode:
                self.generatePath()
            
            self.moveWithinNode()
        
        else:
            self.moveOutsideNode()
        
        # if we have been stationary for too long, then we are stuck, try to move somewhere else
        if self.stationaryTime > self.patienceLimit:
            self.moveToUnstuck()
            
        # update the speed matrix with the information we gained, and calculate to see if there is a new path
        self.updateSpeed()
        self.generatePath()
            
        

    def generatePath(self):
        """
        Generates a path from the current location to the destination using A*.
        """
        
        # helper heuristic function
        def heuristic(n):
            cell = self.model.nodeToCells[n][0]
            return abs(cell[0] - self.destination[0]) + abs(cell[1] - self.destination[1])
        
        target = self.model.cellToNode[self.destination]
        
        pq = PriorityQueue()
        # (heuristic + cost, cost, node)
        pq.put((heuristic(self.currNode), 0, self.currNode))
        
        # stores a tuple (node, direction) 
        cameFrom = {}
        while pq.qsize() > 0:
            priority, cost, node = pq.get()

            # check if we are in the target node
            if node == target:
                # reconstruct the path and return it
                self.path = deque()
                
                while node != self.currNode:
                    self.path.appendleft((cameFrom[node][0], cameFrom[node][1]))
                    node = cameFrom[node][0]

                return 
            
            # if it has no edges, and it's not the target, then it's a dead end
            if node not in self.model.adList:
                continue
            
            for edge in self.model.adList[node]:
                nextN = edge["to"]
                
                if nextN not in cameFrom:
                    cameFrom[nextN] = (node, edge["direction"])
                    newCost = cost + (edge["distance"] / self.speedMatrix[int(node)][int(nextN)])
                    pq.put((heuristic(nextN) + newCost, newCost, nextN))
            
    def moveWithinNode(self):
        """
        Moves the car when it's within a node.
        """
        for agent in self.model.grid[self.pos[0]][self.pos[1]]:
            if isinstance(agent, StreetAgent):
                streetDirections = agent.directions


        # if it can move in the direction it's pathing towards, then move there
        if self.path[0][1] in streetDirections and self.moveToDirection(self.path[0][1]):  
            self.movedCell()
            
            # check if we are out of the current node
            if not (self.pos in self.model.cellToNode and self.model.cellToNode[self.pos] == self.currNode):
                # if we are, then remove the first element from the path
                self.path.popleft()
                if len(self.path) > 0:
                    # if there are still elements in the path, then we are in the next node
                    self.currNode = self.path[0][0]
                
                # our lane speed also resets, since we are in a new street
                self.laneSpeed = deque([1])
        
        # as long as it's not a target node (since we know it's not a target), move with the flow to not block traffic   
        elif not self.targetNodeInDirection(streetDirections[0]) and self.moveToDirection(streetDirections[0]):
            self.movedCell()
            # we moved in a direction not corresponding to our path, if we are out of the node
            # that means we couldn't follow our path and we need to recalculate it
            # check if we are out of the current node
            if not (self.pos in self.model.cellToNode and self.model.cellToNode[self.pos] == self.currNode):
                # find the new node from where we need to recalculate the path
                # it will be the target node of the edge from current node with the direction we moved in
                for edge in self.model.adList[self.currNode]:
                    if edge["direction"] == streetDirections[0]:
                        self.currNode = edge["to"]
                        self.generatePath()
                        break
                
                # our lane speed also resets, since we are in a new street
                self.laneSpeed = deque([1])
                
        else:
            self.didNotMoveCell()
            
        
    def moveOutsideNode(self):
        """
        Moves the car when it's outside a node.
        """
        # check if we are in a stoplight
        for agent in self.model.grid[self.pos[0]][self.pos[1]]:
            if isinstance(agent, StoplightAgent):
                if agent.color == "red":
                    return
                else:
                    break
        
        # get the direction of the street we are in
        streetDirection = None
        for agent in self.model.grid[self.pos[0]][self.pos[1]]:
            if isinstance(agent, StreetAgent):
                streetDirection = agent.directions[0]
        
        if streetDirection == None:
            streetDirection = self.lastDirection
            
        # check if we would move into a node -> idea seems to not work but I'll leave it here in case we want to use it later
        # nextNode = self.wouldMoveIntoNode(streetDirection)
        # if nextNode:
        #     # check intersection occupancy, if it's more than 50%, then don't move
        #     carCount = 0
        #     for agent in self.model.nodeToCells[nextNode]:
        #         for a in self.model.grid[agent[0]][agent[1]]:
        #             if isinstance(a, CarAgent):
        #                 carCount += 1
            
        #     if carCount / len(self.model.nodeToCells[nextNode]) > 0.5:
        #         self.didNotMoveCell()
        #         return
        
        lanes = ["up", "down"] if streetDirection == "left" or streetDirection == "right" else ["left", "right"]
        
        # lane we are in
        currentLane = self.getCurrentLane(streetDirection)
        
        # lane we are not in
        otherLane = lanes[0] if currentLane == lanes[1] else lanes[1]
        
        # an obligatory lane exists if we are making a turn next node
        obligatoryLane = self.getObligatoryLane(streetDirection)
        
        if obligatoryLane == None: 
            # we don't need to be in a lane, but there is a best lane that depends on our next turn
            bestLane = self.getBestLane(streetDirection)
            
            # if we are in the best lane try to move forwards, otherwise, try to change lane
            if bestLane == currentLane:
                
                # try to move forward
                if not self.moveToDirection(streetDirection):
                    # if we didn't move, try to move to the other lane
                    if self.moveLane(streetDirection, otherLane):
                        # we changed lane, so our lane speed resets
                        self.laneSpeed = deque([1])
                    else:
                        # we couldn't move
                        self.didNotMoveCell()
                
                else:
                    # we moved forwards
                    self.movedCell()
                    
            # if we are not in the best lane, try to move to it, otherwise, try to move forwards
            else:
                # try to move to the best lane
                if not self.moveLane(streetDirection, bestLane):
                    # we couldn't move to the best lane, so try to move forwards
                    if self.moveToDirection(streetDirection):
                        # we moved forwards
                        self.movedCell()
                    else:
                        # we couldn't move
                        self.didNotMoveCell()
                else:
                    # we changed lane, so our lane speed resets
                    self.laneSpeed = deque([1])
        
        # there is an obligatory lane
        else:
            # if we are not in the obligatory lane, try to move to it
            if currentLane != obligatoryLane and self.moveLane(streetDirection, obligatoryLane):
                # we changed lane, so our lane speed resets
                self.laneSpeed = deque([1])
            # either we are in the obligatory lane or we couldn't move to it, either way, try to move forwards
            else:
                if self.moveToDirection(streetDirection):
                    # we moved forwards
                    self.movedCell()
                else:
                    # we couldn't move
                    self.didNotMoveCell()    
                
        self.lastDirection = streetDirection
            
    
    def moveLane(self, direction, lane):
        """
        Moves the car to the given lane.
        """
        mod_x = 0
        mod_y = 0
        
        if direction == "up":
            mod_y = 1
        elif direction == "down":
            mod_y = -1
        elif direction == "left":
            mod_x = -1
        else: # direction == "right"
            mod_x = 1
        
        if lane == "up":
            mod_y += 1
        elif lane == "down":
            mod_y -= 1
        elif lane == "left":
            mod_x -= 1
        else: # lane == "right"
            mod_x += 1
            
        targetCell = (self.pos[0] + mod_x, self.pos[1] + mod_y)
        

        if not self.isCarInCell(targetCell):
            self.model.grid.move_agent(self, targetCell)            
            return True
        
        return False
        
    
    def moveToDirection(self, direction):
        if direction == "up":
            targetCell = (self.pos[0], self.pos[1] + 1)

        elif direction == "down":
            targetCell = (self.pos[0], self.pos[1] - 1)
                
        elif direction == "left":
            targetCell = (self.pos[0] - 1, self.pos[1])

        else: # direction == "right"
            targetCell = (self.pos[0] + 1, self.pos[1])
                
        if not self.isCarInCell(targetCell):
            self.model.grid.move_agent(self, targetCell)
            return True
        
        return False
    
    def targetNodeInDirection(self, direction):
        if direction == "up":
            targetCell = (self.pos[0], self.pos[1] + 1)

        elif direction == "down":
            targetCell = (self.pos[0], self.pos[1] - 1)
                
        elif direction == "left":
            targetCell = (self.pos[0] - 1, self.pos[1])

        else: # direction == "right"
            targetCell = (self.pos[0] + 1, self.pos[1])
            
        return any(isinstance(agent, TargetAgent) for agent in self.model.grid[targetCell[0]][targetCell[1]])
    
    def isCarInCell(self, cell):
        """
        Checks if there is a car in the given cell.
        """
        return any (isinstance(agent, CarAgent) for agent in self.model.grid[cell[0]][cell[1]])
    
    def getObligatoryLane(self, streetDirection):
        """
        Returns the preferred lane of the car, based on the direction it's going and the next step in the path
        """
        
        turnDirection = self.path[0][1]
        
        if streetDirection == turnDirection:
            return None
        else:
            return turnDirection
        
    def getBestLane(self, streetDirection):
        """
        Although the car doesn't need to make a turn next node, it will eventually have to,
        so we return what that lane will be.
        """
        for turn in self.path:
            if turn[1] != streetDirection:
                return turn[1]
            
        # we always need to make a turn to reach the destination, so this shouldn't happen
        return None
                
    def getCurrentLane(self, direction=None):
        """
        Returns the current lane of the car
        """
        if direction == None:
            direction = self.lastDirection
        
        if direction == "up" or direction == "down":
            # check if the the cell to the right is a street
            if self.pos[0] + 1 < self.model.grid.width and any(isinstance(agent, StreetAgent) or isinstance(agent, StoplightAgent) for agent in self.model.grid[self.pos[0] + 1][self.pos[1]]):
                return "left"
            else:
                return "right"
            
        else: # direction == "left" or direction == "right"
            # check if the the cell to the top is a street
            if self.pos[1] + 1 < self.model.grid.height and any(isinstance(agent, StreetAgent) or isinstance(agent, StoplightAgent) for agent in self.model.grid[self.pos[0]][self.pos[1] + 1]):
                return "down"
            else:
                return "up"
            
    def movedCell(self):
        """
        Updates the speed of the car when it moves to a new cell.
        """
        if len(self.laneSpeed) == 3:
            self.laneSpeed.popleft()
        
        self.laneSpeed.append(1)
        self.stationaryTime = 0
    
    def didNotMoveCell(self):
        """
        Updates the speed of the car when it doesn't move to a new cell.
        """
        self.laneSpeed[-1] += 1
        self.stationaryTime += 1
        
    def updateSpeed(self):        
        # if our current node has no turns, we're reaching the end of the path so we don't need to update the speeds
        if self.currNode not in self.model.adList:
            return
        
        laneSpeed = sum(self.laneSpeed) / len(self.laneSpeed)
        
        # observe the other lane's speed from observing other cars
        currentLane = self.getCurrentLane()
        
        laneToOtherLanePos = {"up":(0, -1), "down":(0, 1), "left":(1, 0), "right":(-1, 0)}
        otherLanePos = laneToOtherLanePos[currentLane]
        
        otherLaneSpeed = None
        for agent in self.model.grid[self.pos[0] + otherLanePos[0]][self.pos[1] + otherLanePos[1]]:
            if isinstance(agent, CarAgent):
                otherLaneSpeed = sum(agent.laneSpeed) / len(agent.laneSpeed)
                break
            
        if len(self.model.adList[self.currNode]) == 1 or len(self.model.nodeToCells[self.currNode]) == 2:
            # if there is only one edge, then we are going straight
            # so we update the speed of the edge, but we want to do propagate the velocity if next nodes also have one edge
            # also, nodes with only two cells are adjacent to destinations, but in practice, only have one useful edge for 
            # pathfinding since it's the only way to get to the destination
            averageSpeed = laneSpeed if otherLaneSpeed == None else (laneSpeed + otherLaneSpeed) / 2
            
            currentNode = self.currNode
            while len(self.model.adList[currentNode]) == 1 or len(self.model.nodeToCells[currentNode]) == 2:
                for edge in self.model.adList[currentNode]:
                    self.speedMatrix[int(currentNode)][int(edge["to"])] = averageSpeed
                    
                    if len(self.model.nodeToCells[edge["to"]]) > 1:
                        currentNode = edge["to"]
                        break
            
        else:
            for edge in self.model.adList[self.currNode]:
                fromNode = int(self.currNode)
                to = int(edge["to"])
                
                # the turn our lane makes
                if edge["direction"] == currentLane:
                    self.speedMatrix[fromNode][to] = laneSpeed
                
                # going straightforward
                elif edge["direction"] == self.lastDirection:
                    # if there are three turns, it's the average of the two lanes
                    if len(self.model.adList[self.currNode]) == 3:
                        self.speedMatrix[fromNode][to] = laneSpeed if otherLaneSpeed == None else (laneSpeed + otherLaneSpeed) / 2
                    # there are two turns, so it's the speed of the lane not turning
                    else:
                        if currentLane in self.model.nodeToDirections[self.currNode]:
                            if otherLaneSpeed != None:
                                self.speedMatrix[fromNode][to] = otherLaneSpeed
                        else:
                            self.speedMatrix[fromNode][to] = laneSpeed
                
                # the turn the other lane makes
                else:
                    if otherLaneSpeed != None:
                        self.speedMatrix[fromNode][to] = otherLaneSpeed
                    
            
    def wouldMoveIntoNode(self, direction):
        """
        Returns true if the car would move into a node in the given direction.
        """
        if direction == "up":
            targetCell = (self.pos[0], self.pos[1] + 1)

        elif direction == "down":
            targetCell = (self.pos[0], self.pos[1] - 1)
                
        elif direction == "left":
            targetCell = (self.pos[0] - 1, self.pos[1])

        else: # direction == "right"
            targetCell = (self.pos[0] + 1, self.pos[1])
        
        if targetCell in self.model.cellToNode:
            return self.model.cellToNode[targetCell]
        else:
            return False
    
    def moveToUnstuck(self):
        """
        Moves the car to a cell that is not occupied.
        """
        # if we are in a stoplight, we should wait 
        if any(isinstance(agent, StoplightAgent) for agent in self.model.grid[self.pos[0]][self.pos[1]]):
            return
        
        startedInNode = self.pos in self.model.cellToNode
        
        direction = self.lastDirection
        
        # find the street agent we are in
        for agent in self.model.grid[self.pos[0]][self.pos[1]]:
            if isinstance(agent, StreetAgent):
                if len(agent.directions) == 1:
                    direction = agent.directions[0]
        
        # try to move to any of the three squares in front of our direction
        if direction == "up":
            y = self.pos[1] + 1
            
            targetCells = [(x, y) for x in range(max(self.pos[0] - 1, 0), min(self.pos[0] + 2, self.model.grid.width))]
        
        elif direction == "down":
            y = self.pos[1] - 1
            
            targetCells = [(x, y) for x in range(max(self.pos[0] - 1, 0), min(self.pos[0] + 2, self.model.grid.width))]
        
        elif direction == "left":
            x = self.pos[0] - 1
            
            targetCells = [(x, y) for y in range(max(self.pos[1] - 1, 0), min(self.pos[1] + 2, self.model.grid.height))]
            
        else: # direction == "right"
            x = self.pos[0] + 1
            
            targetCells = [(x, y) for y in range(max(self.pos[1] - 1, 0), min(self.pos[1] + 2, self.model.grid.height))]
        
        for cell in targetCells:
            if not self.isCarInCell(cell) and cell not in self.model.destinations:
                # check if the cell is a street or a stoplight
                if not any(isinstance(agent, StreetAgent) for agent in self.model.grid[cell[0]][cell[1]]):
                    continue
                
                self.model.grid.move_agent(self, cell)
                self.movedCell()
                
                # if we were in a node, check if we are still in it
                if startedInNode:
                    # we are no longer in a node, so our current node will be the target node of the edge in the direction we are moving in
                    if self.pos not in self.model.cellToNode:
                        # find the direction of the street we are in
                        streetDirection = self.lastDirection
                        for agent in self.model.grid[self.pos[0]][self.pos[1]]:
                            if isinstance(agent, StreetAgent):
                                streetDirection = agent.directions[0]
                            
                        # find the new node from where we need to recalculate the path
                        for edge in self.model.adList[self.currNode]:
                            if edge["direction"] == streetDirection:
                                self.currNode = edge["to"]
                                self.generatePath()
                                self.laneSpeed = deque([1])
                                
                                break
                    
                    elif self.model.cellToNode[self.pos] != self.currNode:
                        self.currNode = self.model.cellToNode[self.pos]
                        self.generatePath()
                        self.laneSpeed = deque([1])                    
                
                return True
            
        return False
    
class ObstacleAgent(Agent):
    """
    Obstacle agent. Just to add obstacles to the grid.
    """
    def __init__(self, unique_id, model):
        super().__init__(unique_id, model)

    def step(self):
        pass  

class StoplightAgent(Agent):
    """
    Stoplight regulates traffic flow. Can be either vertial or horizontal.
    """
    def __init__(self, unique_id, model, direction):
        super().__init__(unique_id, model)
        self.direction = direction
        
        self.color = "red" if direction == "horizontal" else "green"
        self.shiftIn = 10
        self.timer = 0

    def step(self):
        self.timer += 1
        
        if self.timer == self.shiftIn:
            self.timer = 0
            self.color = "green" if self.color == "red" else "red"

class StreetAgent(Agent):
    """
    Street agent. Cars navigate through here. They can have multiple directions
    """
    def __init__(self, unique_id, model, directions):
        super().__init__(unique_id, model)
        self.directions = directions

    def step(self):
        pass

class TargetAgent(Agent):
    """
    Represents a space where cars can go to. 
    """
    def __init__(self, unique_id, model):
        super().__init__(unique_id, model)
        
    def step(self):
        pass