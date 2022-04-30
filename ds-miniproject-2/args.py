from commands import *


class ArgsParser():

    def __init__(self, primary, nodes):
        self.primary = primary
        aoc, gsic, gsc, gkc, gac, ec = \
            ActualOrderCommand(), \
            GStateIdCommand(), \
            GStateCommand(), \
            GKillCommand(nodes), \
            GAddCommand(nodes), \
            ExitCommand(nodes)

        self.commands = {
            hash(aoc): aoc,
            hash(gsic): gsic,
            hash(gsc): gsc,
            hash(gkc): gkc,
            hash(gac): gac,
            hash(ec): ec
        }

    def is_valid_command(self, command):
        """
        Returns True if a given command exists
        and is valid. Returns False otherwise
        """

        args = command.split(" ")
        name, n_params = args[0], len(args) - 1
        _hash = hash(name + str(n_params))
        if _hash in self.commands:
            command = self.commands[_hash]
            return command.is_valid(args[1:])
        return False

    def get_usage(self, optional_message=""):
        """
        Returns the list of available commands along with
        their allowed parameters and description
        """

        result = ""
        if optional_message != "":
            result += optional_message + "\n"
        result += "List of available commands: " + "\n"
        for c in sorted(self.commands, key=lambda x: self.commands[x].name and self.commands[x].name == "exit"):
            result += str(self.commands[c]) + "\n"
        return result

    def execute(self, command):
        """
        Executes a given command if it exists
        and is valid. Returns the result or False
        """
        
        args = command.split(" ")
        name, n_params = args[0], len(args) - 1
        _hash = hash(name + str(n_params))
        if _hash in self.commands:
            command = self.commands[_hash]
            result = command.execute(args[1:], self.primary)
            if args[0] == "g-kill" and result is not None:
                self.primary = result
            return result
        return False
