"""
Copyright 2014 Hans Hoogenboom

   Licensed under the Apache License, Version 2.0 (the "License");
   you may not use this file except in compliance with the License.
   You may obtain a copy of the License at

       http://www.apache.org/licenses/LICENSE-2.0

   Unless required by applicable law or agreed to in writing, software
   distributed under the License is distributed on an "AS IS" BASIS,
   WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
   See the License for the specific language governing permissions and
   limitations under the License.
"""

#####################################################################
#                                                                   #
# APPLESEED AsProjectFileWriter                                     #
#                                                                   #
#####################################################################

#
# NAME:         ASapi.py ( Python )
#
# COMMENTS:     project independent class to write an
#               .appleseed project file
#


import os
import sys
import subprocess


class AsLogger( object):
    def __init__( self, debug_mode = False):
        self._DEBUG = debug_mode

    def log_debug( self, debug_msg):
        # we only log info when debug is enabled
        if self._DEBUG:
            sys.__stdout__.write( 'DEBUG: ' + debug_msg)

    def log_info( self, info_msg):
        if self._DEBUG:
            sys.__stdout__.write( 'INFO: ' + info_msg)
        else:
            soho.warning( info_msg )

    def log_error( self, error_msg):
        if self._DEBUG:
            sys.__stderr__.write( error_msg)
        else:
            soho.error( error_msg)


# AsProjectFileWriter is independent of Houdini, SOHO or any other program/context.
# It could be reused for any other exporters. In addition, it handles some common
# errors, like indenting mismatches, some tags open / close issues, etc.
class AsProjectFileWriter( object):
    def __init__( self, filename, logger):
        self._filename = filename
        self._logger = logger
        self._proj_dir = os.path.dirname( self._filename)
        self._indent_level = 0
        self._file = open( self._filename, "w")

        # write XML version and encoding
        self._file.write( '<?xml version="1.0" encoding="UTF-8"?>\n')

        self._logger.log_debug( "Created project writer.\n")
        self._logger.log_debug( "filename = %s\n" % self._filename)
        self._logger.log_debug( "proj dir = %s\n" % self._proj_dir)

        self._tags_stack = []

    #
    # internal methods
    #
    def _write_text( self, txt):
        self._file.write( txt)

    def _emit_indent( self):
        self._write_text( " " * self._indent_level * 4)

    def _emit_text( self, txt):
        self._emit_indent()
        self._write_text( txt)

    def _indent( self):
        self._indent_level += 1

    def _unindent( self):
        if self._indent_level == 0:
            self._logger.log_error( "Negative indent level requested.\n")

        self._indent_level -= 1

    def _begin_tag( self, name, values = None):
        self._tags_stack.append( name )

        if values:
            self._logger.log_debug( 'begin tag %s values = %s\n' % ( name, values))
            self._emit_text( '<%s %s>\n' % ( name, values))
        else:
            self._logger.log_debug( 'begin tag %s\n' % name)
            self._emit_text( '<%s>\n' % name )

        self._indent()

    def _end_tag( self, name):
        if len( self._tags_stack) == 0 or self._tags_stack.pop() != name:
            self._logger.log_error( "Closing tag %s, that was not opened" % name)            

        self._unindent()
        self._emit_text( '</%s>\n' % name)
        self._logger.log_debug( 'end tag %s\n' % name)
        self._inside_tag = None

    def close_project_file( self):
        self._file.close()

    #
    # general appleseed tags
    #
    def emit_whiteline( self ):
        self._write_text( '\n' )

    def emit_comment( self, msg):
        if msg != None:
            self._emit_text("<!-- %s -->\n" % msg)

    def begin_parm( self, name):
        self._logger.log_debug( "begin parameters, name = %s\n" % name)
        self._begin_tag( 'parameters', 'name="%s"' % name)

    def emit_parm( self, name, value):
        self._emit_text( '<parameter name="%s" value="%s" />\n' % (name, value))

    def end_parm( self):
        self._end_tag( 'parameters')
        self._logger.log_debug( "end parameters\n")

    def emit_matrix( self, values = None):
        self._begin_tag( 'matrix')

        if values == None:
            self._emit_text( "1.0 0.0 0.0 0.0\n")
            self._emit_text( "0.0 1.0 0.0 0.0\n")
            self._emit_text( "0.0 0.0 1.0 0.0\n")
            self._emit_text( "0.0 0.0 0.0 1.0\n")
        else:
            for i in range(4):
                self._emit_text( "".join( [ "%f " % values[(i * 4) + j] for j in range(4)]))
                self._emit_text("\n")

        self._end_tag( 'matrix')

    def emit_transform( self, values = None, time = 0):
        self._begin_tag( 'transform', 'time="%s"' % time)
        self.emit_matrix( values)
        self._end_tag( 'transform')

    def emit_assign_material( self, slot, side, material ):
        self._emit_text( '<assign_material slot="%s" side="%s" material="%s" />\n' % (slot, side, material) )
    
    def emit_alpha( self, values ):
        self._begin_tag( 'alpha' )
        self._emit_text( values )
        self._end_tag( 'alpha' )

    def emit_values( self, values ):
        self._begin_tag( 'values' )
        self._emit_text( values )
        self._end_tag( 'values' )

    #
    # appleseed entities
    #
    def begin_project( self, revision = 7):
        self._write_text( "\n" )
        self._begin_tag( 'project', 'format_revision = "%s"' % revision)

    def end_project( self):
        self._end_tag( 'project')

    def emit_searchpaths( self, paths):
        if len( paths ) != 0:
            self._begin_tag( 'search_paths' )
            for p in paths:
                self._emit_text( '<search_path> %s </search_path>\n' % p)
            self._end_tag( 'search_paths')
            self.emit_whiteline()

    def begin_scene( self):
        self._begin_tag( 'scene')

    def end_scene( self):
        self._end_tag( 'scene')
        self.emit_whiteline()

    def begin_camera( self, name, model='pinhole_camera' ):
        self._begin_tag( 'camera', 'name="%s" model="%s"' % ( name, model))

    def end_camera( self):
        self._end_tag( 'camera')
        self.emit_whiteline()

    def begin_color( self, name ):
        self._begin_tag=( 'color' )

    def end_color( self ):
        self._end_tag( 'color' )

    def begin_environment_edf( self ):
        self._begin_tag( 'environment_edf', 'name="%s" model="%s" />\n' % (name, model) )

    def end_environment_edf( self ):
        self._end_tag( 'environment_edf' )

    def begin_environment_shader( self ):
        self._begin_tag( 'environment_shader', 'name="%s" model="%s" />\n' % (name, model) )

    def end_environment_shader( self ):
        self._end_tag( 'environment_shader' )

    def begin_environment( self, name, model ):
        self._begin_tag( 'environment', 'name="%s" model="%s" />\n' % (name, model) )

    def end_environment( self ):
        self._end_tag( 'environment' )

    def begin_assembly( self, name):
        self._begin_tag( 'assembly', 'name="%s"' % name)

    def end_assembly( self):
        self._end_tag( 'assembly')
        self.emit_whiteline()

    def begin_light( self, name, model ):
        self._begin_tag( 'light', 'name="%s" model="%s"' % (name, model) )

    def end_light( self ):
        self._end_tag( 'light' )
        self.emit_whiteline()

    def begin_texture( self, name, model='disk_texture_2d' ):
        self._begin_tag( 'texture', 'name="%s" model="%s"' % (name, model) )

    def end_texture( self ):
        self._end_tag( 'texture' )

    def begin_texture_instance( self, name, texture ):
        self._begin_tag( 'texture_instance', 'name="%s" texture="%s"' % (name, texture) )

    def end_texture_instance( self ):
        self._end_tag( 'texture_instance' )

    def begin_shader_group( self, name ):
        self._begin_tag( 'shader_group', 'name="%s"' % name )

    def end_shader_group( self ):
        self._end_tag( 'shader_group' )
        self.emit_whiteline()

    def begin_shader( self, stype, name, layer ):
        self._begin_tag( 'shader', 'type="%s" name="%s" layer="%s"' % (stype, name, layer) )

    def end_shader( self ):
        self._end_tag( 'shader' )

    def emit_connect_shaders( self, slayer, sparm, dlayer, dparm ):
        self._emit_text('<connect_shaders src_layer="%s" src_param="%s" dst_layer=%"s" dst_param="%s" />' % ( slayer, sparm, dlayer, dparm ) )

    def begin_surfaceshader( self, name='physical_surface_shader', model='physical_surface_shader' ):
        self._begin_tag( 'surface_shader', 'name="%s" model="%s"' % (name, model) )

    def end_surfaceshader( self ):
        self._end_tag( 'surface_shader' )
        self.emit_whiteline()

    def begin_material( self, name, model='ols_material' ):
        self._begin_tag( 'material', 'name="%s" model="%s"' % (name, model) )

    def end_material( self ):
        self._end_tag( 'material' )
        self.emit_whiteline()

    def begin_object( self, name):
        self._begin_tag( 'object', 'name="%s" model="mesh_object"' % name)

    def end_object( self):
        self._end_tag( 'object')
        self.emit_whiteline()

    def begin_object_instance( self, name, obj):
        self._begin_tag( 'object_instance', 'name="%s" object="%s"' % ( name, obj))

    def end_object_instance( self):
        self._end_tag( 'object_instance')
        self.emit_whiteline()

    def begin_assembly_instance( self, name, assembly):
        self._begin_tag( 'assembly_instance', 'name="%s" assembly="%s"' % ( name, assembly))

    def end_assembly_instance( self):
        self._end_tag( 'assembly_instance')
        self.emit_whiteline()

    def begin_output( self):
        self._begin_tag( 'output')

    def end_output( self):
        self._end_tag( 'output')
        self.emit_whiteline()

    def begin_frame( self ):
        self._begin_tag( 'frame', 'name="beauty"')

    def end_frame( self ):
        self._end_tag( 'frame' )

    def begin_configuration( self, final=True ):
        if final:
            self._logger.log_debug( "emit final configuration\n")
            self._emit_text( '<configuration name="final" base="base_final">\n')
        else:
            self._logger.log_debug( "emit interactive configuration\n")
            self._emit_text( '<configuration name="interactive" base="base_interactive">\n')
        self._indent()

    def end_configuration( self ):        
        self._unindent()
        self._emit_text( "</configuration>\n")

    def begin_configurations( self):
        self._begin_tag( 'configurations')

    def end_configurations( self):
        self._end_tag( 'configurations')
        self.emit_whiteline()


