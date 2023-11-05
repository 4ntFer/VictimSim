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

        self.walls = []
        self.ends = []
        self.victims = [] ## (x,y,seq,condição)
        self.know_space = []

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
        prev_victim = (0,0)
        for victim_index in road_map:
            current_victim = self.victims[victim_index]
            partial_plan = super().Astar(
                (prev_victim[0], prev_victim[1]), #origem
                (current_victim[0], current_victim[1]), #destino
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

        return True

    def build_road_map(self, cluster):

        ## State/cromossomos do AG é um vetor que diz a ordem quem que as vitimas são visitadas

        ## Iniciando primeira geração com cromossomos aleatórios

        ### Quantos cromossomos iniciais?

        init_n_states = 80

        gen = []

        ## Encapsular o individuo é uma boa ideia para não precisar recalcular o seu fitness
        i = 0
        while i < init_n_states:
            individual = []

            while self.calc_fitness(individual) >= 0 and len(individual) < len(cluster):
                random_victim = cluster[random.randint(0, len(cluster) - 1)]

                while random_victim in individual:
                    random_victim = cluster[random.randint(0, len(cluster) - 1)]

                individual.append(random_victim)

            if self.calc_fitness(individual) < 0:
                individual.pop()

            if not individual in gen:
                gen.append(individual)
                i = i + 1


        ##quantas iterações? quanto é o fitness ideal?

        for i in range(10): ## Encontrar condição
            survivors = self.natural_selection(gen)
            gen = self.crossover(survivors, cluster)

        max_fitness = 0
        individual_w_max_fitness = None
        for individual in gen:
            if self.calc_fitness(individual) > max_fitness:
                individual_w_max_fitness = individual
                max_fitness = self.calc_fitness(individual)

        return individual_w_max_fitness


    def natural_selection(self, gen):
        ## Por roleta de sorteio
        total_fitness = 0
        n_survivors = math.ceil(len(gen)/2) # a definir
        individual_portion = []
        survivors = []

        for individual in gen:
            total_fitness = total_fitness + self.calc_fitness(individual)

        init_interval =  0

        for individual in gen:
            final_interval = init_interval + total_fitness / self.calc_fitness(individual)
            individual_portion.append((init_interval, final_interval))
            init_interval = final_interval


        while len(survivors) < n_survivors:
            rand = random.randint(0,total_fitness)
            survivor = None


            for i in range(len(individual_portion)):
                if rand > individual_portion[i][0] and rand < individual_portion[i][1]:
                    survivor = gen[i]

            if not survivor in survivors and survivor != None:
                survivors.append(survivor)

        return survivors

    def crossover(self, gen,  cluster):
        #Baseado em ordem
        new_gen = []

        for father in gen:
            for j in range(2):
                n_inherited = int(len(father)/2)
                inherited = []
                individual_son = []

                i = 0
                while i < n_inherited:
                    index = random.randint(0, n_inherited)

                    if not index in inherited:
                        inherited.append(index)
                        i = i + 1

                while self.calc_fitness(individual_son) >= 0 and len(individual_son) < len(cluster):
                    random_victim = cluster[random.randint(0, len(cluster) - 1)]

                    while random_victim in individual_son:
                        random_victim = cluster[random.randint(0, len(cluster) - 1)]

                    individual_son.append(random_victim)

                if self.calc_fitness(individual_son) < 0:
                    individual_son.pop()


                for index in inherited:
                    if father[index] in individual_son:
                        index_on_son = individual_son.index(father[index])
                        random_index = random.randint(0, len(individual_son) - 1)

                        individual_son[random_index] = individual_son[index]
                        individual_son[index] = father[index]

                    else:
                        individual_son[index] = father[index]

                new_gen.append(individual_son)


        n_mutation = int(len(new_gen) * 0.05)

        individual_mutants = []

        i = 0
        while i < n_mutation:
            index = random.randint(0, len(new_gen) - 1)

            if not index in individual_mutants:
                individual_mutants.append(index)
                i = i + 1

        for index in individual_mutants:
            atributeA = random.randint(0, len(new_gen[index]) - 1)
            atributeB = random.randint(0, len(new_gen[index]) - 1)

            while atributeB == atributeA:
                atributeB = random.randint(0, len(new_gen[index]) - 1)

            aux = new_gen[index][atributeA]

            new_gen[index][atributeA] = new_gen[index][atributeB]
            new_gen[index][atributeB] = aux

        return new_gen



    def calc_fitness(self, states):
        saved_victims = len(states)
        cost = 0

        if None in states:
            return 0

        victim_pos = (self.victims[0][0], self.victims[0][1]) ## (x,y)
        cost = self.Astar((0,0), victim_pos, self.know_space, self.walls, self.ends)["cost"]

        for i in range(len(states)-1):
            origin = victim_pos
            victim_pos = victim_pos = (self.victims[i+1][0], self.victims[i+1][1]) ## (x,y)
            cost = cost + self.Astar(origin, victim_pos, self.know_space, self.walls, self.ends)["cost"]

        origin = victim_pos
        cost = cost + self.Astar(origin, (0,0), self.know_space, self.walls, self.ends)["cost"]

        return saved_victims*(self.rtime + 1 - cost)