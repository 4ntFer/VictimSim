## EXPLORER AGENT
### @Author: Tacla, UTFPR
### It walks randomly in the environment looking for victims.

import sys
import os
import random
from abstract_agent import AbstractAgent
from physical_agent import PhysAgent
from abc import ABC, abstractmethod


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
        self.visitedStates = []
        self.ends = []
        self.walls = []
        self.unback = []
        self.victims = []  # (x,y,index)
        self.max_x = 0
        self.max_y = 0
        self.allPositions = []

        self.map = []  # Cada elemento da coleção é um conjunto de 3 valores
        # que representam respectivamente: a posição relativa à
        # base (x e y) e o elemento encontrado nela,
        # esse ultimo podendo ser CLEAR = 0, WALL = 1, END = 2
        # e VICTIM = 3

    def deliberate(self) -> bool:
        """ The agent chooses the next action. The simulator calls this
        method at each cycle. Must be implemented in every agent"""

        dx = 0
        dy = 0

        actions = []  # lista de ações possiveis

        # No more actions, time almost ended
        if self.rtime < self.TLIM / 2:
            # time to wake up the rescuer
            # pass the walls and the victims (here, they're empty)
            while len(self.allPositions) != 0 or self.body.x == 0 and self.body.y == 0:
                newstate = self.allPositions.pop()
                dx = newstate[0]
                dy = newstate[1]
                result = self.body.walk(-dx, -dy)
            print(f"{self.NAME} I believe I've remaining time of {self.rtime:.1f}")
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
                if not ((self.body.x + pos[0], self.body.y + pos[1]) in self.visitedStates):  # Se a posição que ele quer ir, não foi visitada, pode ir pra actions
                    actions.append(pos)
            elif obstacles[i] == 1:
                if not pos in self.walls:
                    self.walls.append(pos)
                    # adicionando parede ao mapa
                    self.map.append((self.body.x + pos[0], self.body.y + pos[1], 1))
            else:
                if not pos in self.ends:
                    self.ends.append(pos)
                    # adicionando fins ao mapa
                    self.map.append((self.body.x + pos[0], self.body.y + pos[1], 2))

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

        if not ((self.body.x,
                 self.body.y) in self.visitedStates):  # Para caso a posição atual dele não esteja em 'visitedStates'
            self.visitedStates.append((self.body.x, self.body.y))

        if self.body.x > self.max_x:
            self.max_x = self.body.x

        if self.body.y > self.max_y:
            self.max_y = self.body.y

        # Update remaining time
        if dx != 0 and dy != 0:
            self.rtime -= self.COST_DIAG
        else:
            self.rtime -= self.COST_LINE

        # Test the result of the walk action
        if result == PhysAgent.BUMPED:
            walls = 1  # build the map- to do
            # print(self.name() + ": wall or grid limit reached")

        if result == PhysAgent.EXECUTED:
            # check for victim returns -1 if there is no victim or the sequential
            # the sequential number of a found victim
            seq = self.body.check_for_victim()
            if seq >= 0:
                vs = self.body.read_vital_signals(seq)
                # vitima é representada por um conjunto de 3 valores.
                # (dx, dy, index)
                if not ((self.body.x, self.body.y, seq) in self.victims):
                    self.victims.append((self.body.x, self.body.y, seq))
                    self.map.append((self.body.x, self.body.y, 3))

                self.rtime -= self.COST_READ
                # print("exp: read vital signals of " + str(seq))
                # print(vs)
            else:
                # Inclui a posição livre no mapa
                self.map.append((self.body.x, self.body.y, 0))

        return True
