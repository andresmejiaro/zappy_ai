import json


class Party():
    def __init__(self, agent):
        self.agent = agent
        self.reset_party()
        
    def set_party_size(self,lv):
        ps =[1,2,2,4,4,6,6,1]
        return ps[lv-1]
    
    def party_message_processer(self, message, direction):
        processers = {
            "lfg": self.bc_lfg_processer,#generated
            "join": self.bc_join_processer, #generated
            "inventory": self.bc_inventory_processer, #generated
            "closed": self.bc_closed_party, #generated
            "disband": self.bc_disband, #generated
            "ready": self.bc_incantation_ready
         }

        try:
            message_dict = json.loads(message)
        except Exception as e:
            print(f"Could not decript message {e}")
            return
        kind = message_dict.get("kind")
        if kind is not None and kind in processers.keys():
            processers[kind](message_dict, direction)
            return
        print("Recived random broadcast")



    def reset_party(self):
        """
        Resets variables related to the partys
        """
        self.party_name = None # for partying up
        self.party_role = 0 # 0 = none ,1 = applicant, 2=member, 3 = master
        self.party_members = [] #who is in our party
        self.party_inventories = {} #inventories of our party members
        self.colection_complete = False # is what we are doing done?
        self.party_size = self.set_party_size(self.agent.level) # party size limit 
        self.party_closed = False # did I send closing message
        self.party_inventory = {}  #agreate inventory
        self.party_members_ready = []

    def update_party_inventory(self):
        self.party_inventory = self.agent.inventory.copy()
        for key in self.party_inventory.keys():
            for inv in self.party_inventories.values():
                self.party_inventory[key] += inv.get(key,0) 

    def bc_lfg_processer(self, message_dict, direction):
        """
        Recieves messages of poosible lfg.

        Tested
        generator written
        """
        lvl = int(message_dict.get("lvl",-1))
        if self.party_closed == True:
            return
        if lvl != self.agent.level:
            return
        remote_name =message_dict.get("party_name")
        if self.party_name is not None:
            if remote_name < self.party_name:
                return
            else:
                self.reset_party()  
        self.party_name = remote_name
        self.party_role = 1
        
        

    def bc_join_processer(self,message_dict, direction):
        """
        generator written
        """
        if message_dict.get("party_name") != self.party_name and self.party_role != 3:
            return 
        if self.party_closed:
            return
        self.party_members.append(message_dict.get("name"))
        if len(self.party_members) >= self.party_size:
            while len(self.party_members) > self.party_size:
                self.party_members.pop()       

    def bc_inventory_processer(self, message_dict,direction):
        """
        tested
        generator written
        """
        member = message_dict.get("name")
        if member not in self.party_members:
            return
        inventory = message_dict.get("inventory")
        self.party_inventories[member] = inventory

    def bc_incantation_ready(self, message_dict, direction):
        """
        """
        if message_dict.get("party_name") != self.party_name:
            return 
        member = message_dict.get("name")
        if member not in self.party_members_ready:
            self.party_members_ready.append(member)
        self.sound_direction = direction
    # def bc_complete_processer(self,message_dict, direction):
    #     if message_dict.get("party_name") != self.party_name:
    #         return
    #     self.colection_complete = True

    def bc_closed_party(self, message_dict,direction):
        """
        Message to send when the party is full
        tested
        """       
        if message_dict.get("party_name") != self.party_name and self.party_role != 1:
            return
        if self.agent.name not in message_dict.get("members"):
            self.reset_party()
        self.party_role = 2
        self.party_closed = True
        self.party_members = message_dict.get("members")

    def bc_disband(self, message_dict,direction):
        """
        disbands if the leader says so

        tested
        """
        if message_dict.get("party_name") != self.party_name:
            return
        self.reset_party()

        
