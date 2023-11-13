##  RESCUER AGENT
### @Author: Tacla (UTFPR)
### Demo of use of VictimSim
import math
import os
import random
import numpy as np
from abstract_agent import AbstractAgent
from physical_agent import PhysAgent

from matplotlib import pyplot as plt


## Classe que define o Agente Rescuer com um plano fixo
class Rescuer(AbstractAgent):
    def __init__(self, env, config_file, name):
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
        self.name = name
        self.walls = []
        self.ends = []
        self.victims = []  ## (x,y,seq,condição)
        self.know_space = []
        self.savedVicitms = []

        # Starts in IDLE state.
        # It changes to ACTIVE when the map arrives
        self.body.set_state(PhysAgent.IDLE)
        self.max_x = 0  # O máximo em X que o explorador chegou
        self.max_y = 0
        self.map_update_count = 0

    def go_save_victims(self, know_states, victims, ends, walls, cluster):
        """ The explorer sends the map containing the walls and
        victims' location. The rescuer becomes ACTIVE. From now,
        the deliberate method is called by the environment"""
        self.victims = victims
        self.know_space = know_states
        self.ends = ends
        self.walls = walls

        # print("Nome: ", self.name, "Cluster: ", cluster)

        road_map = self.build_road_map(cluster)

        self.planner(road_map)
        print(self.plan)

        self.body.set_state(PhysAgent.ACTIVE)

    def planner(self, road_map):
        """ A private method that calculates the walk actions to rescue the
        victims. Further actions may be necessary and should be added in the
        deliberata method"""

        # This is a off-line trajectory plan, each element of the list is
        # a pair dx, dy that do the agent walk in the x-axis and/or y-axis
        prev_victim = (0, 0)
        for victim_index in road_map:
            current_victim = self.victims[victim_index]
            partial_plan = super().Astar(
                (prev_victim[0], prev_victim[1]),  # origem
                (current_victim[0], current_victim[1]),  # destino
                self.know_space, self.walls, self.ends
            )

            prev_victim = current_victim

            self.plan = self.plan + partial_plan["path"]

        partial_plan = super().Astar(
            (prev_victim[0], prev_victim[1]),  # origem
            (0, 0),  # destino
            self.know_space, self.walls, self.ends
        )

        self.plan = self.plan + partial_plan["path"]

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
                if res:
                    for victim in self.victims:
                        if victim[2] == seq and not (victim[0], victim[1], victim[2], victim[3]) in self.savedVicitms:
                            self.savedVicitms.append((victim[2], victim[0], victim[1], 0, victim[3]))

        return True

    def build_road_map(self, cluster):

        ## State/cromossomos do AG é um vetor que diz a ordem quem que as vitimas são visitadas

        ## Iniciando primeira geração com cromossomos aleatórios

        ### Quantos cromossomos iniciais?
        init_n_states = math.factorial(len(cluster))
        bound = 80
        gen = {0: {"Individuo": [], "Fitness": 1}}
        fitnessIndividual = 0
        ## Encapsular o individuo é uma boa ideia para não precisar recalcular o seu fitness
        i = 0
        repeated = False
        while i < init_n_states and i < bound:
            individual = []

            while len(individual) < len(cluster):
                random_victim = cluster[random.randint(0, len(cluster) - 1)]

                while random_victim in individual:
                    random_victim = cluster[random.randint(0, len(cluster) - 1)]

                individual.append(random_victim)

            while not repeated:
                for individuals in list(gen):
                    if individual == gen[individuals]["Individuo"]:
                        repeated = True

            print(repeated, i)

            if repeated:
                continue

            fitnessIndividual = self.calc_fitness(individual)
            if fitnessIndividual < 0:
                individual.pop()
                continue

            if not repeated:
                gen[i] = {"Individuo": individual, "Fitness": fitnessIndividual}
                i = i + 1

            repeated = False

        ##quantas iterações? quanto é o fitness ideal?

        for i in range(10):  ## Encontrar condição
            if len(gen) <= 2:
                break
            print("Iteração:", i)
            survivors = self.natural_selection(gen)
            gen = self.crossover(survivors, cluster)

        max_fitness = 0
        individual_w_max_fitness = None
        for individual in gen:
            if gen[individual]["Fitness"] > max_fitness:
                individual_w_max_fitness = gen[individual]["Individuo"]
                max_fitness = gen[individual]["Fitness"]

        return individual_w_max_fitness

    def natural_selection(self, gen):
        ## Por roleta de sorteio
        total_fitness = 0
        final_interval = 0.0
        n_survivors = math.ceil(len(gen) / 2)  # a definir
        # n_survivors = len(gen) * 0.6
        individual_portion = []
        fitnessSurvivor = 0
        repeated = False
        survivors = {0: {"Individuo": [], "Fitness": 0}}
        j = 0
        for individual in list(gen):
            total_fitness = total_fitness + gen[individual]["Fitness"]

        init_interval = 0

        for individual in list(gen):
            final_interval = init_interval + gen[individual]["Fitness"]
            individual_portion.append((init_interval, final_interval))
            init_interval = final_interval

        while len(survivors) < n_survivors:
            rand = random.uniform(0, total_fitness)
            survivor = None

            for i in range(len(individual_portion)):
                if individual_portion[i][0] < rand < individual_portion[i][1]:
                    survivor = gen[i]["Individuo"]
                    fitnessSurvivor = gen[i]["Fitness"]

            for individuals in list(survivors):
                if survivor == survivors[individuals]["Individuo"]:
                    repeated = True

            if not repeated and survivor is not None:
                survivors[j] = {"Individuo": survivor, "Fitness": fitnessSurvivor}
                j = j + 1

            repeated = False

        return survivors

    def crossover(self, gen, cluster):
        lenGenOld = len(gen)
        lenGen = len(gen)
        new_gen = gen.copy()
        j = 0
        i = 0
        # 5% de chance de ocorrer mutação no filho 1 ou no filho 2, mutação baseada em ordem
        mutation1 = random.randint(0, 19)
        mutation2 = random.randint(0, 19)
        swapFather1 = []
        swapFather2 = []
        while len(new_gen) < (lenGenOld*2):
            father1 = random.randint(0, (lenGenOld - 1))
            father2 = random.randint(0, (lenGenOld - 1))

            while father2 == father1:  # garantindo que vai gerar indices diferentes
                father2 = random.randint(0, (lenGenOld - 1))

            crossoverRange = random.randint(2, len(cluster) - 1)

            new_gen[lenGen] = {"Individuo": gen[father2]["Individuo"].copy()}  # Filho 1
            new_gen[lenGen + 1] = {"Individuo": gen[father1]["Individuo"].copy()}  # Filho 2

            for j in range(0, crossoverRange):
                new_gen[lenGen]["Individuo"][j] = gen[father1]["Individuo"][j]
                for k in range(crossoverRange, len(new_gen[lenGen]["Individuo"])):
                    if new_gen[lenGen]["Individuo"][j] == new_gen[lenGen]["Individuo"][k]:
                        swapFather1.append(k)

                new_gen[lenGen + 1]["Individuo"][j] = gen[father2]["Individuo"][j]
                for k in range(crossoverRange, len(new_gen[lenGen + 1]["Individuo"])):
                    if new_gen[lenGen + 1]["Individuo"][j] == new_gen[lenGen + 1]["Individuo"][k]:
                        swapFather2.append(k)

            while len(swapFather1) > 0:
                index1 = swapFather1.pop()
                index2 = swapFather2.pop()
                auxiliar = new_gen[lenGen]["Individuo"][index1]
                new_gen[lenGen]["Individuo"][index1] = new_gen[lenGen + 1]["Individuo"][index2]
                new_gen[lenGen + 1]["Individuo"][index2] = auxiliar

            mutation = random.randint(0, 19)
            if mutation1 == mutation:
                indexMutation1 = random.randint(0, len(new_gen[lenGen]["Individuo"]) - 1)
                indexMutation2 = random.randint(0, len(new_gen[lenGen]["Individuo"]) - 1)
                while indexMutation2 == indexMutation1:  # garantindo que vai gerar indices diferentes
                    indexMutation2 = random.randint(0, len(new_gen[lenGen]["Individuo"]) - 1)
                auxiliarMutation = new_gen[lenGen]["Individuo"][indexMutation1]
                new_gen[lenGen]["Individuo"][indexMutation1] = new_gen[lenGen]["Individuo"][indexMutation2]
                new_gen[lenGen]["Individuo"][indexMutation2] = auxiliarMutation

            if mutation2 == mutation:
                indexMutation1 = random.randint(0, len(new_gen[lenGen + 1]["Individuo"]) - 1)
                indexMutation2 = random.randint(0, len(new_gen[lenGen + 1]["Individuo"]) - 1)
                while indexMutation2 == indexMutation1:  # garantindo que vai gerar indices diferentes
                    indexMutation2 = random.randint(0, len(new_gen[lenGen + 1]["Individuo"]) - 1)
                auxiliarMutation = new_gen[lenGen + 1]["Individuo"][indexMutation1]
                new_gen[lenGen + 1]["Individuo"][indexMutation1] = new_gen[lenGen + 1]["Individuo"][indexMutation2]
                new_gen[lenGen + 1]["Individuo"][indexMutation2] = auxiliarMutation

            new_gen[lenGen]["Fitness"] = self.calc_fitness(new_gen[lenGen]["Individuo"])
            new_gen[lenGen + 1]["Fitness"] = self.calc_fitness(new_gen[lenGen + 1]["Individuo"])
            mutation1 = random.randint(0, 19)
            mutation2 = random.randint(0, 19)
            lenGen += 2

        return new_gen

    def calc_fitness(self, states):
        saved_victims = len(states)
        cost = 0

        if None in states:
            return 0

        victim_pos = (self.victims[states[0]][0], self.victims[states[0]][1])  ## (x,y)
        cost = self.Astar((0, 0), victim_pos, self.know_space, self.walls, self.ends)["cost"]

        for i in range(len(states) - 1):
            origin = victim_pos
            victim_pos = (self.victims[states[i + 1]][0], self.victims[states[i + 1]][1])  ## (x,y)
            cost = cost + self.Astar(origin, victim_pos, self.know_space, self.walls, self.ends)["cost"]

        origin = victim_pos
        cost = cost + self.Astar(origin, (0, 0), self.know_space, self.walls, self.ends)["cost"]

        return saved_victims * (self.rtime + 1 - cost)
