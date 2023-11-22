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
        if self.pos in self.model.cellToNode:
            # currNode stores the current Node we are in (not the cell)
            # if we are not in a node, it stores the node we are going towards, since we have to calculate the path from there
            self.currNode = self.model.cellToNode[self.pos]
            
            if self.path == None:
                self.generatePath()
                
            self.moveWithinNode()
            
        

    def generatePath(self):
        """
        Generates a path from the current location to the destination using A*.
        """
        
        # helper heuristic function
        def heuristic(n):
            cell = self.model.nodeToCells[n][0]
            return abs(cell[0] - self.destination[0]) + abs(cell[1] - self.destination[1])
        
        target = self.model.cellToNode[self.destination]
        
        print("from node: " + str(self.currNode))
        print("to node: " + str(target))
        
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

        # if it can move in the direction it's pathing towards, then move there
        if self.path[0][1] in self.model.nodeToDirections[self.currNode] and self.moveToDirection(self.path[0][1]):            
            # check if we are out of the current node
            if not (self.pos in self.model.cellToNode and self.model.cellToNode[self.pos] == self.currNode):
                # if we are, then remove the first element from the path
                self.path.popleft()
                
        elif self.moveToDirection(self.path[0][1]):
            # we moved in a direction not corresponding to our path, if we are out of the node
            # that means we couldn't follow our path and we need to recalculate it
            
            # check if we are out of the current node
            if not (self.pos in self.model.cellToNode and self.model.cellToNode[self.pos] == self.currNode):
                # find the new node from where we need to recalculate the path
                # it will be the target node of the edge from current node with the direction we moved in
                for edge in self.model.adList[self.currNode]:
                    if edge["direction"] == self.path[0][1]:
                        self.currNode = edge["to"]
                        self.generatePath()
                        break
    
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
    
    def isCarInCell(self, cell):
        """
        Checks if there is a car in the given cell.
        """
        return any (isinstance(agent, CarAgent) for agent in self.model.grid[cell[0]][cell[1]])

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

    def step(self):
        pass 

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