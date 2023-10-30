##  RESCUER AGENT
### @Author: Tacla (UTFPR)
### Demo of use of VictimSim
import math
import os
import random
from abstract_agent import AbstractAgent
from physical_agent import PhysAgent

from matplotlib import pyplot as plt




## Classe que define o Agente Rescuer com um plano fixo
class Rescuer(AbstractAgent):
    def __init__(self, env, config_file):
        """ 
        @param env: a reference to an instance of the environment class
        @param config_file: the absolute path to the agent's config file"""

        super().__init__(env, config_file)

        # Specific initialization for the rescuer
        self.plan = []  # a list of planned actions
        self.rtime = self.TLIM  # for controlling the remaining time
        self.unificated_map = []  # Cada elemento da coleção é um conjunto de 3 valores
        # que representam respectivamente: a posição relativa à
        # base (x e y) e o elemento encontrado nela,
        # esse ultimo podendo ser CLEAR = 0, WALL = 1, END = 2
        # e VICTIM = 3

        # Starts in IDLE state.
        # It changes to ACTIVE when the map arrives
        self.body.set_state(PhysAgent.IDLE)
        self.max_x = 0  # O máximo em X que o explorador chegou
        self.max_y = 0
        self.map_update_count = 0

        # planning
        self.__planner()

    def go_save_victims(self, mapa, victims, max_x, max_y):
        """ The explorer sends the map containing the walls and
        victims' location. The rescuer becomes ACTIVE. From now,
        the deliberate method is called by the environment"""
        victims_for_clustering = []
        
        self.update_map(mapa)
        self.map_update_count+=1
        # print("Mapa: ", self.unificated_map)

        self.max_x = max_x
        self.max_y = max_y

        for i in self.unificated_map:
            if i[2] == 3:
                victims_for_clustering.append(
                    (
                        i[0],
                        i[1],
                        self.body.read_vital_signals(i[2])[len(self.body.read_vital_signals(i[2])) - 1]
                    )
                )
        
        if(self.map_update_count == 4):
            self.clustering(victims_for_clustering, 4)

        self.body.set_state(PhysAgent.ACTIVE)

    def __planner(self):
        """ A private method that calculates the walk actions to rescue the
        victims. Further actions may be necessary and should be added in the
        deliberata method"""

        # This is a off-line trajectory plan, each element of the list is
        # a pair dx, dy that do the agent walk in the x-axis and/or y-axis
        self.plan.append((0, 1))
        self.plan.append((1, 1))
        self.plan.append((1, 0))
        self.plan.append((1, -1))
        self.plan.append((0, -1))
        self.plan.append((-1, 0))
        self.plan.append((-1, -1))
        self.plan.append((-1, -1))
        self.plan.append((-1, 1))
        self.plan.append((1, 1))

    def deliberate(self) -> bool:
        """ This is the choice of the next action. The simulator calls this
        method at each reasonning cycle if the agent is ACTIVE.
        Must be implemented in every agent
        @return True: there's one or more actions to do
        @return False: there's no more action to do """

        # No more actions to do
        if self.plan == []:  # empty list, no more actions to do
            return False

        # Takes the first action of the plan (walk action) and removes it from the plan
        dx, dy = self.plan.pop(0)

        # Walk - just one step per deliberation
        result = self.body.walk(dx, dy)

        # Rescue the victim at the current position
        if result == PhysAgent.EXECUTED:
            # check if there is a victim at the current position
            seq = self.body.check_for_victim()
            if seq >= 0:
                res = self.body.first_aid(seq)  # True when rescued

        return True

    # Recebe um novo mapa enviado por um explorador
    def update_map(self, map):
        for i in map:
            if not self.unificated_map.__contains__(i):
                self.unificated_map.append(i)

    def clustering(self, victims, k):
        centroides = []
        centroides_anteriores = [None] * k  # A distancia de cada vítima em relação ao centroide associado à ela
        victims_phys_dis = []
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
                    random.uniform(0.0, self.max_x + 1), random.uniform(0.0, self.max_y + 1)  # Mais um pois, max_x pode ser por exemplo, 19, então para incluir 19 no random, tem que aumentar em um, max_x e max_y
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
                    # distance_of_i_centroid = self.calcula_distancia(victims_phys_dis[j], victims[j][2], centroides[i][0],centroides[i][1])
                    distance_of_i_centroid = self.calcula_distancia(x_axis[j], y_axys[j], centroides[i][0],
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
                    new_cent_x = random.uniform(0.0, self.max_x + 1)
                    new_cent_y = random.uniform(0.0, self.max_y + 1)

                centroides_anteriores[i] = centroides[i]
                centroides[i] = (new_cent_x, new_cent_y)

            x = []
            y = []

            for cent in centroides:
                x.append(cent[0])
                y.append(cent[1])

            #  self.kmeans_visualize(x, y, dots_x, dots_y)

            it = it + 1

        for c in cluster:
            print(c)



    def calcula_distancia(self, x, y, x1, y1):
        c1 = 0
        c2 = 0

        c1 = x - x1
        c2 = y - y1

        return math.sqrt(c1 * c1 + c2 * c2)

    def kmeans_visualize(self, cx, cy, vx, vy):
        plt.clf()
        plt.scatter(vx, vy)
        plt.scatter(cx,cy)
        plt.ion()
        plt.show()
        plt.pause(0.5)