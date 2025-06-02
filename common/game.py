from common import enums


def try_kill(player, target):
    attack = player.role.attack.value
    defense = target.role.defense.value
    if attack > defense:
        target.alive = False

class Player:
    def __init__(self, role, name, id):
        self.role = role
        self.name = name
        self.id = id
        self.alive = True

class Role:
    def __init__(self):
        self.name = "Role"
        self.description = "Role description."
        self.id = -1
        self.default_defense = enums.Defense.NONE
        self.defense = enums.Defense.NONE
        self.attack = enums.Attack.NONE
        self.alignment = enums.Alignment.TOWN
        self.priority = 0
    def ability(self, player, *args: Player):
        pass
    def on_night_end(self, player: Player):
        player.role.defense = player.role.default_defense
        pass


class Mafioso(Role):
    def __init__(self):
        super().__init__()
        self.name = "Mafioso"
        self.description = "The mafioso is the evil role of the town. He can kill someone every night."
        self.id = 1
        self.default_defense = enums.Defense.NONE
        self.defense = enums.Defense.NONE
        self.attack = enums.Attack.NONE
        self.alignment = enums.Alignment.MAFIA
        self.priority = 2
    def ability(self, player, *args: Player):
        try_kill(player, args[0])
    def on_night_end(self, player: Player):
        super().on_night_end(player)

class Doctor(Role):
    def __init__(self):
        super().__init__()
        self.name = "Doctor"
        self.description = "The doctor is the role of the doctors. He can try and protect someone every night."
        self.id = 3
        self.default_defense = enums.Defense.NONE
        self.defense = enums.Defense.NONE
        self.attack = enums.Attack.NONE
        self.alignment = enums.Alignment.TOWN
        self.priority = 1
    def ability(self, player, *args: Player):
        args[0].role.defense = enums.Defense.POWERFUL
    def on_night_end(self, player: Player):
        super().on_night_end(player)

class Sheriff(Role):
    def __init__(self):
        super().__init__()
        self.name = "Sheriff"
        self.description = "Sheriff can find out if someone is suspicious, or innocent."
        self.id = 2
        self.default_defense = enums.Defense.NONE
        self.defense = enums.Defense.NONE
        self.attack = enums.Attack.NONE
        self.alignment = enums.Alignment.TOWN
        self.priority = 3
    def ability(self, player, *args: Player):
        alignment = args[0].role.alignment
        if alignment == enums.Alignment.TOWN:
            return "This player is innocent."
        elif enums.Alignment.MAFIA or enums.Alignment.NEUTRAL:
            return "This player is suspicious."
    def on_night_end(self, player: Player):
        super().on_night_end(player)

class GameState:
    def __init__(self):
        self.players: list[Player] = []
        self.phase = enums.Phase.LOBBY
    def add_player(self, player: Player):
        self.players.append(player)

if __name__ == "__main__":
    print("THIS FILE IS NOT MEANT TO BE RUN")