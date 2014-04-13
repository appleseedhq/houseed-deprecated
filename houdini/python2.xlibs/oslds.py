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


import os, sys, tempfile, time


_HoudiniShaderMap = {
'surface'       : 'surface',
'displacement'  : 'displace',
'volume'        : 'fog',
'light'         : 'light',
'shader'        : 'surface'
}


def _HoudiniType( tp ):
    if tp.find( 'int' ) >= 0:
        return( 'int', 1 )
    if tp.find( 'point' ) >= 0:
        return( 'float', 3 )
    if tp.find( 'vector' ) >= 0 or tp.find('normal') >= 0:
        return( 'direction', 3 )
    if tp.find( 'color' ) >= 0:
        return( 'color', 3 )
    if tp.find( 'string' ) >= 0:
        return( 'file', 1 )
    if tp.find( 'matrix' ) >= 0:
        return( 'float', 16 )
    if tp.find( 'shader' ) >= 0:
        return( 'oppath', 1 )
    if tp.find( 'float' ) >= 0:
        return( 'float', 1 )
    sys.stderr.write( 'Warning: unknown OSL type "%s"\n' % tp )
    return( 'float', 0 )


# create menu in string format and append to Hextra
# return Htype, append UI to a list
def _HoudiniUI( uilist, uiType, uiOptions=None ):
    if 'popup' in uiType or 'mapper' in uiType:
        # convert uiOptions to a dict
        menu = dict()
        if ':' in uiOptions:
            for entry in uiOptions.split('|'):
                (value, key) = entry.replace('"','').split(':')
                menu[key] = value
        else:
            for entry in uiOptions.split('|'):
                (value, key) = (entry.replace('"',''), entry.replace('"',''))
                menu[key] = value
        # convert dict to a formated string
        indent='        '
        uilist.append(indent + 'menu {')
        for entry in menu:
            uilist.append(indent + "    \"%s\" \"%s\"" % (entry, menu[entry]))
        uilist.append(indent + '}')
        return ('ordinal')
    if 'checkBox' in uiType or 'boolean' in uiType:
        return ('toggle')
    if 'null' in uiType:
        # return Hextra, Htype stays unchanged
        uilist.append(indent + 'invisible')
        return (None)
    else:
        return(None)

class OslParmDS:
    def __init__( self, parmName, parmType ):
        self.Type      = parmType
        self.Name      = parmName
        self.Label     = parmName.replace('_', ' ')
        self.ArraySize = None
        self.Default   = None
        self.Help      = None
        self.UItype    = None
        self.Hextra    = None
        self.Range     = None
        (self.HType, self.HSize) = _HoudiniType( self.Type )

    def setLabel( self, label ):
        self.Label = label.strip()

    def setArraySize( self, size ):
        self.ArraySize = size

    def setDefault( self, value ):
        if len(value) == 0:
            value = '""'
        self.Default = value

    def setHelp( self, osl_help ):
        self.Help = osl_help

    def setUI( self, widgets, options=None ):
        uiextra = list()
        for entry in widgets:
            uitype = _HoudiniUI(uiextra, entry, options)
        if uitype is not None:
            self.HType  = uitype
            if self.HType == 'toggle':
                if self.Default == 0:
                    self.Default = 'off'
                else:
                    self.Default = 'on'
        if uiextra is not None:
            self.Hextra = uiextra
 
    def setRange( self, parmMinMax ):
        self.Range = parmMinMax
    
    def printParm( self ):
        print self.Name
        print self.Label
        print self.Type
        print self.Default
        print self.ArraySize
        print self.Hsize
        print self.Help
        print self.Htype
        print self.Hextra
        print "\n"

    def saveParm( self, fp, indent='' ):
        n = self.HSize * self.ArraySize
        fp.write( indent + '    parm {\n')
        fp.write( indent + '        name "%s"\n' % self.Name )
        fp.write( indent + '        label "%s"\n' % self.Label )
        fp.write( indent + '        type %s\n' % self.HType )
        fp.write( indent + '        size %d\n' % n )
        fp.write( indent + '        export none\n' )
        if self.Range:
            fp.write( indent + '        range { %s %s }\n' % (self.Range[0], self.Range[1]) )
        if self.ArraySize > 1:
            fp.write( indent + '        parmtag { script_osltype "%s[%d]" }\n' % ( self.Type, self.ArraySize ) )
        else:
            fp.write( indent + '        parmtag { script_osltype "%s" }\n' % self.Type )
        if self.Default:
            fp.write( indent + '        default {')
            if type( self.Default ) is list:
                self.Default = ' '.join('"' + entry + '"' for entry in self.Default )
            else:
                self.Default = '"' + self.Default + '"'
            fp.write(' %s' % self.Default)
            fp.write(' }\n')
        if self.Help:
            fp.write( indent + '        help "%s"\n' % self.Help )
        if self.Hextra:
            for entry in self.Hextra:
                fp.write( indent + entry + '\n' )
        fp.write( indent + '    }\n' )