def convertToString( value ):
    return ' '.join( map(str, value) )


#####################################################################
#                                                                   #
# APPLESEED SETTINGS                                                #
#                                                                   #
#####################################################################

#
# NAME:         ASsettings.py ( Python )
#
# COMMENTS:     settings from the Appleseed ROP plus generic data objects
#

import hou, soho
from soho import SohoParm
from soho import Precision
from sohog import SohoGeometry


class SceneObject( object ):
    _sopCache      = []
    _shaderCache   = []
    _instanceCache = []
    
    def __init__( self, obj, now, soppath ):
        self.obj      = obj
        self.houobj   = None
        self.housop   = None
        self.soppath  = soppath
        self.name     = None
        self.shopname = None
        self.gblur    = None
        self.xblur    = None

        _ASGeoSettings = {
            'geo_velocityblur' : SohoParm('geo_velocityblur',  'int', [0], False),
            'as_lightsamples'  : SohoParm('as_lightsamples', 'int', [1], False)
        }
        attr_list = obj.evaluate( _ASGeoSettings, now )
        velblur = attr_list.get( 'geo_velocityblur', None )
        samples = attr_list.get( 'as_lightsamples', None )

        if velblur:
            self.gblur = velblur.Value[0]
        if samples:
            self.samples = samples.Value[0]

        hou_sop = hou.node( soppath )
        if hou_sop:
            self.housop = hou_sop
            self.houobj = hou_sop.creator()
            self.xblur  = self.houobj.isTimeDependent()
        else:
            self.sop = None

        if self.obj:
            self.name = obj.getName()

    def getName( self ):
        return self.name

    def addInstance( self, instanceObject ):
        if not self.instance.has_key( instanceObject.name ): 
            self.instance[ instanceObject.name ] = instanceObject

    def getPath( self, path ):
        if self.obj:
            hou_sop = self.obj.node( path )
        if hou_sop:
            path = hou_sop.path()
        return path

    def getSopCache():
        return _sopCache

    def getShopCache():
        return _shaderCache

    def getInstanceCache():
        return _instanceCache

    def clearCaches():
        _sopCache      = []
        _shaderCache   = []
        _instanceCache = []


# configuration and parameter containers for the config and
# output part for parameters on lights or cameras
outputParms  = dict()
configParms  = dict()
CameraTimeSteps = []
GeoTimeSteps = []
SettingDefs = []

# UGLY
VelocityBlurSamples = []

# object containers
theShaderList   = {}


#
# Settings from the appleseed render operator
# Additional settings are added to the global
# variables outputParms and configParms
#

tileSize = str( soho.getDefaultedInt( 'as_tile_size', [''] )[0] )

#Main output settings for Appleseed (output image)
ASOutputSettings = {
    'tile_size'     : tileSize + " " + tileSize,
    'pixel_format'  : soho.getDefaultedString( 'as_pixel_format', [''] )[0],
    'filter'        : soho.getDefaultedString( 'as_filter', [''] )[0],
    'filter_size'   : soho.getDefaultedInt( 'as_filter_size', [''] )[0],
    'color_space'   : soho.getDefaultedString( 'as_color_space', [''] )[0],
    'premult_alpha' : soho.getDefaultedInt( 'as_premult_alpha', [''] )[0],
    'clamping'      : soho.getDefaultedInt( 'as_clamping', [''] )[0],
    'gamma'         : soho.getDefaultedFloat( 'as_gamma', [''] )[0]
}


#Main config settings for Appleseed (render engine)
ASConfigSettings = {
    #image plane sampling
    'passes'         : soho.getDefaultedInt( 'as_passes', [''] )[0],
    'pixel_renderer' : soho.getDefaultedString( 'as_pixel_renderer', [''] )[0],
    #lighting
    'lighting_engine' : soho.getDefaultedString( 'as_lighting_engine', [''] )[0],
    #system
    'override_cpu'       : soho.getDefaultedInt( 'override_cpu', [''] )[0],
    'rendering_threads'  : soho.getDefaultedInt( 'as_rendering_threads', [''] )[0],
    'override_mem'       : soho.getDefaultedInt( 'override_mem', [''], )[0],
    'texture_cache_size' : soho.getDefaultedInt( 'as_texture_cache_size', [''] )[0]
}

#Sub config settings for Appleseed
ASUniformSampler = {
    'uniform_samples': soho.getDefaultedInt( 'as_uniform_samples', [''] )[0],
    'uniform_force_antialiasing' : soho.getDefaultedInt( 'as_uniform_force_antialiasing', [''] )[0],
    'uniform_decorrelate_pixels' : soho.getDefaultedInt( 'as_uniform_decorrelate_pixels', [''] )[0]
}

