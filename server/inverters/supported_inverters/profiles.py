"""
Maybe the get function below should return a class object? 
"""

from .inverters.sungrow import profile as sungrow
from .inverters.sungrow_hybrid import profile as sungrow_hybrid
from .inverters.solaredge import profile as solaredge
from .inverters.growatt import profile as growatt
from .inverters.huawei import profile as huawei
from .inverters.lqt40s import profile as lqt40s
import json as JSON

inverters = [sungrow, sungrow_hybrid, solaredge, growatt, huawei, lqt40s]


class RegisterInterval:
    def __init__(self, operation, start_register, offset):
        self.operation = operation
        self.start_register = start_register
        self.offset = offset


class InverterProfile:
    def __init__(self, inverter_profile):
        self.inverter_profile = inverter_profile
        self.name = self.inverter_profile["name"]
        self.registers = []

        for register_intervall in self.inverter_profile["registers"]:
            self.registers.append(
                RegisterInterval(register_intervall["operation"],
                                 register_intervall["start_register"],
                                 register_intervall["num_of_registers"])
            )

    def get(self):
        return self.profile


class InverterProfiles:
    def __init__(self):
        self.profiles = []

        for inverter in inverters:
            self.profiles.append(InverterProfile(inverter))

    def get(self, name) -> InverterProfile:
        for profile in self.profiles:
            if profile.name == name:
                return profile
        return None

    def get_supported_inverters(self):
        return [profile.name for profile in self.profiles]
