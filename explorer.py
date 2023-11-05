## EXPLORER AGENT
### @Author: Tacla, UTFPR
### It walks randomly in the environment looking for victims.

import random
from abstract_agent import AbstractAgent
from physical_agent import PhysAgent
from math import sqrt
import math


class Explorer(AbstractAgent):
    visitados = [] # Todos os espaços visitados por todos os exploradores
    paredes = []  # todas paredes descobertas por todos os exploradores
    vitimas = []  # todas vitimas descobertas por todos os exploradores
    fins = []
    victims_for_clustering = []
    maxX = 0
    maxY = 0
    exploradoresBase = 0  # numero de exploradores que chegaram na base
    socorristasAcordar = []  # lista que guarda os socorristas a serem acordados

    def completaMapa(self, know_states, walls, victims, ends, resc):
        for i in walls:
            if not Explorer.paredes.__contains__(i):
                Explorer.paredes.append(i)

        for i in victims:
            if not Explorer.vitimas.__contains__(i):
                Explorer.vitimas.append(i)

        for i in ends:
            if not Explorer.fins.__contains__(i):
                Explorer.fins.append(i)

        for i in know_states:
            if not Explorer.visitados.__contains__(i):
                Explorer.visitados.append(i)

        Explorer.exploradoresBase += 1
        Explorer.socorristasAcordar.append(resc)
        for i in Explorer.vitimas:
            if not Explorer.victims_for_clustering.__contains__((i[0], i[1], i[3])):
                Explorer.victims_for_clustering.append(
                    (
                        i[0],
                        i[1],
                        i[3]
                    )
                )

        if self.max_x > Explorer.maxX:
            Explorer.maxX = self.max_x

        if self.max_y > Explorer.maxY:
            Explorer.maxY = self.max_y

        if Explorer.exploradoresBase == 4:
            cluster = Explorer.cluster(self, Explorer.victims_for_clustering, 4, Explorer.maxX, Explorer.maxY)
            i = 0
            for socorrista in Explorer.socorristasAcordar:
                socorrista.go_save_victims(Explorer.visitados, Explorer.vitimas, Explorer.fins, Explorer.paredes, cluster[i])
                i += 1

    def cluster(self, victims, k, max_x, max_y):
        centroides = []
        centroides_anteriores = [None] * k  # A distancia de cada vítima em relação ao centroide associado à ela
        x_axis = []
        y_axys = []
        cluster = []
        victim_centroid_distance = []

        for i in range(k):
            victim_centroid_distance.append([])
            for j in range(len(victims)):
                victim_centroid_distance[i].append(j)

        max_phys_dis = 100000  # Maior distancia física
        aux_dis = 0
        max_it = 100000
        it = 0

        # Determinando a vítima mais distante
        # for i in range(len(victims)):
        #    aux_dis = math.sqrt(victims[i][0] * victims[i][0] + victims[i][1] * victims[i][1])

        #    victims_phys_dis.append(aux_dis)

        #    if aux_dis > max_phys_dis:
        #        max_phys_dis = aux_dis

        for v in victims:
            x_axis.append(v[0])
            y_axys.append(v[1])

        # Determinando centroides em posições aleatórias
        for i in range(k):
            # 4 é a gravidade máxima dos ferimentos da vítima
            centroides.append(
                (
                    random.uniform(0.0, max_x + 1), random.uniform(0.0, max_y + 1)
                    # Mais um pois, max_x pode ser por exemplo, 19, então para incluir 19 no random, tem que aumentar em um, max_x e max_y
                )
            )

        not_chage_count = 0
        while it < max_it and not_chage_count < 20:
            cluster = []
            dots_x = []
            dots_y = []

            if centroides == centroides_anteriores:
                not_chage_count += 1

            for i in range(k):
                cluster.append([])

            # Calculando a distancia entre vítima e cada centroide

            for i in range(k):
                for j in range(len(victims)):
                    distance_of_i_centroid = Explorer.calcula_distancia(self, x_axis[j], y_axys[j], centroides[i][0],
                                                                        centroides[i][1])
                    victim_centroid_distance[i][j] = distance_of_i_centroid
                    # dots_x.append(victims_phys_dis[j])
                    # dots_y.append(victims[j][2])
                    dots_x.append(x_axis)
                    dots_y.append(y_axys)

            for i in range(len(victims)):
                cluster_index = 0
                min_dis = max_phys_dis * 4 / 2
                for j in range(k):
                    if min_dis > victim_centroid_distance[j][i]:
                        min_dis = victim_centroid_distance[j][i]
                        cluster_index = j

                cluster[cluster_index].append(i)

            # Calculando novos centroides
            for i in range(k):
                victim_dis_sum = 0
                victim_label_sum = 0
                new_cent_x = 0
                new_cent_y = 0

                if len(cluster[i]) > 0:
                    for j in range(len(cluster[i])):
                        victim_index = cluster[i][j]
                        # victim_dis_sum += victim_centroid_distance[i][victim_index]
                        # victim_label_sum += victims[victim_index][2]

                        victim_dis_sum += x_axis[victim_index]
                        victim_label_sum += y_axys[victim_index]

                    new_cent_x = victim_dis_sum / len(cluster[i])
                    new_cent_y = victim_label_sum / len(cluster[i])

                else:
                    new_cent_x = random.uniform(0.0, max_x + 1)
                    new_cent_y = random.uniform(0.0, max_y + 1)

                centroides_anteriores[i] = centroides[i]
                centroides[i] = (new_cent_x, new_cent_y)

            x = []
            y = []

            for cent in centroides:
                x.append(cent[0])
                y.append(cent[1])

            #  kmeans_visualize(x, y, dots_x, dots_y)

            it = it + 1

        # for c in cluster:
        # print(c)
        return cluster

    def calcula_distancia(self, x, y, x1, y1):
        c1 = 0
        c2 = 0

        c1 = x - x1
        c2 = y - y1

        return math.sqrt(c1 * c1 + c2 * c2)

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

            if not (atual[0] + 1, atual[1] - 1) in checado and (atual[0] + 1, atual[1] - 1) in self.visitedStates:
                fronteira.append((1, -1))

            if not (atual[0] + 1, atual[1]) in checado and (atual[0] + 1, atual[1]) in self.visitedStates:
                fronteira.append((1, 0))

            if not (atual[0] + 1, atual[1] + 1) in checado and (atual[0] + 1, atual[1] + 1) in self.visitedStates:
                fronteira.append((1, 1))

            if not (atual[0], atual[1] + 1) in checado and (atual[0], atual[1] + 1) in self.visitedStates:
                fronteira.append((0, 1))

            if not (atual[0] - 1, atual[1] + 1) in checado and (atual[0] - 1, atual[1] + 1) in self.visitedStates:
                fronteira.append((-1, 1))

            if not (atual[0] - 1, atual[1]) in checado and (atual[0] - 1, atual[1]) in self.visitedStates:
                fronteira.append((-1, 0))

            if not (atual[0] - 1, atual[1] - 1) in checado and (atual[0] - 1, atual[1] - 1) in self.visitedStates:
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
                else:
                    if not pos in self.ends:
                        self.ends.append((self.x + pos[0], self.y + pos[1]))

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
            self.pathHome = super().Astar(position, (0,0), self.visitedStates, self.walls, self.ends)

            if not ((self.x, self.y) in self.visitedStates) and not (
                    (self.x, self.y) in self.walls) and not (
                    (self.x, self.y) in self.ends):  # Para caso a posição atual dele não esteja em 'visitedStates'
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
                    if not ((self.x, self.y, seq, vs[7]) in self.victims):
                        self.victims.append((self.x, self.y, seq, vs[7]))

                    self.rtime -= self.COST_READ
                    # print("exp: read vital signals of " + str(seq))
                    # print(vs)
        else:
            if not self.voltar:
                self.voltar = True
            # print("PAREI na posicao:", self.x, ",", self.y)
            # print("CAMINHO para casa:", self.pathHome["path"])
            # time to wake up the rescuer
            # pass the walls and the victims (here, they're empty)
            # print(f"{self.name} I believe I've remaining time of {self.rtime:.1f}")
            homePos = self.pathHome["path"].pop(0)
            dx = homePos[0]
            dy = homePos[1]
            result = self.body.walk(dx, dy)
            self.x += dx
            self.y += dy

            if self.x == 0 and self.y == 0:
                Explorer.completaMapa(self, self.visitedStates, self.walls, self.victims, self.ends, self.resc)
                return False

        return True