ASAdaptiveSampler = {
    'min_samples' : soho.getDefaultedInt( 'as_adaptive_min_samples', [''] )[0],
    'max_samples' : soho.getDefaultedInt( 'as_adaptive_max_samples', [''] )[0],
    'quality'     : soho.getDefaultedFloat( 'as_adaptive_quality', [''] )[0],
    'diagnostics' : soho.getDefaultedInt( 'as_adaptive_diagnostics', [''] )[0]
}

ASRayTracer = {
    'drt_enable_ibl'        : soho.getDefaultedInt( 'as_drt_enable_ibl', [''] )[0],
    'drt_unlimited_bounces' : soho.getDefaultedInt( 'as_drt_unlimited_bounces', [''] )[0],
    'drt_max_bounces'       : soho.getDefaultedInt( 'as_drt_max_bounces', [''] )[0],
    'drt_rr_start_bounce'   : soho.getDefaultedInt( 'as_drt_rr_start_bounce', [''] )[0],
    'drt_light_samples'     : soho.getDefaultedInt( 'as_drt_light_samples', [''] )[0],
    'drt_ibl_samples'       : soho.getDefaultedInt( 'as_drt_ibl_samples', [''] )[0]
}

ASPathTracer = {
    'pt_direct_lighting'   : soho.getDefaultedInt( 'as_pt_direct_lighting', [''] )[0],
    'pt_enable_ibl'        : soho.getDefaultedInt( 'as_pt_enable_ibl', [''] )[0],
    'pt_enable_caustics'   : soho.getDefaultedInt( 'as_pt_enable_caustics', [''] )[0],
    'pt_unlimited_bounces' : soho.getDefaultedInt( 'as_pt_unlimited_bounces', [''] )[0],
    'pt_max_bounces'       : soho.getDefaultedInt( 'as_pt_max_bounces', [''] )[0],
    'pt_rr_start_bounce'   : soho.getDefaultedInt( 'as_pt_rr_start_bounce', [''] )[0],
    'pt_next_event'        : soho.getDefaultedInt( 'as_pt_next_event', [''] )[0],
    'pt_light_samples'     : soho.getDefaultedInt( 'as_pt_light_samples', [''] )[0],
    'pt_ibl_samples'       : soho.getDefaultedInt( 'as_pt_ibl_samples', [''] )[0],
    'pt_unlimited_max_ray_intensity' : soho.getDefaultedInt( 'as_pt_unlimited_max_ray_intensity', [''] )[0],
    'pt_max_ray_intentsity' : soho.getDefaultedFloat( 'as_pt_max_ray_intentsity', [''] )[0]
}

ASPhotonMapping = {
    'sppm_direct_lighting'            : soho.getDefaultedInt( 'as_sppm_direct_lighting', [''] )[0],
    'sppm_enable_ibl'                 : soho.getDefaultedInt( 'as_sppm_enable_ibl', [''] )[0],
    'sppm_enable_caustics'            : soho.getDefaultedInt( 'as_sppm_enable_caustics', [''] )[0],
    'sppm_unlimited_photon_bounces'   : soho.getDefaultedInt( 'as_sppm_unlimited_photon_bounces', [''] )[0],
    'sppm_photon_max_bounces'         : soho.getDefaultedInt( 'as_sppm_photon_max_bounces', [''] )[0],
    'sppm_photon_rr_start_bounce'     : soho.getDefaultedInt( 'as_sppm_photon_rr_start_bounce', [''] )[0],
    'sppm_light_photons'              : soho.getDefaultedInt( 'as_sppm_light_photons', [''] )[0],
    'sppm_env_photons'                : soho.getDefaultedInt( 'as_sppm_env_photons', [''] )[0],
    'sppm_radiance_unlimited_bounces' : soho.getDefaultedInt( 'as_sppm_radiance_unlimited_bounces', [''] )[0],
    'sppm_radiance_max_bounces'       : soho.getDefaultedInt( 'as_sppm_radiance_max_bounces', [''] )[0],
    'sppm_radiance_rr_start_bounce'   : soho.getDefaultedInt( 'as_sppm_radiance_rr_start_bounce', [''] )[0],
    'initial_radius'                  : soho.getDefaultedFloat( 'as_sppm_radiance_radius', [''] )[0],
    'sppm_radiance_max_photons'       : soho.getDefaultedInt( 'as_sppm_radiance_max_photons', [''] )[0],
    'sppm_radiance_alpha'             : soho.getDefaultedFloat( 'as_sppm_radiance_alpha', [''] )[0]
}

ASProjectPaths = {
    'as_shaderpath'  : soho.getDefaultedString( 'as_shaderpath', [''] )[0],
    'as_texturepath' : soho.getDefaultedString( 'as_texturepath', [''] )[0],
    'as_archivepath' : soho.getDefaultedString( 'as_archivepath', [''] )[0]
}


#####################################################################
#                                                                   #
# APPLESEED SHOP PROCESSING                                         #
#                                                                   #
#####################################################################

#
# NAME:         ASgeo.py ( Python )
#
# COMMENTS:     process geometry and shaders using SOHO
#


import time, sys, string, math, os 
import hou, soho
from soho import SohoParm
from soho import Precision
from sohog import SohoGeometry


#
# Process shaders and textures
#
def processShop( shader, key, writer ):
    # first entry is the shopname
    # then the parameters, type and values delimited by ,
    argend = shader.find('"', 1)
    if argend < 2:
        #no name?
        return ['',shader]
    shopname = shader[1 : argend]
    shopparm = shader[argend + 1 : -1]
    parms    = shopparm.split(',')
    writer.begin_shader( key, shopname, shopname + "1" )
    for parm in parms:
        # parm should always constit of a name, type and its value, if we
        # only have two entries in parm we have a tab from the interface
        if len( parm.split() ) < 3:
            continue         
        name  = parm.split()[0]
        value = convertToString( parm.split()[1:] )
        writer.emit_parm( name, value )
    writer.end_shader()


#TODO: add the generic OSL shader shader and light shader
_ShaderContext = {
    'surface'      : 'shop_surfacepath',
    'displacement' : 'shop_displacepath',
    'volume'       : 'shop_volumepath',
    }

_ShaderSkipContext = {
    'surface'      : 'shop_disable_surfacepath',
    'displacement' : 'shop_disable_displacepath',
    'volume'       : 'shop_disable_volumepath',
    }


def isContextDisabled(obj, now, wrangler, context):
    if not _ShaderSkipContext.has_key( context ):
        return False
    else:
        return obj.wrangleInt( wrangler, _ShaderSkipContext[ context ], now, [0] )[0]


def wrangleMaterial( shopname, shop, now, writer, wrangler=None ):
    shg_name = "/shg" + shopname    
    writer.begin_shader_group( shg_name )

    shaders = {}
    if wrangler:
        for context in _ShaderContext:
            if isContextDisabled( shop, now, wrangler, context ):
                continue
            shadertype = _ShaderContext[ context ]
            # Uses the osclerks.py script in $HH/pythonlibs2.xlibs/shopclerks to
            # query the shader parameters. Only returns NON default values
            # the shader is a formatted string with all the parameters etc.
            shader = shop.wrangleShader( wrangler, shadertype, now, [''] )[0]
            if shader:
                shaders[ context ] = processShop( shader, writer )
    else:
        for context in _ShaderContext:
            if isContextDisabled( shop, now, wrangler, context ):
                continue
            shadertype = _ShaderContext[ context ]
            shader = shop.getDefaultedShader( shadertype, now, [''] )[0]
            if shader:
                shaders[ context ] = processShop( shader, context, writer )
    #TODO: how to get the correct closure of an osl shader?
    if len( shaders ) > 1:
        writer.emit_connect_shaders( "a", "b", "c", "d" )

    writer.end_shader_group()
       

