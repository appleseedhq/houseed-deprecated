#!/usr/bin/env hython

# osl2otl.py
#
# copyright Hans Hoogenboom 2013
#
# Translation script to create a houdini digital
# asset from a compiled openshadinglanguage shader 

# TODO:  URL as help
#        export keyword
#        output keyword
#        closure keyword?

import sys, os, optparse
import oslparser, oslds

#----------------------------------------------------------
# Functions         
#----------------------------------------------------------

def error( msg, crash = False ):
    sys.stderr.write( msg )
    sys.stderr.write( '\n' )
    if crash:
        sys.exit(1)
    return False


def checkFiles( args ):
    for shaderfile in args:
        reg_file = os.path.isfile( shaderfile )
        if not reg_file:
            error( "File does not exist: %s" % shaderfile, True )


def queryValues( oslType, st ):
    if oslType == "string":
        return(st, 1)
    else:
        obracket = st.find( '[' )
        cbracket = st.find( ']' )
        if obracket < 0:
            value = st.replace(' ', '')
            return(value, 1)
        else:
            st = st[obracket+2: cbracket-1]
            value = st.split()
            if oslType in ["float", "int"]:
                size = len(value)
            else:
                size = 1
            return( value, size )


def createDS( shader ):
    try:
        ds = oslds.OslShaderDS( shader['type'], shader['name'] )
    except NameError:
        error( "Could not create shader %s." % shader['name'] )
        
    # basic help section for dialogscript
    oslHelp = [
        '#type: node',
        '#content: shop',
        '#tags: osl,shader',
        '#icon: NETWORKS/shop',
        '',
        '= %s =' % ds.Name,
        '']
    if 'help' in shader:
        if len(shader['help']) > 2:
            oslHelp.extend( replaceQuotes( shader['help'] ).split('\n') )
    # check if we have metadata help on parms
    if shader['hasParmHelp'] == True:
        oslHelp.append('@parameters')
        oslHelp.append('')

    # add shader parameters to dialogscript
    parmnames = shader['parmlist']
    for name in parmnames:
        parm = shader[name]
        # check if a parameter name starts with output
        # get rid of it
        _name = parm["name"].split()
        if len( _name ) > 1:
            print( _name )
        # create houdini ds parm
        oslParm = oslds.OslParmDS( parm['name'], parm['type'] )
        #set label
        if 'label' in parm:
            oslParm.setlabel( parm['label'] )
        # get and set values and arraysize
        parmvalues = parm['value']
        (values, asize) = queryValues( oslParm.Type, parmvalues )
        oslParm.setDefault( values )
        oslParm.setArraySize( asize )
        # set range on parameter
        if 'UImin' in parm:
            range_v = [parm['UImin'], parm['UImax']]
            oslParm.setRange( range_v )
        # set help on parameter
        if 'help' in parm:
            oslHelp.append('    ' + parm['name'] + ':')
            oslHelp.append('       ' + parm['help'] ) 
            oslParm.setHelp( parm['help'] )
        # set special ui stuff
        if 'widget' in parm:
            if 'mapper' in parm['widget'] or 'popup' in parm['widget']:
                if 'options' in parm:
                    oslParm.setUI( parm['widget'], parm['options'] )
                else:
                    error("No menu entries found: %s" % parm['name'])
            else:
                oslParm.setUI( parm['widget'], None )
        # set tab/page of parameter
        oslParmPage = list()
        if 'page' in parm:
            page = parm['page'].replace('"','',2)
            oslParmPage = page.split('.')
        # add parm to dialogscript
        ds.addParm( oslParm, oslParmPage )
    
    if 'label' in shader:
        ds.setLabel( shader['label'] )
    ds.setHelp( oslHelp )
    # return the shader dialogscript
    return ds


#----------------------------------------------------------
# Main body
#----------------------------------------------------------

usage = """%prog [options] [shaderfiles]
osl2otl converts compiled OSL (openshadinglanguage)
shaders into a HDA or adds it to an existing OTL.
"""

parser = optparse.OptionParser( usage )

parser.add_option( "-v", action="store_true", dest="verbose", help="Output verbosity." )
parser.add_option( "-s", action="store_true", dest="source", help="Parse shader source file instead of object file." )
parser.add_option( "-l", action="store", dest="hdafile", help="Create a Houdini digital asset for a single shader." )
parser.add_option( "-L", action="store", dest="otlfile", help="Add shader to an existing digital asset library." )
parser.add_option( "-N", action="store", dest="label", help="For a single .oso file, specify the label in the menu." )
parser.add_option( "-C", action="store", dest="iconfile", help="For a single .oso file, specify the icon in the menu." )
parser.add_option( "-n", action="store", dest="shopname", help="For a single .oso file, specify the name in the menu." )
parser.add_option( "-p", action="store", dest="shoppath", help="For a single .oso file, specify the name in the menu." )

(options, args) = parser.parse_args()

if len( sys.argv[1:] ) == 0:
    parser.print_help()
    error( "", True )
if len( args ) == 0:
    error( "No shader files specified.", True )
else:
    checkFiles(args )

hdaFile = options.hdafile
otlFile = options.otlfile
label   = options.label
icon    = options.iconfile
name    = options.shopname
path    = options.shoppath
verbose = options.verbose

for oso in args:
    if verbose:
        print("Processing: %s" % oso)
    # create ds object
    shader = oslparser.parseOslInfo( oso )
    if not shader:
        continue
    ds = createDS( shader )
    ds.setIcon( icon )
    ds.setName( name )
    ds.setPath( path )
    ds.setLabel( label )
    if hdaFile:
        ds.makeOTL( hdaFile )
    else:
        ds.addToOTL( otlFile )
