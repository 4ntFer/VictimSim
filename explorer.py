## EXPLORER AGENT
### @Author: Tacla, UTFPR
### It walks randomly in the environment looking for victims.

import sys
import os
import random
from abstract_agent import AbstractAgent
from physical_agent import PhysAgent
from abc import ABC, abstractmethod
from math import sqrt


class Explorer(AbstractAgent):

    def __init__(self, env, config_file, resc):
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
        self.walls = []
        self.pathHome = []
        self.voltar = False
        self.COST_BACK = 0
        self.unback = []
        self.victims = []  # (x,y,index)
        self.max_x = 0
        self.max_y = 0
        self.allPositions = []
        self.x = 0
        self.y = 0
        self.map = []  # Cada elemento da coleção é um conjunto de 3 valores
        # que representam respectivamente: a posição relativa à
        # base (x e y) e o elemento encontrado nela,
        # esse ultimo podendo ser CLEAR = 0, WALL = 1, END = 2
        # e VICTIM = 3

    def costH(self, position, destiny):
        return sqrt((position[0] - destiny[0]) ** 2 + (position[1] - destiny[1]) ** 2)

    def Astar(self, position):
        self.COST_BACK = 0  # Custo para voltar para base
        disponiveis = []  # Estados disponiveis para o agente ir
        checked = []  # Checa se um estado já nao esta no caminho para casa
        home = []  # Constroi o caminho para casa
        f = 0
        g = 0  # Variáveis importantes
        a = 0
        b = 0
        print("POSICAO ATUAL:", position)
        while True:
            new = position.pop()
            menor_f_caminhos = 46532179034260
            checked.append((new[0], new[1]))
            count = 0

            if (new[0], new[1] - 1) in self.visitedStates and not ((new[0], new[1] - 1) in checked):
                disponiveis.append((0, -1))
                count += 1

            if (new[0] + 1, new[1] - 1) in self.visitedStates and not ((new[0] + 1, new[1] - 1) in checked):
                disponiveis.append((1, -1))
                count += 1

            if (new[0] + 1, new[1]) in self.visitedStates and not ((new[0] + 1, new[1]) in checked):
                disponiveis.append((1, 0))
                count += 1

            if (new[0] + 1, new[1] + 1) in self.visitedStates and not ((new[0] + 1, new[1] + 1) in checked):
                disponiveis.append((1, 1))
                count += 1

            if (new[0], new[1] + 1) in self.visitedStates and not ((new[0], new[1] + 1) in checked):
                disponiveis.append((0, 1))
                count += 1

            if (new[0] - 1, new[1] + 1) in self.visitedStates and not ((new[0] - 1, new[1] + 1) in checked):
                disponiveis.append((-1, 1))
                count += 1

            if (new[0] - 1, new[1]) in self.visitedStates and not ((new[0] - 1, new[1]) in checked):
                disponiveis.append((-1, 0))
                count += 1

            if (new[0] - 1, new[1] - 1) in self.visitedStates and not ((new[0] - 1, new[1] - 1) in checked):
                disponiveis.append((-1, -1))
                count += 1

            #  Após testar todas as posições disponíveis, itera sobre elas para ver qual está mais perto da base

            while len(disponiveis) != 0:
                nextPos = disponiveis.pop()
                if nextPos[0] != 0 and nextPos[1] != 0:
                    g = self.COST_DIAG
                    f = g + self.COST_BACK + self.costH((new[0] + nextPos[0], new[1] + nextPos[1]), (0, 0))
                else:
                    g = self.COST_LINE
                    f = g + self.COST_BACK + self.costH((new[0] + nextPos[0], new[1] + nextPos[1]), (0, 0))

                if f < menor_f_caminhos:  # Se achou um caminho menor armazena em menor_f_caminhos
                    menor_f_caminhos = f
                    self.menor_f_base = f  # Dá pra tirar acho
                    x = nextPos[0]
                    y = nextPos[1]

            if count > 0:  # Tendo opções pra ir, vai pra melhor escolhida (mais proxima da base). Ps: percebi que dá pra usar o len(disponiveis).
                home.append((x, y))
                position.append((new[0] + x, new[1] + y))
                self.COST_BACK += g
            else:  # Não tendo opções volta até ter uma.
                self.COST_BACK -= g
                a = home.pop()
                position.append((new[0] - a[0], new[1] - a[1]))
            # print(checked)
            # print("X:", x, "Y:", y)
            # print("POSICAO NOVA:", position)
            if (new[0] + x) == 0 and (new[1] + y) == 0:  # Se chegou na base, acabou.
                break

        print("CUSTO para voltar:", self.COST_BACK)
        print("AINDA possuo:", self.rtime)
        if 4 < (self.rtime - self.COST_BACK):  # Teste para ver se a bateria esta acabando, dado que ele precisa fazer um movimento de volta, precisa sobrar o suficiente para uma ação (explico melhor no whats se precisar)
            self.pathHome = []
            self.pathHome = list(reversed(home))
            print("HOME:", self.pathHome)
        else:  # Bateria acabando, hora de voltar pra base, faz mais uma ação de volta ainda.
            newstate = self.unback.pop()
            dx = newstate[0]
            dy = newstate[1]
            result = self.body.walk(dx, dy)
            self.x += dx
            self.y += dy
            self.voltar = True

    def deliberate(self) -> bool:
        """ The agent chooses the next action. The simulator calls this
        method at each cycle. Must be implemented in every agent"""

        dx = 0
        dy = 0

        actions = []  # lista de ações possiveis
        position = []
        # No more actions, time almost ended
        if self.voltar:
            print("PAREI na posicao:", self.x, ",", self.y)
            print("CAMINHO para casa:", self.pathHome)
            # time to wake up the rescuer
            # pass the walls and the victims (here, they're empty)
            print(f"{self.NAME} I believe I've remaining time of {self.rtime:.1f}")
            while len(self.pathHome) != 0:
                newstate = self.pathHome.pop()
                dx = newstate[0]
                dy = newstate[1]
                result = self.body.walk(dx, dy)
                self.x += dx
                self.y += dy
            self.resc.go_save_victims(self.map, self.victims, self.max_x, self.max_y)
            return False

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
                if not ((self.x + pos[0], self.y + pos[
                    1]) in self.visitedStates):  # Se a posição que ele quer ir, não foi visitada, pode ir pra actions
                    actions.append(pos)
            elif obstacles[i] == 1:
                if not (self.x + pos[0], self.y + pos[1]) in self.walls:
                    self.walls.append((self.x + pos[0], self.y + pos[1]))
                    # adicionando parede ao mapa
                    self.map.append((self.x + pos[0], self.y + pos[1], 1))
            else:
                if not pos in self.ends:
                    self.ends.append(pos)
                    # adicionando fins ao mapa
                    self.map.append((self.x + pos[0], self.y + pos[1], 2))

        if not len(actions) == 0:
            newstate = random.choice(actions)  # Escolhe aleatoriamente uma ação
            dx = newstate[0]
            dy = newstate[1]
            self.unback.append((-dx, -dy))
            self.allPositions.append((dx, dy))
            result = self.body.walk(dx, dy)


        else:  # Se não há ações disponíveis, ele volta uma posição com o 'self.unback.pop()'
            newstate = self.unback.pop()
            dx = newstate[0]
            dy = newstate[1]
            self.allPositions.append((dx, dy))
            result = self.body.walk(dx, dy)

        self.x += dx
        self.y += dy

        position.append((self.x, self.y))
        self.Astar(position)
        if len(position) != 0:
            position.pop()

        if not ((self.x,
                 self.y) in self.visitedStates) and not ((self.x,
                                                          self.y) in self.walls):  # Para caso a posição atual dele não esteja em 'visitedStates'
            self.visitedStates.append((self.x, self.y))

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
            print(self.name() + ": wall or grid limit reached")

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

        return True