def outputMaterial( now, writer ):
    global theShaderList

    #write shader groups - write materials (possibly consisting of several shops)
    for shopname in theShaderList:
        wrangleMaterial( shopname, theShaderList[shopname], now, writer )

    #write surface_shader (and possibly others)
    if len( theShaderList ) > 0:
        writer.begin_surfaceshader()
        writer.end_surfaceshader()

    #write material tags
    for shopname in theShaderList:
        materialname = "/mat" + shopname
        shopname     = "/shg" + shopname
        writer.begin_material( materialname, 'osl_material' )
        writer.emit_parm( 'osl_surface', shopname )
        writer.emit_parm( 'surface_shader', 'physical_surface_shader' )
        writer.end_material()
    

def getMaterial( path, now ):
    global theShaderList
   
    sopnode  = hou.node( path )
    if sopnode:
        parent   = sopnode.creator()
        hou_shop = parent.node( path )
        hou_shop = hou_shop.path()

        shop = soho.getObject( hou_shop )
        shopname = shop.getName()
        if shopname not in theShaderList:
            theShaderList[shopname] = shop
    else:
        shopname = None
        shop = None
        soho.warning( "Paths to shaders not found: %s" % path )

    return (shopname, shop)


# partition geometry based on attached shader
def partitionMaterial( geoList, attrib ):
    handle = geoList[0].attribute( 'geo:prim', attrib )
    
    # we have more than one material on our geo
    if handle >= 0:
        splits = {}
        for geo in geoList:
            parts = geo.partition( 'geo:partattrib', attrib )
            for material in parts:
                parsed_obj = splits.get(material, None)
                if not parsed_obj:
                    splits[material] = [parts[material]]
                else:
                    parsed_obj.append(parts[material])
    # all geo has the same material
    else:
        splits = {"" : geoList}
                
    return splits


#####################################################################
#                                                                   #
# APPLESEED GEOMETRY PROCESSING                                     #
#                                                                   #
#####################################################################


def computeVBounds( geo, bbox, tscale ):
    vbox  = [0, 0, 0, 0, 0, 0 ]
    vattr = geo.attribute( 'geo:point', 'v' )
    if vattr > 0:
        npts = geo.globalValue( 'geo:pointcount' )[0]
        for pt in range( npts ):
            v = geo.value( vattr, pt )
            vbox[0] = min( vbox[0], v[0]*tscale )
            vbox[1] = min( vbox[1], v[1]*tscale )
            vbox[2] = min( vbox[2], v[2]*tscale )
            vbox[3] = max( vbox[0], v[0]*tscale )
            vbox[4] = max( vbox[1], v[1]*tscale )
            vbox[5] = max( vbox[2], v[2]*tscale )
    vbounds = [ x + y for x, y in zip( vbox, bbox ) ]
    return vbounds


#in case of velocity blur we have to deforming geometry
def movePoints( geo, tscale ):
    vattr = geo.attribute( 'geo:point', 'v' )
    if vattr > 0:
        npts = geo.globalValue( 'geo:pointcount' )[0]
        pnt  = geo.attribute( 'geo:point', 'P' )
        vattr = geo.attribute( 'geo:point', 'v' )
        for pt in range( npts ):
            pos = geo.value( pnt, pt )
            vel = geo.value( vattr, pt )
            vp  = [ p + v * tscale for p, v in zip( pos, vel ) ]
        return vp


#save as a wavefront obj file VERSION 2, WORKS
#fix output of appleseed object and object_instances
def saveObjArchives( geo, name, time_sample ):
        print( '#archive created at %s' % time.ctime() )
        print( '#name: %s' % name )
        bounds = geo.globalValue( 'geo:boundingbox' )
        print( "# bounds: %s" % convertToString( bounds ) )
        print( "# time sample at: %s" % time_sample )
        nprims = geo.globalValue( 'geo:primcount' )[0]
        npts   = geo.globalValue( 'geo:pointcount' )[0]

        #write point positions
        print( "\n# %d vertices" % npts )
        pnt = geo.attribute( 'geo:point', 'P' )
        v_handle = geo.attribute( 'geo:point', 'v' )
        if v_handle < 0:
            for pts in range( npts ):
                pos = geo.value( pnt, pts )
                print( "v %f %f %f" % ( pos[0], pos[1], pos[2] ) )
        else:
            for pts in range( npts ):
                pos  = geo.value( pnt, pts )
                v    = geo.value( v_handle,   pts )
                print( "v " + "".join( [" %f" % ( pos[i] + v[i] * time_sample ) for i in range( 3 ) ] ) )

        #write uv/texture coordinates
        prim_uv = dict()
        counter = 1
        uv      = geo.attribute( 'geo:vertex', 'uv' )
        vtxs    = geo.attribute( 'geo:prim', 'geo:vertexcount')
        if uv > 0:
            print ("\n# uv coordinates")
            for prim in range( nprims ):
                uvLst = []
                nv    = geo.value( vtxs, prim)[0]
                for vtx in range( nv ):
                    uvCoord = geo.vertex( uv, prim, vtx )
                    print( "vt %f %f %f" % ( uvCoord[0], uvCoord[1], uvCoord[2] ) )
                    uvLst.append( counter )
                    counter += 1
                uvLst = [uvLst[0]] + uvLst[-1:0:-1]
                prim_uv[ prim ] = uvLst

        #write normals
        nrml = geo.attribute( 'geo:point', "N" )
        nstr = "\n# normals"
        #if no normals, calculate the normals
        if nrml < 0:
            nrml = geo.normal()
            nstr = "\n# soho calculated normals"
        print( nstr )
        for pts in range( npts ):
            pnt_nrml = geo.value( nrml, pts )
            print( "vn %f %f %f" % ( pnt_nrml[0], pnt_nrml[1], pnt_nrml[2] ) )

        #write faces
        nvts   = geo.attribute( 'geo:prim', 'geo:vertexcount' )
        pntRef = geo.attribute( 'geo:vertex', 'geo:pointref' )
        print( "\n# %d faces" % nprims )
        for prim in range( nprims ):
            nvtx =  geo.value( nvts, prim )[0]
            vtxList = []
            nrmList = []
            for vtx in range( nvtx ):
                curpnt = geo.vertex( pntRef, prim, vtx )[0] + 1
                vtxList.append( curpnt )
                nrmList.append( curpnt )
            #reverse vertices and normals so we go CCW
            vtxList = [vtxList[0]] + vtxList[-1:0:-1]
            nrmList = [nrmList[0]] + nrmList[-1:0:-1]
            #we have normals and faces
            if uv < 0:
                print( "f" + "".join([" %d//%d " % (vtxList[vtx], nrmList[vtx]) for vtx in range(nvtx)]) )
            # or faces, uv's and normals
            else:
                print( "f" + "".join( [" %d/%d/%d " % (vtxList[vtx], prim_uv[prim][vtx], nrmList[vtx]) for vtx in range(nvtx)] ) )


# appleseed only supports closed polygons at the moment
# so we only return just them and ignore the rest
def primTypeIterator( geo ):
    attr_type  = geo.attribute( 'geo:prim', 'intrinsic:typename' )
    attr_close = geo.attribute( 'geo:prim', 'geo:primclose' )
    primcount  = geo.globalValue( 'geo:primcount' )[0]

    #soho.warning( "number: %s" % primcount )
    for prim in xrange( primcount ):
        primtype = geo.value( attr_type, prim )[0]
        # get polygons
        if primtype == 'Poly':
            if geo.value( attr_close, prim )[0]:
                #soho.warning ("LALALALA")
                yield 'closedpoly'
            else:
                #soho.warning( "HIHII" )
                yield 'openpoly'
        # everything else
        else:
            #soho.warning( "MUAHA" )
            yield 'nonpoly'


