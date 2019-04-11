import skiros2_msgs.msg as msgs
import skiros2_common.core.params as params
from skiros2_common.ros.utils import registerClass, serializeParamMap, decodeParam, ParamsEncoder, json_loads_byteified
import json

def encodeSkill(encoder, obj):
    return {'manager': obj.manager, 'type': obj.type, 'name': obj.name,
    'ph': {k: encoder.default(v) for k, v in obj.ph.iteritems() }, 'children': obj.children}

def decodeSkill(obj):
    if isinstance(obj, str):
        obj = json_loads_byteified(obj)
    return SkillHolder(obj['manager'], obj['type'], obj['name'], {k: decodeParam(v) for k, v in obj['ph'].iteritems()}, [decodeSkill(c) for c in obj['children']])

class SkillHolder(object):
    __slots__ = ['manager', 'type', 'name', 'ph', 'children']
    def __init__(self, manager, type_in, name, params_in=None, children=None):
        self.manager = manager
        self.name = name
        self.type = type_in
        self.ph = params.ParamHandler()
        self.children = list()
        if params_in:
            self.ph.reset(params_in)
        if children:
            self.children = children

    def __str__(self):
        return "{}:{} [{}]".format(self.type, self.name, self.ph.printState())

    def toMsg(self):
        msg = msgs.ResourceDescription()
        msg.type = self.type
        msg.name = self.name
        msg.params = serializeParamMap(self.ph.getParamMap())
        return msg

    def toJson(self):
        return str(json.dumps(self, cls=ParamsEncoder))


registerClass("SkillHolder", SkillHolder, encodeSkill, decodeSkill)

def deserialize_skill(string):
    return decodeSkill(string)