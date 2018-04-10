#################################################################################
# Software License Agreement (BSD License)
#
# Copyright (c) 2016, Francesco Rovida
# All rights reserved.
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are met:
#
# * Redistributions of source code must retain the above copyright
#   notice, this list of conditions and the following disclaimer.
# * Redistributions in binary form must reproduce the above copyright
#   notice, this list of conditions and the following disclaimer in the
#   documentation and/or other materials provided with the distribution.
# * Neither the name of the copyright holder nor the
#   names of its contributors may be used to endorse or promote products
#   derived from this software without specific prior written permission.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS" AND
# ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
# WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
# DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT OWNER OR CONTRIBUTORS BE LIABLE FOR
# ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES
# (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES;
# LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND
# ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT
# (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS
# SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
#################################################################################

import subprocess
import os
from os import walk, remove

class PddlTypes(object):
    __slots__ = '_types'

    def __init__(self):
        self._types = {}

    def addType(self, name, supertype):
        if name==supertype:
            return
        if not self._types.has_key(supertype):
            self._types[supertype] = []
        if not name in self._types[supertype]:
            self._types[supertype].append(name)

    def toPddl(self):
        string = "(:types \n"
        for supertype, types in self._types.iteritems():
            string += '\t'
            string += ' '.join(types)
            string += " - {}\n".format(supertype)
        string += ")"
        return string

class Predicate(object):
    __slots__ = 'name', 'params', 'negated', 'operator', 'value', 'abstracts'

    def __eq__(self, other):
        if self.name!=other.name:
            return False
        return True

    def __ne__(self, other):
        return not self.__eq__(other)

    def __init__(self, predicate, params, abstracts):
        self.name = predicate.getProperty("skiros:appliedOnType").value
        self.operator = None
        self.value = None
        self.abstracts = abstracts
        self.negated = not predicate.getProperty("skiros:desiredState").value
        self.params = []
        sub = predicate.getProperty("skiros:hasSubject").value
        self.params.append({"paramType": "x", "key": sub, "valueType": params[sub]})
        if predicate.hasProperty("skiros:hasObject"):
            obj = predicate.getProperty("skiros:hasObject").value
            self.params.append({"paramType": "y", "key": obj, "valueType": params[obj]})
        if predicate.hasProperty("skiros:operator"):
            self.operator = predicate.getProperty("skiros:operator").value
            self.value = predicate.getProperty("skiros:desiredValue").value

    def isFunction(self):
        return self.operator!=None and not isinstance(self.value, str)

    def toActionPddl(self):
        string = ''
        if self.negated:
            string += '(not '
        if self.isFunction():
            string += '({} '.format(self.operator)
        if isinstance(self.value, str):
            string += '({}'.format(self.value)
        else:
            string += '({}'.format(self.name)
        for p in self.params:
            string += ' ?{}'.format(p["key"])
        if self.isFunction():
            string += ') {}'.format(self.value)
        if self.negated:
            string += ')'
        string += ")"
        return string

    def toUngroundPddl(self):
        if isinstance(self.value, str):
            string = '({}'.format(self.value)
        else:
            string = '({}'.format(self.name)
        for p in self.params:
            string += ' ?{} - {} '.format(p["paramType"], p["valueType"])
        string += ")"
        return string

class GroundPredicate(object):
    __slots__ = 'name', 'params', 'operator', 'value'

    def __init__(self, name, params, operator=None, value=None):
        self.name = name
        self.params = params
        self.operator = operator
        self.value = value

    def isFunction(self):
        return self.operator!=None and not isinstance(self.value, str)

    def toPddl(self):
        string = ''
        if self.isFunction():
            string += '({} '.format(self.operator)
        if isinstance(self.value, str):
            string += '({}'.format(self.value)
        else:
            string += '({}'.format(self.name)
        for p in self.params:
            string += ' {}'.format(p)
        if self.isFunction():
            string += ') {}'.format(self.value)
        string += ")"
        return string

class ForallPredicate(object):
    __slots__ = 'predicate'

    def __init__(self, predicate):
        self.predicate = predicate

    def toPddl(self):
        return self.predicate

class Action(object):
    __slots__ = 'name', 'params', 'preconditions', 'effects'

    def __init__(self, skill, params, precons, postcons):
        self.name = skill._label
        self.params = params
        self.preconditions = precons
        self.effects = postcons

    def __eq__(self, other):
        if self.name!=other.name:
            return False
        return True

    def __ne__(self, other):
        return not self.__eq__(other)

    def toPddl(self):
        string = '(:durative-action {}\n'.format(self.name)
        string += "\t:parameters ("
        for p, t in self.params.iteritems():
            string += "?{} - {} ".format(p, t)
        string += ")\n"
        string +='\t:duration (= ?duration 1)\n'
        string += '\t:condition (and\n'
        for p in self.preconditions:
            string += '\t\t(at start {})\n'.format(p.toActionPddl())
        string += "\t)\n"
        string += "\t:effect (and\n"
        for e in self.effects:
            string += '\t\t(at end {})\n'.format(e.toActionPddl())
        string += "\t)\n"
        string += ")\n"
        return string


