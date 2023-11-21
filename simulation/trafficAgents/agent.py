from mesa import Agent

class CarAgent(Agent):
    """
    Agent that represents a car that moves around the grid.
    
    """
    def __init__(self, unique_id, model):
        """
        Creates a new car agent.
        Args:
        """
        super().__init__(unique_id, model)

    def step(self):
        pass

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