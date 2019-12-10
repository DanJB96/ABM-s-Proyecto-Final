import random
from mesa import Agent, Model
from mesa.time import RandomActivation
from mesa.space import MultiGrid
from mesa.datacollection import DataCollector


class miAgente(Agent): # Comenzamos definiendo a cada agente
    def __init__(self, pos, model, gender, beauty, wealth, desired_beauty, desired_wealth, time_to_critical, sojourn, is_critical):
        super().__init__(pos, model) 
        self.pos = pos
        self.gender = gender
        self.beauty = beauty
        self.wealth = wealth
        self.desired_beauty = desired_beauty
        self.desired_wealth = desired_wealth 
        self.time_to_critical = time_to_critical
        self.sojourn = -1
        self.is_critical = 0
        
    def step(self): # Modelamos el movimiento
        vecindad = self.model.grid.get_neighborhood(self.pos,moore=True,include_center=False)
        destino = random.choice(vecindad)
        self.model.grid.move_agent(self, destino)

        prospectos = self.model.grid.get_neighbors(self.pos,moore=True, include_center=True,radius=0)
        matches = [x for x in prospectos if type(x) is miAgente and x!=self and x.beauty>=self.desired_beauty and x.gender != self.gender and x.wealth >= self.desired_wealth]

        if len(matches)==1:  # Si encuentra pareja, desaparecen del grid
            self.model.schedule.remove(self)
            self.model.grid.remove_agent(self)
            self.model.parejas += 1 # Contabilizamos una pareja en la lista para futura recolección
            for m in matches: 
                self.model.schedule.remove(m)
                self.model.grid.remove_agent(m) 

        self.sojourn += 1
        if self.sojourn >= self.time_to_critical:
            self.is_critical = 1
            
        if self.is_critical == 1:
            self.model.unhappy_agents.append(self) 
            self.model.schedule.remove(self)
            self.model.grid.remove_agent(self)
            self.model.unhappy += 1
            
    def promedio_beauty_unhappy(model):
        sum_beauty = 0
        for a in model.schedule.agents:
            sum_beauty += a.beauty
        prom_beauty = sum_beauty/len(model.unhappy_agents)
        return prom_beauty
    
class LoveMatch(Model):
    '''
    Love-match market Model: 
    
    En este modelo, cada individuo recorre de manera aleatoria el lugar, al encontrarse con un match (agente del sexo opuesto con parámetros de belleza y riqueza coincidentes con lo deseado) desaparece del modelo. 
    El objetivo es observar la distribución de perfiles de belleza y riqueza a lo largo del tiempo hasta ver quienes no logran encontrar pareja. 
    '''
    def __init__(self, height=50, width=50, density=0.8, HM_pc=0.2, entry_rate=5, max_agents=250): # Aquí establecemos el tamaño del Grid donde se desarrolla el modelo, además de los parámetros iniciales.
        self.height = height
        self.width = width
        self.density = density
        self.HM_pc = HM_pc
        self.dummy = 0
        self.entry_rate = 5
            
        self.schedule = RandomActivation(self)
        self.grid = MultiGrid(height, width, torus=False)
        self.max_agents = max_agents
        self.parejas = 0
        self.unhappy = 0
        self.unhappy_agents = []
        max_agents = height*width
        

            
# En esta sección, etiquetamos a cada agente según su tipo 

        for cell in self.grid.coord_iter():
            x = cell[1]
            y = cell[2]
            if self.random.random() < self.density:
                if self.random.random() < self.HM_pc:
                    gender = 1 
                    
                else:
                    gender = 0
                   
                agent = miAgente((x, y), self, gender, beauty = random.gauss(0.5,0.15),
                                                         wealth = random.gauss(0.5,0.15),
                                                         desired_beauty = random.gauss(0.5,0.1), 
                                                         desired_wealth = random.gauss(0.5,0.1),
                                                         time_to_critical = random.gauss(20,5), 
                                                         sojourn = -1,
                                                         is_critical= 0)     
                self.schedule.add(agent)
                self.grid.place_agent(agent, (x,y))
        
        self.running = True
        self.datacollector = DataCollector(agent_reporters ={"wealth":"wealth"} )
        self.datacollector.collect(self)
                            
        
    def step(self):# Este step permite que el modelo siga corriendo hasta que todos los agentes tengan pareja
        self.schedule.step()
        if self.schedule.get_agent_count() < (self.max_agents-self.entry_rate):
            for cell in self.grid.coord_iter():
                n_x = cell[1]
                n_y = cell[2]
            for i in range(self.entry_rate):
                new_beauty = random.gauss(0.5,0.15)
                new_wealth = random.gauss(0.5,0.15)
                new_desired_beauty = random.gauss(0.5, 0.15)
                new_desired_wealth = random.gauss(0.5, 0.15)
                new_time_to_critical = random.gauss(20,5)
                new_sojourn = -1
                new_is_critical = 0

                if self.random.random() < self.HM_pc:
                    new_gender = 1 
                    
                else:
                    new_gender = 0
                
            new_agent = miAgente((n_x,n_y), i, 
                                 gender = new_gender, 
                                 beauty = new_beauty,
                                 wealth = new_wealth, 
                                 desired_beauty = new_desired_beauty,
                                 desired_wealth = new_desired_wealth,
                                 time_to_critical = new_time_to_critical,
                                 sojourn = new_sojourn,
                                 is_critical = new_is_critical )

            self.schedule.add(new_agent)
            self.grid.place_agent(new_agent, (n_x,n_y))
    
            self.dummy = self.schedule.get_agent_count()
            print(str(self.dummy))

        # Por fines gráficos, recolectamos la información sobre la cantidad de parejas
        self.datacollector.collect(self)
        
        self.datacollector.get_agent_vars_dataframe().to_csv("dc.csv")
        if self.schedule.get_agent_count() == 0: 
            self.running = False