class PddlInterface:
    """
    Class to manage a pddl domain and do task planning

    It generates a pddl definition and invoke a task planner
    """
    def __init__(self, workspace, title="untitled"):
        self._title = title
        self._workspace = workspace
        self.clear()

    def clear(self):
        self._types = PddlTypes()
        self._objects = {}
        self._functions = []
        self._predicates = []
        self._actions = []
        self._init_state = []
        self._goal = []

    def _addSuperTypes(self, predicate):
        lookuplist = self._predicates
        if predicate.isFunction():
            lookuplist = self._functions
        for p in lookuplist:
            if p==predicate:
                for param1, param2 in zip(p.params, predicate.params):
                    if param1["valueType"]!=param2["valueType"]:
                        supertypeId = p.name+param1["paramType"]
                        self._types.addType(param1["valueType"], supertypeId)
                        self._types.addType(param2["valueType"], supertypeId)
                        param1["valueType"] = supertypeId
                return

    def addType(self, name, supertype):
        self._types.addType(name, supertype)

    def addUngroundPredicate(self, predicate):
        if predicate.isFunction():
            self.addFunction(predicate)
            return
        if not predicate in self._predicates:
            self._predicates.append(predicate)
        else:
            self._addSuperTypes(predicate)

    def addFunction(self, function):
        if not function in self._functions:
            self._functions.append(function)
        else:
            self._addSuperTypes(function)

    def addAction(self, action):
        if not action in self._actions and action.preconditions and action.effects:
            for k, p in action.params.iteritems():
                self.addType(p, "thing")
            for c in action.preconditions:
                self.addUngroundPredicate(c)
            for c in action.effects:
                self.addUngroundPredicate(c)
            self._actions.append(action)

    def setObjects(self, objects):
        self._objects = objects

    def setInitState(self, init):
        self._init_state = init

    def addGoal(self, g):
        self._goal.append(g)

    def printDomain(self, to_file=False):
        string = "(define (domain {})\n".format(self._title)
        string += "(:requirements :typing :fluents :universal-preconditions)\n" #TODO: make this dynamic?
        string += self._types.toPddl()
        string += "\n"
        string += "(:predicates \n"
        for p in self._predicates:
            string += "\t"
            string += p.toUngroundPddl()
            string += "\n"
        string += ")\n"
        string += "(:functions \n"
        for f in self._functions:
            string += "\t{}\n".format(f.toUngroundPddl())
        string += ")\n"
        for a in self._actions:
            string += a.toPddl()
            string += "\n"
        string += ")\n"
        if to_file:
            with open(self._workspace+"/domain.pddl", 'w') as f:
                f.write(string)
        else:
            return string

    def printProblem(self, to_file=False):
        string = "(define (problem {}) (:domain {})\n".format("1", self._title)
        string += "(:objects \n"
        for objType, objects in self._objects.iteritems():
            if len(objects):
                 string += '\t'
                 string += ' '.join(objects)
                 string += ' - {}\n'.format(objType)
        string += ")\n"
        string += "(:init \n"
        for state in self._init_state:
            string += "\t"
            string += state.toPddl()
            string += "\n"
        string += ")\n"
        string += "(:goal (and \n"
        for g in self._goal:
            string += '\t'
            string += g.toPddl()
            string += "\n"
        string += "))\n"
        string += ")\n"
        if to_file:
            with open(self._workspace+"/p01.pddl", 'w') as f:
                f.write(string)
        else:
            return string

    def invokePlanner(self, generate_pddl=True):
        #subprocess.call(["plan.py", "y+Y+a+T+10+t+5+e+r+O+1+C+1", self._workspace+"/domain.pddl", self._workspace+"/p01.pddl", "mypddlplan"])
        if generate_pddl:
            self.printDomain(True)
            self.printProblem(True)

        output = subprocess.Popen(["plan.py", "y+Y+a+T+10+t+5+e+r+O+1+C+1", self._workspace+"/domain.pddl", self._workspace+"/p01.pddl", self._workspace+"/pddlplan"], stdout=subprocess.PIPE).communicate()[0]
        outpath = None
        for (dirpath, dirnames, filenames) in walk(self._workspace):
            for name in filenames:
                if name.find('pddlplan')>=0:
                    outpath = dirpath+'/'+name
        if outpath:
            with open(outpath, 'r') as f:
                data=f.read()
            remove("output")
            remove("all.groups")
            remove("variables.groups")
            remove("output.sas")
            remove(outpath)
            return data
        else:
            return None
