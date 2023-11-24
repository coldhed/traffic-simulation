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
        

    def step(self):
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
            
            if self.path == None:
                self.generatePath()
                
            self.moveWithinNode()
        
        else:
            self.moveOutsideNode()
            
        

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
                    newCost = cost + edge["distance"]
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
            # check if we are out of the current node
            if not (self.pos in self.model.cellToNode and self.model.cellToNode[self.pos] == self.currNode):
                # if we are, then remove the first element from the path
                self.path.popleft()
            
        # as long as it's not a target node (since we know it's not a target), move with the flow to not block traffic   
        elif not self.targetNodeInDirection(streetDirections[0]) and self.moveToDirection(streetDirections[0]):
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
        
        lanes = ["up", "down"] if streetDirection == "left" or streetDirection == "right" else ["left", "right"]
        
        # lane we are in
        currentLane = self.getCurrentLane(streetDirection)
        
        # lane we are not in
        otherLane = lanes[0] if currentLane == lanes[1] else lanes[1]
        
        # an obligatory lane exists if we are making a turn next node
        obligatoryLane = self.getObligatoryLane(streetDirection)
        
        if obligatoryLane == None:
            bestLane = self.getBestLane(streetDirection)
            
            # try to move to the best lane
            if bestLane == currentLane:
                if not self.moveToDirection(streetDirection):
                    # if we didn't move, try to move to the other lane
                    self.moveLane(streetDirection, otherLane)
            else:
                if not self.moveLane(streetDirection, bestLane):
                    self.moveToDirection(streetDirection)
                
        elif currentLane == obligatoryLane:
            self.moveToDirection(streetDirection)
            
        else:
            if not self.moveLane(streetDirection, obligatoryLane):
                self.moveToDirection(streetDirection)
                
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
                
    def getCurrentLane(self, direction):
        """
        Returns the current lane of the car
        """
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