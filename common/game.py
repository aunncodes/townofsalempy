from common import enums


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

    def ability(self, player: Player, *args: Player):
        # Return a dict representing intent (server will execute this)
        return {"type": "none"}

    def on_night_end(self, player: Player):
        player.role.defense = player.role.default_defense


class Mafioso(Role):
    def __init__(self):
        super().__init__()
        self.name = "Mafioso"
        self.description = "The mafioso is the evil role of the town. He can kill someone every night."
        self.id = 1
        self.attack = enums.Attack.BASIC
        self.alignment = enums.Alignment.MAFIA
        self.priority = 2

    def ability(self, player: Player, target: Player):
        return {
            "type": "action_result",
            "actor": player.id,
            "target": target.id,
            "effect": "attack",
            "attack": self.attack.value
        }


class Doctor(Role):
    def __init__(self):
        super().__init__()
        self.name = "Doctor"
        self.description = "The doctor can protect someone each night."
        self.id = 3
        self.attack = enums.Attack.NONE
        self.alignment = enums.Alignment.TOWN
        self.priority = 1

    def ability(self, player: Player, target: Player):
        return {
            "type": "action_result",
            "actor": player.id,
            "target": target.id,
            "effect": "protect",
            "defense": enums.Defense.POWERFUL.value
        }


class Sheriff(Role):
    def __init__(self):
        super().__init__()
        self.name = "Sheriff"
        self.description = "Sheriff can find out if someone is suspicious, or innocent."
        self.id = 2
        self.attack = enums.Attack.NONE
        self.alignment = enums.Alignment.TOWN
        self.priority = 3

    def ability(self, player: Player, target: Player):
        alignment = target.role.alignment
        if alignment == enums.Alignment.TOWN:
            result_text = "This player is innocent."
        else:
            result_text = "This player is suspicious."
        return {
            "type": "action_result",
            "actor": player.id,
            "target": target.id,
            "effect": "investigate",
            "result": result_text
        }


class GameState:
    def __init__(self):
        self.players: list[Player] = []
        self.phase = enums.Phase.LOBBY

    def add_player(self, player: Player):
        self.players.append(player)