def groupByPrimitiveType( geo ):
    splits = {}
    #for geo in geolist:
    groups = geo.partition( 'geo:partlist', geo.attribute( 'geo:prim', 'intrinsic:typename' ) ) #primTypeIterator( geo ) )
    for key in groups:
        soho.warning( "%s holds:" % key )
        soho.warning( "contents: %s" % groups[key] )
    for key in groups:
        parsed_obj = splits.get( key, None )
        if not parsed_obj:
            splits[key] = [groups[key]]
        else:
            parsed_obj.append( groups[key] )
    #        splits[key].append(groups[key])
    if splits.has_key('closedpoly'):
        test = splits['closedpoly']
        return test
    else:
        return None


# appleseed only works with wavefront obj format so we
# need to write the vertices, faces and points to a file
# and return the filepath for the appleseed object tag
def parseGeoObject( ASobj, now, name ):

    # TODO: get rid of globals
    gblur_samples = GeoTimeSteps
    vel_samples   = VelocityBlurSamples

    geoList = []
    time_samples = []
    # velocity or deformation blur
    if ASobj.gblur:
        # get handle to geometry
        gdp = SohoGeometry( ASobj.soppath, now )
        if gdp.Handle >= 0:
            v_handle = gdp.attribute( 'geo:point', 'v' )
            if v_handle >= 0:
                if gdp.attribProperty( v_handle, 'geo:vectorsize' )[0] != 3:
                    v_handle = False
                if v_handle >= 0:
                    ASobj.vblur = True
            # we have velocity blur, overrule deformation
            if v_handle >= 0:
                for i in range( len(vel_samples) ):
                    geoList.append( gdp )
                time_samples = vel_samples
            else:
                for t in gblur_samples:
                    gdp = SohoGeometry( ASobj.soppath, t )
                    geoList.append( gdp )
                time_samples = gblur_samples
    # tranformation blur is set with camera
    else:
        gdp = SohoGeometry( ASobj.soppath, now )
        if gdp.Handle >= 0:
            geoList.append( gdp )
        time_samples.append( now )

    time_samples = time_samples * 10

    if len( geoList ) < 1:
        return False

    # partition geometry based on shader
    # matGeo is a dict with material as key, primitives as value
    partGeo = partitionMaterial( geoList, 'shop_materialpath' )

    # get base path for storing obj files
    (cwd, paths) = getProjectPaths( now )
    if paths.has_key('as_archivepath'):
        path = paths['as_archivepath']
    else:
        path = cwd
    if os.path.isabs( path ):
        as_archivepath = path
    else:
        as_archivepath = os.path.join( cwd, path )

    partionedObjects = {}
    shopcounter = 0    
    for shoppath in partGeo:
        if shoppath:
            (shopname, shop) = getMaterial( shoppath, now )
        else:
            # no shops? Then we probably have a material set on the object!
            obj_material_path = ASobj.obj.getDefaultedString('shop_materialpath', now, [''])[0]
            if obj_material_path:
                (shopname, shop) = getMaterial( obj_material_path, now)
            else:
                # no shader present
                shop = None
                shopname = None

        partname = '%s-mat%d' % ( name, shopcounter )
        shopcounter += 1

        filenameList = []
        save_stdout = sys.stdout
        timecounter = 0
        # enumerate?
        for timesample in partGeo[shoppath]:
            filename = os.path.basename( partname ) + "_%d" % timecounter
            filepath = as_archivepath + '/' + filename + '.obj'
            filenameList.append( filename )

            with open( filepath, 'w' ) as fp:
                sys.stdout = fp
                saveObjArchives( timesample, partname, time_samples[ timecounter ] )

            timecounter += 1

        sys.stdout = save_stdout
        archives = [ path, filenameList, shopname ]
        partionedObjects[ shopcounter ] = archives

    # return dictioanry with shopname and a list containing 
    return ( partionedObjects )


#####################################################################
#                                                                   #
# APPLESEED MISC SECTION                                            #
#                                                                   #
#####################################################################

#
# NAME:         ASmisc.py ( Python )
#
# COMMENTS:     .appleseed generation using SOHO
#


headerParms = {
    'ropname'           : SohoParm('object:name', 'string', key='ropname'),
    'hip'               : SohoParm('$HIP',        'string', key='hip'),
    'hipname'           : SohoParm('$HIPNAME',    'string', key='hipname'),
    'fps'               : SohoParm('state:fps',   'real', key='fps'),
    'soho_program'      : SohoParm('soho_program','string'),
    'soho_pipecmd'      : SohoParm('soho_pipecmd','string'),
    'target'            : SohoParm('target',      'string'),
    'hver'              : SohoParm('state:houdiniversion', 'string', ["9.0"], False, key='hver')
}


def fullFilePath( file ):
    path = sys.path
    for dir in path:
        full = os.path.join(dir, file)
        try:
            if os.stat(full):
                return full
        except:
            pass
    return file


def emitHeader( now, writer ):
    global FPS, FPSinv, SettingDefs

    rop = soho.getOutputDriver()
    roplist = rop.evaluate(headerParms, now)

    FPS = roplist['fps'].Value[0]
    FPSinv = 1.0 / FPS

    soho_program = roplist.get('soho_program', None)
    soho_pipecmd = roplist.get('soho_pipecmd', None)
    target  = roplist.get('target',  None)
    hip     = roplist.get('hip',     None)
    hipname = roplist.get('hipname', None)
    ropname = roplist.get('ropname', None)

    #check if houseed.cli is there
    #try:
    #    mplay = hou.findFile( soho_pipecmd )
    #except:
    #    soho.error

    writer.emit_comment("Houdini Version: %s" % roplist['hver'].Value[0])
    writer.emit_comment("Generation Time: %s" % time.strftime("%b %d, %Y at %H:%M:%S"))
    if soho_program:
        ("Soho Script: %s" % fullFilePath(soho_program.Value[0]))
    if target:
        writer.emit_comment("Render Target: %s" % target.Value[0])
    rendersettings = SettingDefs
    if len(rendersettings):
        writer.emit_comment( "Render Defs: %s" % rendersettings[0] )
        for i in range(1, len(rendersettings)):
            writer.emit_comment(" : %s" % rendersettings[i])
    if hip and hipname:
        writer.emit_comment("HIP File: %s/%s, $T=%g, $FPS=%g" % (hip.Value[0], hipname.Value[0], now, FPS))
    if ropname:
        writer.emit_comment("Output driver: %s" % ropname.Value[0])


#some of these params are on the geometry object (geo_velocityblur and motionstyle)
#the other parameters are set on the ROP
CamMotionParms = [
    SohoParm('allowmotionblur',      'int',    [1],          False),
    SohoParm('xform_motionsamples',  'int',    [1],          False),
    SohoParm('geo_motionsamples',    'int',    [1],          False),
    SohoParm('shutter',              'float',  [.5],         False),
    SohoParm('shutteroffset',        'float',  [1],          False),
    SohoParm('motionstyle',          'string', ['trailing'], False)
   ]


