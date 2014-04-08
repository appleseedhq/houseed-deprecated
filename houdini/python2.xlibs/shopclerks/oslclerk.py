#
#  This is a clerk for OSL SHOP shaders
#

import hou, sys
from clerkutil import *


def getName():
    return "OSL"


def getLabel():
    return "appleseed"


def getKeywords():
    return "appleseed"


def isVexClerk():
    return False


class _contextInfo:
    def __init__(self, geoattrib, indattrib):
        self.Geometry = geoattrib
        self.Indirect = indattrib


__contexts = {
    "surface"           : _contextInfo('osl_material',   'shop_osl_material'),
    "displace"          : _contextInfo('osl_displace',   'shop_osl_displace'),
    "geometry"          : _contextInfo('osl_geometry',   'shop_osl_geometry'),
    "light"             : _contextInfo('osl_light',      'shop_osl_light'),
    "fog"               : _contextInfo('osl_volume',     'shop_osl_volume'),
}


def shaderSupported(style):
    return __contexts.has_key(style)


def getGeometryAttribute(style):
    cinfo = __contexts.get(style, None)
    if cinfo != None:
        return cinfo.Geometry
    return None


def getIndirectAttribute(style):
    cinfo = __contexts.get(style, None)
    if cinfo != None:
        return cinfo.Indirect
    return None


def boolString(v):
    if v:
        return 'true'
    return 'false'


# child class of ParmEvaluator, see clerkutil.py
class oslParmEval( ParmEvaluator ):
    def __init__( self, evaluator, precision, options, map=None):
        ParmEvaluator.__init__(self, evaluator, precision, options, map)

    # override ParmEvaluator getParmValues method
    def getParmValues( self, parm, values ):
        #read parmtags from .ds scripts
        tags = parm.parmTemplate().tags()
        parmtype = tags.get( 'script_osltype', '' )
        if parmtype:
            parmtype += ' '
        name = parm.name()
        parmval = ('%s,' % (values,)).replace('"','')
        return [ ('%s %s' % (parmname, parmtype), parmval) for parmname in self.map.get(name, [name]) ]


def buildShaderString(style, shopname, time, parmnames, options):
    precision = options.get('soho_precision', 12)
    shop = hou.node(shopname)
    shader = '"%s" ' % shop.shaderName(False, style)
    frame = hou.timeToFrame(time)
    comma = False

    args = [ shader ]
    parmeval = oslParmEval( None, precision, options )
    for parm in parmeval.getShaderParms( shop, frame, parmnames ):
        args.extend( parm )
    
    #return shader parameter string
    return ' '.join( args )
