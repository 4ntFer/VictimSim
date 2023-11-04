##  ABSTRACT AGENT
### @Author: Tacla (UTFPR)
### It has the default methods for all the agents supposed to run in
### the environment

import os
import random
from abc import ABC, abstractmethod
from physical_agent import PhysAgent


class AbstractAgent:
    """ This class represents a generic agent and must be implemented by a concrete class. """
    
    
    def __init__(self, env, config_file):
        """ 
        Any class that inherits from this one will have these attributes available.
        @param env referencia o ambiente
        @param config_file: the absolute path to the agent's config file
        """
       
        self.env = env              # ref. to the environment
        self.body = None            # ref. to the physical part of the agent in the environment
        self.NAME = ""              # the name of the agent
        self.TLIM = 0.0             # time limit to execute (cannot be exceeded)
        self.COST_LINE = 0.0        # cost to walk one step hor or vertically
        self.COST_DIAG = 0.0        # cost to walk one step diagonally
        self.COST_READ = 0.0        # cost to read a victim's vital sign
        self.COST_FIRST_AID = 0.0   # cost to drop the first aid package to a victim
        self.COLOR = (100,100,100)  # color of the agent
        self.TRACE_COLOR = (140,140,140) # color for the visited cells
        
        # Read agents config file for controlling time
        with open(config_file, "r") as file:

            # Read each line of the file
            for line in file:
                # Split the line into words
                words = line.split()

                # Get the keyword and value
                keyword = words[0]
                if keyword=="NAME":
                    self.NAME = words[1]
                elif keyword=="COLOR":
                    r = int(words[1].strip('(), '))
                    g = int(words[2].strip('(), '))
                    b = int(words[3].strip('(), '))
                    self.COLOR=(r,g,b)  # a tuple
                elif keyword=="TRACE_COLOR":
                    r = int(words[1].strip('(), '))
                    g = int(words[2].strip('(), '))
                    b = int(words[3].strip('(), '))
                    self.TRACE_COLOR=(r,g,b)  # a tuple
                elif keyword=="TLIM":
                    self.TLIM = float(words[1])
                elif keyword=="COST_LINE":
                    self.COST_LINE = float(words[1])
                elif keyword=="COST_DIAG":
                    self.COST_DIAG = float(words[1])
                elif keyword=="COST_FIRST_AID":
                    self.COST_FIRST_AID = float(words[1])
                elif keyword=="COST_READ":    
                    self.COST_READ = float(words[1])
                    
        # Register within the environment - creates a physical body
        # Starts in the ACTIVE state
        self.body = env.add_agent(self, PhysAgent.ACTIVE)

      
    @abstractmethod
    def deliberate(self) -> bool:
        """ This is the choice of the next action. The simulator calls this
        method at each reasonning cycle if the agent is ACTIVE.
        Must be implemented in every agent
        @return True: there's one or more actions to do
        @return False: there's no more action to do """

        pass

    def costH(self, position, destiny):
        return int(sqrt((position[0] - destiny[0]) ** 2 + (position[1] - destiny[1]) ** 2))

    def Astar(self, position, destiny, known_states, walls, ends):
        disponiveis = {}
        checado = {}
        fronteira = []
        destino = destiny
        disponiveis[position] = {"g(n)": 0, "h(n)": self.costH(position, destino), "pai": None}
        while True:
            atual = None
            menor_f_caminho = 678542906
            for i in disponiveis.keys():
                if (disponiveis[i]["g(n)"] + disponiveis[i]["h(n)"]) <= menor_f_caminho:
                    menor_f_caminho = disponiveis[i]["g(n)"] + disponiveis[i]["h(n)"]
                    atual = i
            checado[atual] = disponiveis[atual]
            del disponiveis[atual]
            if atual == destino:
                break

            if not (atual[0], atual[1] - 1) in checado and (atual[0], atual[1] - 1) in known_states:
                fronteira.append((0, -1))

            if not (atual[0] + 1, atual[1] - 1) in checado and (
                    atual[0] + 1, atual[1] - 1) in known_states:
                fronteira.append((1, -1))

            if not (atual[0] + 1, atual[1]) in checado and (atual[0] + 1, atual[1]) in known_states:
                fronteira.append((1, 0))

            if not (atual[0] + 1, atual[1] + 1) in checado and (
                    atual[0] + 1, atual[1] + 1) in known_states:
                fronteira.append((1, 1))

            if not (atual[0], atual[1] + 1) in checado and (atual[0], atual[1] + 1) in known_states:
                fronteira.append((0, 1))

            if not (atual[0] - 1, atual[1] + 1) in checado and (
                    atual[0] - 1, atual[1] + 1) in known_states:
                fronteira.append((-1, 1))

            if not (atual[0] - 1, atual[1]) in checado and (atual[0] - 1, atual[1]) in known_states:
                fronteira.append((-1, 0))

            if not (atual[0] - 1, atual[1] - 1) in checado and (
                    atual[0] - 1, atual[1] - 1) in known_states:
                fronteira.append((-1, -1))

            for opt in fronteira:
                nextPosOpt = (atual[0] + opt[0], atual[1] + opt[1])
                if nextPosOpt in checado.keys() or nextPosOpt in walls or nextPosOpt in ends:
                    continue

                # gets the cost of the movement
                if opt[0] != 0 and opt[1] != 0:
                    movCost = self.COST_DIAG
                else:
                    movCost = self.COST_LINE

                if nextPosOpt not in disponiveis.keys():
                    disponiveis[nextPosOpt] = {
                        "g(n)": checado[atual]["g(n)"] + movCost,
                        "h(n)": self.costH(nextPosOpt, destino),
                        "pai": atual,
                    }
                elif (checado[atual]["g(n)"] + movCost) < disponiveis[nextPosOpt]["g(n)"]:
                    disponiveis[nextPosOpt]["g(n)"] = checado[atual]["g(n)"] + movCost
                    disponiveis[nextPosOpt]["pai"] = atual
            fronteira = []

            # Builds path
        atual = destino
        path = []

        while not atual == position:
            newMov = (atual[0] - checado[atual]["pai"][0], atual[1] - checado[atual]["pai"][1])
            path.append(newMov)
            atual = checado[atual]["pai"]
        return {"path": list(reversed(path)), "cost": checado[destino]["g(n)"]}