def SetCameraBlur( cam, now ):
    global CameraTimeSteps, GeoTimeSteps, FPSinv, VelocityBlurSamples

    camlist = cam.evaluate( CamMotionParms, now )
    allowblur     = camlist[0].Value[0]
    xsteps        = camlist[1].Value[0]
    gsteps        = camlist[2].Value[0]
    shutter       = camlist[3].Value[0] * FPSinv
    shutteroffset = camlist[4].Value[0]
    style         = camlist[5].Value[0]

    if style == 'centered':
        delta = shutter * 0.5
    elif style == 'leading':
        delta = shutter
    else:
        delta = 0

    #set time for transformation blur
    CameraTimeSteps = []
    if allowblur and shutter != 0 and xsteps > 1:
        t0 = now - delta
        t1 = t0 + shutter
        td  = (t1 - t0) / float( xsteps - 1 )
        for i in range( xsteps ):
            CameraTimeSteps.append( t0 )
            t0 += td
    #no transformation blur
    else:
        CameraTimeSteps.append( now )

    #gsteps has to be equal to a power of two
    if xsteps > gsteps:
        gsteps = xsteps
    gsteps = round( math.log( gsteps, 2 ) )
    gsteps =   int( math.pow(2, gsteps ) )

    #set time for geometry blur
    #treat velocity blur as a form of geo blur
    GeoTimeSteps = []
    if allowblur and shutter != 0 and gsteps > 1:
        t0 = now
        t1 = t0 + shutter
        td = (t1 - t0) / float( gsteps - 1 )
        for i in range( gsteps ):
            GeoTimeSteps.append( t0 )
            t0 += td
    else:
        GeoTimeSteps.append(now)

    # TODO: get exact time points (motionsamples influence is missing)
    blurstart = shutter + 0.5 * FPSinv * ( shutteroffset - 1 )
    blurend   = shutter + 0.5 * FPSinv * ( 1 + shutteroffset )
    # relative values from NOW
    VelocityBlurSamples = [ blurstart, blurend ]

    if allowblur and (gsteps > 1 or xsteps > 1):
        return True
    else:
        return False

#for some reason evaluating ASPRojectPaths does not work
#so a slightly more verbose way to get paths
def getProjectPaths( now ):
    searchPaths = {}
    searchPaths['as_archivepath'] = ASProjectPaths['as_archivepath']
    searchPaths['as_texturepath'] = ASProjectPaths['as_texturepath']
    searchPaths['as_shaderpath']  = ASProjectPaths['as_shaderpath']

    for key, value in searchPaths.items():
        if value == "":
            del searchPaths[key]

    #get current working directory
    rop = soho.getOutputDriver()
    hip = rop.evaluate( { 'hip' : SohoParm( '$HIP', 'string', key='hip' ) }, now )
    hippath = hip['hip'].Value[0]

    #if paths is not empty, check that paths exist
    for path in searchPaths:
        if os.path.isabs( searchPaths[path] ):
            if not os.path.exists( searchPaths[path] ):
                soho.error( 'Directory does not exist: %s' % searchPaths[path] )
        else:
            if not os.path.exists( os.path.join( hippath, searchPaths[path] ) ):
                soho.error( 'Directory does not exist: %s' % os.path.join( hippath, searchPaths[path] ) )

    return (hippath, searchPaths)


# there are three kinds of blurs, transformation, deformation and velocity blur
# transformation blur is set on the camera (moving camera). Deformation and
# velocity blur is set on the geometry object. The object can be keyframed in which
# case it probably won't have a velocity attribute.
def groupBlurObjects( objectlist, now, mblur, ipr=False ):
    objCache  = []
    staticObj = []
    dynamObj  = []

    if ipr:
        for obj in objectlist:
            if obj in objCache:
                continue
            objCache.append( obj )

            # check if we have an empty object
            soppath = []
            if not obj.evalString( 'object:soppath', now, soppath ):
                continue
            if not soppath[0]:  
                continue
            #create and initialize ASobject
            ASobj = SceneObject( obj, now, soppath[0] )

            dynamObj.append( ASobj )
        return ( None, dynamObj )

    for obj in objectlist:
        if obj in objCache:
            continue
        objCache.append( obj )

        # check if we have an empty object
        soppath = []
        if not obj.evalString( 'object:soppath', now, soppath ):
            continue
        if not soppath[0]:  
            continue
        #create and initialize ASobject
        ASobj = SceneObject( obj, now, soppath[0] )

        # the object is time dependent (animated)
        if ASobj.xblur and mblur:
            dynamObj.append( ASobj )
        # not animated but possibly deformation or
        # velocity blur, dealt with later
        else:
            staticObj.append( ASobj )

    return ( staticObj, dynamObj )


#####################################################################
#                                                                   #
# APPLESEED RENDER FRAME, collect camera, lights and geometry       #
#                                                                   #
#####################################################################

#
# NAME:         ASframe.py ( Python )
#
# COMMENTS:     parse objects, camera and lights of a houdini scene
#


import time, sys, string, math, os 

import hou, soho
from soho import SohoParm
from soho import Precision
from sohog import SohoGeometry

#import ASsettings, ASgeo, ASProjectFileWriter
#from ASsettings import SettingDefs


def getObjectWrangler( obj, now, style ):
    wrangler = obj.getDefaultedString( style, now, [''] )[0]
    wrangler = '%s-AS' % wrangler
    if style == 'light_wrangler':
        wrangler = soho.LightWranglers.get( wrangler, None )
    elif style == 'camera-wrangler':
        wrangler = soho.CameraWranglers.get( wrangler, None )
    elif style == 'object_wrangler':
        wrangler = soho.ObjectWranglers.get( wrangler, None ) 
    else:
        wrangler = None
    if wrangler:
        wrangler = wrangler( obj, now, theVersion )
    return wrangler
    

def instanceTransform( obj, time, writer ):
    xform = []

    #if "invert" in method:
    #    xform = list( hou.Matrix4( xform ).inverted().asTuple() )
    #if "swap" in method:
    #    swap_matrix = hou.Matrix4( (-1,0,0,0, 0,1,0,0, 0,0,-1,0, 0,0,0,1) )
    #    swapped = hou.Matrix4( xform ) * swap_matrix
    #    xform = list( swapped.asTuple() )
    if not obj.evalFloat( 'space:world', time, xform ):
        xform = identMat
    if len(xform) != 16:
        xform = identMat

    #always transpose the matrix, appleseed post multiplies matrices
    xform = list( hou.Matrix4( xform ).transposed().asTuple() )
    #writer.emit_transform( xform, reltime / num_samples )
    writer.emit_transform( xform, time )


def outputFlipbook():
    return 'output "rgba" "mplay" "flipbook"'


def cameraDisplay( wrangler, cam, now):
    #function used to output to flipbook or plane (in other words: select outputdevice)
    #see if we have a wrangled camera
    #TODO: get the number of planes/deeps we want to output additionally (the render layers)
    return


