## EXPLORER AGENT
### @Author: Tacla, UTFPR
### It walks randomly in the environment looking for victims.

import random
from abstract_agent import AbstractAgent
from physical_agent import PhysAgent
from math import sqrt


class Explorer(AbstractAgent):

    def __init__(self, env, config_file, resc, name):
        """ Construtor do agente random on-line
        @param env referencia o ambiente
        @config_file: the absolute path to the explorer's config file
        @param resc referencia o rescuer para poder acorda-lo
        """

        super().__init__(env, config_file)

        # Specific initialization for the rescuer
        self.resc = resc  # reference to the rescuer agent
        self.rtime = self.TLIM  # remaining time to explore
        self.visitedStates = [(0, 0)]
        self.ends = []
        self.menor_f_base = 0
        self.name = name
        self.walls = []
        self.pathHome = {"path": [], "cost": 0}
        self.voltar = False
        self.COST_BACK = 0
        self.unback = []
        self.victims = []  # (x,y,index)
        self.max_x = 0
        self.max_y = 0
        self.x = 0
        self.y = 0
        self.graph = []
        self.map = []  # Cada elemento da coleção é um conjunto de 3 valores
        # que representam respectivamente: a posição relativa à
        # base (x e y) e o elemento encontrado nela,
        # esse ultimo podendo ser CLEAR = 0, WALL = 1, END = 2
        # e VICTIM = 3

    def costH(self, position, destiny):
        return int(sqrt((position[0] - destiny[0]) ** 2 + (position[1] - destiny[1]) ** 2))

    def Astar(self, position):
        disponiveis = {}
        checado = {}
        fronteira = []
        destino = (0, 0)
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

            if not (atual[0], atual[1] - 1) in checado and (atual[0], atual[1] - 1) in self.visitedStates:
                fronteira.append((0, -1))

            if not (atual[0] + 1, atual[1] - 1) in checado and (
                    atual[0] + 1, atual[1] - 1) in self.visitedStates:
                fronteira.append((1, -1))

            if not (atual[0] + 1, atual[1]) in checado and (atual[0] + 1, atual[1]) in self.visitedStates:
                fronteira.append((1, 0))

            if not (atual[0] + 1, atual[1] + 1) in checado and (
                    atual[0] + 1, atual[1] + 1) in self.visitedStates:
                fronteira.append((1, 1))

            if not (atual[0], atual[1] + 1) in checado and (atual[0], atual[1] + 1) in self.visitedStates:
                fronteira.append((0, 1))

            if not (atual[0] - 1, atual[1] + 1) in checado and (
                    atual[0] - 1, atual[1] + 1) in self.visitedStates:
                fronteira.append((-1, 1))

            if not (atual[0] - 1, atual[1]) in checado and (atual[0] - 1, atual[1]) in self.visitedStates:
                fronteira.append((-1, 0))

            if not (atual[0] - 1, atual[1] - 1) in checado and (
                    atual[0] - 1, atual[1] - 1) in self.visitedStates:
                fronteira.append((-1, -1))

            for opt in fronteira:
                nextPosOpt = (atual[0] + opt[0], atual[1] + opt[1])
                if nextPosOpt in checado.keys() or nextPosOpt in self.walls or nextPosOpt in self.ends:
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

    def deliberate(self) -> bool:
        """ The agent chooses the next action. The simulator calls this
        method at each cycle. Must be implemented in every agent"""

        dx = 0
        dy = 0

        actions = []  # lista de ações possiveis
        # No more actions, time almost ended
        if self.pathHome["cost"] < (self.rtime - (self.COST_DIAG if self.COST_DIAG > self.COST_LINE else self.COST_LINE) - self.COST_READ) and not self.voltar:
            # Check the neighborhood obstacles
            obstacles = self.body.check_obstacles()
            for i in range(0, len(obstacles) - 1):

                if i == 0:
                    pos = (dx, dy - 1)

                elif i == 1:
                    pos = (dx + 1, dy - 1)

                elif i == 2:
                    pos = (dx + 1, dy)

                elif i == 3:
                    pos = (dx + 1, dy + 1)

                elif i == 4:
                    pos = (dx, dy + 1)

                elif i == 5:
                    pos = (dx - 1, dy + 1)

                elif i == 6:
                    pos = (dx - 1, dy)

                else:
                    pos = (dx - 1, dy - 1)

                if obstacles[i] == 0:
                    if not ((self.x + pos[0], self.y + pos[1]) in self.visitedStates):  # Se a posição que ele quer ir, não foi visitada, pode ir pra actions
                        actions.append(pos)
                elif obstacles[i] == 1:
                    if not (self.x + pos[0], self.y + pos[1]) in self.walls:
                        self.walls.append((self.x + pos[0], self.y + pos[1]))
                        # adicionando parede ao mapa
                        self.map.append((self.x + pos[0], self.y + pos[1], 1))
                else:
                    if not pos in self.ends:
                        self.ends.append((self.x + pos[0], self.y + pos[1]))
                        # adicionando fins ao mapa
                        self.map.append((self.x + pos[0], self.y + pos[1], 2))

            if not len(actions) == 0:
                # newstate = actions.pop()
                newstate = random.choice(actions)  # Escolhe aleatoriamente uma ação
                dx = newstate[0]
                dy = newstate[1]
                self.unback.append((-dx, -dy))
                result = self.body.walk(dx, dy)


            else:  # Se não há ações disponíveis, ele volta uma posição com o 'self.unback.pop()'
                newstate = self.unback.pop()
                dx = newstate[0]
                dy = newstate[1]
                result = self.body.walk(dx, dy)

            self.x += dx
            self.y += dy

            position = (self.x, self.y)
            self.pathHome = self.Astar(position)

            if not ((self.x,
                     self.y) in self.visitedStates) and not ((self.x,
                                                              self.y) in self.walls):  # Para caso a posição atual dele não esteja em 'visitedStates'
                self.visitedStates.append((self.x, self.y))

            # print(self.x, self.y)
            # print(self.pathHome["path"])
            if self.body.x > self.max_x:
                self.max_x = self.x

            if self.body.y > self.max_y:
                self.max_y = self.y

            # Update remaining time
            if dx != 0 and dy != 0:
                self.rtime -= self.COST_DIAG
            else:
                self.rtime -= self.COST_LINE

            # Test the result of the walk action
            if result == PhysAgent.BUMPED:
                walls = 1  # build the map- to do

            if result == PhysAgent.EXECUTED:
                # check for victim returns -1 if there is no victim or the sequential
                # the sequential number of a found victim
                seq = self.body.check_for_victim()
                if seq >= 0:
                    vs = self.body.read_vital_signals(seq)
                    # vitima é representada por um conjunto de 3 valores.
                    # (dx, dy, index)
                    if not ((self.x, self.y, seq) in self.victims):
                        self.victims.append((self.x, self.y, seq))
                        self.map.append((self.x, self.y, 3))

                    self.rtime -= self.COST_READ
                    # print("exp: read vital signals of " + str(seq))
                    # print(vs)
                else:
                    # Inclui a posição livre no mapa
                    self.map.append((self.x, self.y, 0))
        else:
            if not self.voltar:
                self.voltar = True
            #print("PAREI na posicao:", self.x, ",", self.y)
            #print("CAMINHO para casa:", self.pathHome["path"])
            # time to wake up the rescuer
            # pass the walls and the victims (here, they're empty)
            #print(f"{self.name} I believe I've remaining time of {self.rtime:.1f}")
            homePos = self.pathHome["path"].pop(0)
            dx = homePos[0]
            dy = homePos[1]
            result = self.body.walk(dx, dy)
            self.x += dx
            self.y += dy

            if self.x == 0 and self.y == 0:
                self.resc.go_save_victims(self.map, self.victims, self.max_x, self.max_y)
                return False

        return True