class OslShaderDS:
    def __init__( self, shader_type, shader_name, shader_path=None ):
        self.Type = _HoudiniShaderMap.get( shader_type )
        self.Name = shader_name
        if shader_path is not None:
            self.Path = shader_path
        else:
            self.Path = shader_name
        self.Label = self.Name
        self.Help = None
        self.Icon = None
        self.Parms = (list(), dict())
        # empty dictionary
        self.ParmNames = {}
        self.HType = _HoudiniShaderMap.get( shader_type )
        # self.HType = self.Type
        if not self.HType:
            sys.stderr.write( 'Unknown shader type "%s" for %s\n' % (shader_type, shader_name) )

    def setName( self, name ):
        if name:
            if self.Label == self.Name:
                self.label = name
            self.Name = name

    def setLabel( self, label ):
        if label:
            self.Label = label

    def setHelp( self, oslhelp ):
        self.Help = oslhelp

    def setIcon( self, icon ):
        self.Icon = icon

    def setPath(self, path):
        if path:
            self.Path = path

    def addParm( self, parm, tab = None ):
        if self.ParmNames.has_key( parm.Name ):
            sys.stderr.write( 'Duplicate parameter name: %s\n' % parm.Name )
        else:
            if tab is None:
                self.Parms[0].append( parm )
            else:
                tmpPageDict = self.Parms
                for subTab in tab:
                    if not tmpPageDict[1].has_key( subTab ):
                        tmpPageDict[1][ subTab ] = (list(), dict())
                    tmpPageDict = tmpPageDict[1][ subTab ]
                tmpPageDict[0].append(parm)
                    

    def saveDialogScript( self, fp ):
        fp.write('{\n')
        fp.write('    name\t%s\n' % self.Name)
        fp.write('    script\t%s\n' % self.Path)
        fp.write('    label\t"%s"\n' % self.Label)
        fp.write('    rendermask\tOSL\n')
        if self.Help:
            fp.write('    help {\n')
            for line in self.Help:
                fp.write('        "%s"\n' % line.replace('"', '\\"'))
            fp.write('    }\n\n')

        def writeParms(parameters, tabs, indent=''):
            # write parameters
            for parm in parameters:
                 parm.saveParm(fp, indent=indent)
            # write tabs
            for subTab in tabs.keys():
                fp.write( indent + "group {\n")
                fp.write( indent + "    name  \"%s\"\n" % subTab.replace(' ', '_') )
                fp.write( indent + "    label \"%s\"\n" % subTab )
                newIndent = indent + '    '
                writeParms( tabs[subTab][0], tabs[subTab][1], newIndent )
                fp.write( indent + "}\n" )

        writeParms( self.Parms[0], self.Parms[1], indent='    ')
        fp.write('}\n')
        return True

    def makeOTL( self, otl_path ):
        tmpdir = tempfile.mkdtemp(prefix='oslds')

        # create otl header
        with open( tmpdir + '/Sections.list', 'w' ) as fp:
            fp.write( '""\nINDEX__SECTION INDEX_SECTION\nShop_1%s Shop/%s\n' % (self.Name, self.Name) )

        with open( tmpdir + '/INDEX__SECTION', 'w' ) as fp:
            fp.write( 'Operator: %s\n' % self.Name )
            fp.write( 'Label: %s\n' % self.Label )
            fp.write( 'Path: oplib:/Shop/%s?Shop/%s\n' % (self.Name, self.Name) )
            if self.Icon:
                fp.write( 'Icon: %s\n' % self.Icon )
            fp.write( 'Table: Shop\n' )
            fp.write( 'Extra: %s\n' % self.HType )
            fp.write( 'Inputs: 0 to 0\n' )
            fp.write( 'Subnet: false\n' )
            fp.write( 'Python: false\n' )
            fp.write( 'Empty: false\n' )
            now = time.strftime( '%a %b %d %H:%M:%S %Y' )
            fp.write( 'Modified: %s\n' % now )

        # create content dir
        contents_dir = tmpdir + ('/Shop_1%s' % self.Name)
        os.mkdir( contents_dir )

        with open( contensts_dir + '/Sections.list', 'w' )
            fp.write( '""\nDialogScript DialogScript\n' )

        with open( contents_dir + '/DialogScript', 'w' )
            self.saveDialogScript(fp)
            fp.close()

        # compile and assemble otl
        cmd = 'hotl -c "%s" "%s"' % ( tmpdir, otl_path )
        status = os.system(cmd)

        # remove temporary files
        os.remove( tmpdir + '/INDEX__SECTION' )
        os.remove( tmpdir + '/Sections.list' )
        os.remove( contents_dir + '/DialogScript' )
        os.remove( contents_dir + '/Sections.list' )
        os.rmdir( contents_dir )
        os.rmdir( tmpdir )

        return True

    def addToOTL(self, otl_path, force=True):
        if not self.HType:
            return False

        tmpotl = tempfile.mktemp( prefix='oslds' )
        self.makeOTL( tmpotl )
        
        if force:
            option = '-M'
        else:
            option = '-m'
        cmd = 'hotl "%s" "%s" "%s"' % (option, tmpotl, otl_path)
        status = os.system( cmd )
    
        os.remove( tmpotl )
        return True