#TODO:render from light
#TODO:use cameraDisplay to select output device (plane, flipbook)
def defineCamera( cam, now, writer ):
    global outputParms

    name = '%s-cam' % cam.getName()
    #TODO: check if this cam exists in cache
    wrangler = getObjectWrangler( cam, now, 'camera_wrangler' )
    # cameraDisplay()
    # wrangle shaders? camera shaders?

    #default camera type
    cam_type = 'pinhole_camera'
    cam_parms = {}

    # get the standard camera properties
    proj = cam.wrangleString( wrangler, 'projection', now, ['perspective'] )[0]
    if proj == 'ortho':
        focal = ['inifinity']
        aperture = cam.wrangleFloat( wrangler, 'orthowidth', now, [2] )[0]
    else:
        focal = cam.wrangleFloat( wrangler, 'focal', now, [50] )[0]
        aperture = cam.wrangleFloat( wrangler, 'aperture', now, [41.4214] )[0]
    if proj == 'sphere':
        cam_type = 'spherical_camera'

    #parameters for depth of field (thinlens_camera)
    dof = soho.getDefaultedInt( 'dof', ['0'] )[0]
    if dof:
        #if cam_type == 'spherical_camera':
        #    soho.warning( 'Enabling depth of field will set camera to thin lens' )
        cam_parms['f_stop'] = cam.wrangleFloat( wrangler, 'f_stop', now, [5.6] )[0]
        cam_parms['focus_distance']  = cam.wrangleFloat( wrangler, 'focus', now, [5] )[0]
        #TODO: add bokeh blade numbers
        #cam_parms['diaphragm_blades'] = cam.wrangleInt( wrangler, 'bokehblades', now, [0] )[0]
        #cam_parms['diaphragm_tilt_angle'] = cam.wrangleFloat( wrangler, 'vm_bokehrotation', now, [0] )[0]
        cam_tpye = 'thinlens_camera'

    #get image resolution
    resolution = cam.wrangleInt( wrangler, 'res', now, [256, 256] )
    #does appleseed support clipping planes?
    if cam.wrangleInt( wrangler, 'override_camerares', now, [0] )[0]:
        resolution = cam.wrangleInt( wrangler, 'res_override', now, resolution )
    outputParms['resolution'] = convertToString( resolution )

    unit = cam.wrangleString( wrangler, 'focalunits', now, ['mm'] )[0]
    focal = soho.houdiniUnitLength( focal, unit )
    aperture = soho.houdiniUnitLength( aperture, unit )
    #calculate film dimensions
    resx = resolution[0]
    resy = resolution[1]
    asp  = cam.wrangleFloat( wrangler, 'aspect', now, [1] )[0]
    apx = aperture
    apy = (resy * apx) / (resx * asp)

    #set camera window and crop
    crop = cam.getCameraCropWindow( wrangler, now )
    if crop[0] != 0 and crop[1] != 1 and crop[2] != 0 and crop[3] != 1:
        crop[0] = int( (resolution[0] - 1) * crop[0] )
        crop[1] = int( (resolution[0] - 1) * crop[1] )
        crop[2] = int( (resolution[1] - 1) * crop[2] )
        crop[3] = int( (resolution[1] - 1) * crop[3] )
        outputParms['crop_window'] = convertToString( crop )

    cam_parms['film_dimensions']   = "%s %s" % (apx, apy)
    #cam_parms['film_height'   =  aperture * aspect
    cam_parms['focal_length'] = focal
    #cam_parms['focal_distance'] = focal[0]
    #cam_parms['horizontal_fov'] = 2 * math.atan( 0.5 * aperture / focal )

    return ( cam_type, cam_parms )
        

def outputCamera( cam, now, writer ):
    name = cam.getName()
    #TODO: check if cam exist in cache, then we can just exit the function

    (model, cam_parms ) = defineCamera( cam, now, writer )

    if not model:
        return None

    writer.begin_camera( name, model )
    for key in cam_parms:
        writer.emit_parm( key, cam_parms[key] )

    motion_samples = CameraTimeSteps
    for time in motion_samples:
        instanceTransform( cam, time, writer )
            
    writer.end_camera()
    return name


#TODO: create a wrangler for the light and for the cam
def defineLight( light, now, writer ):
    name = '%s-light' % light.getName()
    wrangler = getObjectWrangler( light, now, 'light_wrangler' )

    light_parms = {}

    #get some light properties
    lightType = light.wrangleString( wrangler, 'light_type', now, ['point'] )[0]
    # translate light to appleseed light
    if lightType == 'point':
        lightType = 'point_light'
    if lightType == 'distant':
        lightType = 'directional_light'
    if light.wrangleInt( wrangler, 'coneenable', now, [0])[0]:
        lightType = 'spot_light'
        light_parms['outer_angle'] = light.wrangleFloat( wrangler, 'coneangle', now, [45] )[0]
        light_parms['inner_angle'] = light.wrangleFloat( wrangler, 'conedelta', now, [10] )[0]
        #light_parms['tilt_angle'] = light.wrangleFloat( wrangler, 'tiltangle', now [0] )
    if lightType == 'sun':
        lightType = 'sun_light'

    #common parameters
    light_parms['radiance_multiplier'] = light.wrangleFloat( wrangler, 'light_intensity', now, [1.0] )[0]
    #radiance can also be a color
    light_parms['radiance'] = light.wrangleFloat( wrangler, 'radiance', now, [1.0] )[0]
    light_parms['importance_mulitplier'] = light.wrangleFloat( wrangler, 'importance_multiplier', now, [1.0] )[0]
    light_parms['cast_indirect_light']   = light.wrangleString( wrangler, 'indirect_light', now, ['true'] )[0]

    #TODO: light color with wavelengths?
    return ( lightType, light_parms )
    

#create light instance of light
def outputLight( light, now, writer ):
    name = light.getName()
    #TODO: cache light, does it already exist? for example when we instance
    #lights there is already one master object

    #create actual light
    (light_type, light_parms) = defineLight( light, now, writer )
    #TODO: some intstance function to write instance
    #TODO: auto headlight

    writer.begin_light( name, light_type )
    for key in light_parms:
        writer.emit_parm( key, light_parms[key] )
    instanceTransform( light, now, writer )
    writer.end_light()
    return name


def outputGeometry( ASobj, now, writer ):
    name = '%s-geo' % ASobj.getName()
    # saved_archives is a dict with a number as key and a list as value
    # the list contains the path, a list with files, and shadername
    saved_archives = parseGeoObject( ASobj, now, name )

    # objectname : shader
    instances = {}
    if saved_archives:
        material_count = 0
        for key in saved_archives:
            objname = name +  '_%s' % material_count
            parms   = saved_archives[ key ]
            instances[ objname ] = parms[2]
            writer.begin_object( objname )
            if len( parms[1] ) > 1:
                writer.begin_parm( 'filename' )
                for index, files in enumerate( parms[1] ):
                    writer.emit_parm( index, parms[0] + '/' + files + '.obj' )
                writer.end_parm()
            else:
                writer.emit_parm( 'filename', parms[0] + '/' + parms[1][0] + '.obj' )
            writer.end_object()
            material_count += 1
        return ( instances )
    else:
        soho.warning( "No geometry returned on object: %s" % ASobj.getName() )
        return False


def outputGeometryInstance( obj, now, writer ):
    # TODO: this function will be a place holder for
    # future procedural geometry shaders
    instances = outputGeometry( obj, now, writer )
    return instances


def outputInstances( scene, now, writer ):
    for ASobj in scene:
        instances = scene[ASobj]
        #objName = instances[ ASobj ].keys()[0]
        #shopName  = instances[ ASobj ].values()[0]

        for geo in instances:
            objName  = geo
            shopName = instances[ geo ]

            instName = objName + ".inst"
            writer.begin_object_instance( instName, objName + ".0" )
            instanceTransform( ASobj.obj, now, writer )
            if shopName != None:
                shopName = "/mat" + shopName
                writer.emit_assign_material( shopName, 'front', shopName )
                writer.emit_assign_material( shopName, 'back' , shopName )
            else:
                writer.emit_comment(" No shader or material on object ")
            writer.end_object_instance()


# sub assemblies are used for geometry with transformation blur or for IPR renders
def instanceSubAssemblies( subs, now, writer ):
    motion_samples = CameraTimeSteps

    for assem_name in subs:
        writer.begin_assembly_instance( assem_name + "_instance_0", assem_name )
        ASobj = subs[ assem_name ]
        if ASobj.xblur:
            for time in motion_samples:
                instanceTransform( ASobj.obj, time, writer )
        else:
            instanceTransform( ASobj.obj, now, writer )
        writer.end_assembly_instance()


def instanceMasterAssembly( writer ):
    writer.begin_assembly_instance( "master.inst", "master" )
    writer.emit_transform()
    writer.end_assembly_instance()
        

def outputOutput( cam, now, writer ):
    global outputParms, ASOutputSettings
 
    writer.begin_output()
    writer.begin_frame()

    for entry in ASOutputSettings:
        writer.emit_parm( entry, ASOutputSettings[entry] )
    for entry in outputParms:
        writer.emit_parm( entry, outputParms[entry] )

    writer.end_frame()
    writer.end_output()


#all the <configurations></configurations> stuff should go here
def outputConfig( cam, now, writer ):
    global configParms, ASConfigSettings, ASRayTracer, ASPathTracer, ASPhotonMapping

    writer.begin_configurations()
    writer.begin_configuration( True )

    for entry in ASConfigSettings:
        writer.emit_parm( entry, ASConfigSettings[entry] )

    if ASConfigSettings['pixel_renderer'] == 'uniform':
        writer.begin_parm( 'uniform_pixel_renderer' )
        for entry in ASUniformSampler:
            writer.emit_parm( entry, ASUniformSampler[entry] )
        writer.end_parm()
    else:
        writer.begin_parm( 'adaptive_pixel_renderer' )
        for entry in ASAdaptiveSampler:
            writer.emit_parm( entry, ASAdaptiveSampler[entry] )
        writer.end_parm()

    if ASConfigSettings['lighting_engine'] == "drt":
        writer.begin_parm( 'drt' )
        for entry in ASRayTracer:
            writer.emit_parm( entry, ASRayTracer[entry] )
        writer.end_parm()
    elif ASConfigSettings['lighting_engine'] == "pt":
        writer.begin_parm( 'pt' )
        for entry in ASPathTracer:
            writer.emit_parm( entry, ASPathTracer[entry] )
        writer.end_parm()
    else:
        writer.begin_parm( 'sppm' )
        for entry in ASPhotonMapping:
            writer.emit_parm( entry, ASPhotonMapping[entry] )
        writer.end_parm()

    #for user configuration?
    for entry in configParms:
        writer.emit_parm( entry, configParms[entry] )

    writer.end_configuration()

    #empty interactive configuration
    writer.begin_configuration( False )
    writer.end_configuration()

    writer.end_configurations()


# here the misery really starts
def Render( cam, now, objectlist, lightlist, writer ):
    emitHeader( now, writer )

    writer.begin_project()
    (cwd, paths) = getProjectPaths( now )
    writer.emit_searchpaths( paths.values() )
    paths['hip'] = cwd
    writer.begin_scene()

    mblur = SetCameraBlur( cam, now )
    camName = outputCamera( cam, now, writer )

    if camName:
        writer.begin_assembly( 'master' )

        for light in lightlist:
            outputLight( light, now, writer )

        (master, subs) = groupBlurObjects( objectlist, now, mblur )

        sceneObjs = {}
        # sub assemblies
        for index, ASobj in enumerate( subs ):
            sub_assem_name = 'sub' + str( index )
            sceneObjs[ sub_assem_name ] = ASobj
            writer.begin_assembly( sub_assem_name )
            instance = outputGeometryInstance( ASobj, now, writer )
            outputInstances( { ASobj : instance }, now, writer )
            writer.end_assembly()
        instanceSubAssemblies( sceneObjs, now, writer )

        # content of the master assembly
        sceneObjs.clear()
        for ASobj in master:
            sceneObjs[ ASobj ] = outputGeometryInstance( ASobj, now, writer ) 
        outputInstances( sceneObjs, now, writer )

        outputMaterial( now, writer )

        writer.end_assembly()
        instanceMasterAssembly( writer )

        writer.end_scene()
    
        # TODO: rules for aov
        outputOutput( cam, now, writer )
        outputConfig( cam, now, writer )

        writer.end_project()

    else:
        soho.error( "Error evaluating camera parameters: %s" % cam.getName() )


#####################################################################
#                                                                   #
# APPLESEED SOHO                                                    #
#                                                                   #
#####################################################################

#
# NAME:     AS.py ( Python )
#
# COMMENTS: Main routine for SOHO Appleseed export
#

import time
import sys
import os

import soho
from soho import SohoParm
from soho import Precision


def main():
    debug_mode = False
    logger = AsLogger( debug_mode )
    logger.log_debug( "Starting appleseed export\n")

    parmlist = soho.evaluate({  'now'   : SohoParm('state:time', 'real',   [0],         False, key = 'now'),
                                'camera': SohoParm('camera',     'string', '/obj/cam1', False, key = 'camera')})

    now = parmlist['now'].Value[0]
    cam = parmlist['camera'].Value[0]

    if not soho.initialize( now, cam):
        soho.error( 'Unable to initialize rendering module with given camera')

    for cam in soho.objectList( 'objlist:camera'):
        break
    else:
        soho.error( 'Unable to find viewing camera for render')

    # Candidate object selection
    objectSelection = {
                        'vobject'       : SohoParm( 'vobject',       'string', ['*'], False),
                        'alights'       : SohoParm( 'alights',       'string', ['*'], False),
                        'forceobject'   : SohoParm( 'forceobject',   'string', [''] , False),
                        'forcelights'   : SohoParm( 'forcelights',   'string', [''] , False),
                        'excludeobject' : SohoParm( 'excludeobject', 'string', [''] , False),
                        'excludelights' : SohoParm( 'excludelights', 'string', [''] , False),
                        'sololight'     : SohoParm( 'sololight',     'string', [''] , False)
                       }
    objparms = cam.evaluate( objectSelection, now)

    stdobject       = objparms['vobject'].Value[0]
    stdlights       = objparms['alights'].Value[0]
    forceobject     = objparms['forceobject'].Value[0]
    forcelights     = objparms['forcelights'].Value[0]
    excludeobject   = objparms['excludeobject'].Value[0]
    excludelights   = objparms['excludelights'].Value[0]
    sololight       = objparms['sololight'].Value[0]
    forcelightsparm = 'forcelights'

    if sololight:
        stdlights = excludelights = ''
        forcelights = sololight
        forcelightsparm = 'sololight'

    # First, we add objects based on their display flags or dimmer values
    soho.addObjects( now, stdobject, stdlights, '', True, geo_parm = 'vobject', light_parm = 'alights', fog_parm = '')
    soho.addObjects( now, forceobject, forcelights, '', False, geo_parm = 'forceobject', light_parm=forcelightsparm, fog_parm = '')
    soho.removeObjects( now, excludeobject, excludelights, '', geo_parm = 'excludeobject', light_parm = 'excludelights', fog_parm = '')

    # Lock off the objects we've selected
    soho.lockObjects( now)

    # how fast are we?
    clockstart = time.time()

    rop = soho.getOutputDriver()
    filename = rop.evaluate({ 'soho_diskfile' : SohoParm( 'soho_diskfile', 'string')}, now)['soho_diskfile'].Value[0]

    # initialize AsProjectFileWriter 
    writer = AsProjectFileWriter( filename, logger )

    Render( cam, now, soho.objectList('objlist:instance'), soho.objectList('objlist:light'), writer )

    # finish project file!
    writer.emit_comment( 'Script generation time %g seconds' % (time.time() - clockstart) )
    writer.close_project_file()


    # completely untested...
    '''
    render_mode = soho.getDefaultedInt( 'as_render_mode', [''] )[0]

    # call appleseed.cli if needed.
    if render_mode == 0: # render & export
        file_type = soho.getDefaultedInt( 'as_filetype', [''] )[0]
    
        cmd = ['appleseed.cli']

        if file_type == 0: # mplay
            cmd.append( '--mplay' )
            cmd.append( filename )
        else:
            cmd.append( filename )
            img_file_name = soho.getDefaultedString( 'as_filename', [''] )[0]
            cmd.append( ' -o ' + img_file_name)

        sys.__stdout__.write(  ' '.join( cmd ) )
        subprocess.Popen( cmd)
    '''

#
# call our entry point!
#

main()
