"""Real native widget definitions, with engine resource allocation stubbed."""
from harness import *
import subprocess
def native(path):
    p=GAME/path
    return p.read_text(encoding='utf-8-sig') if p.is_file() else subprocess.check_output(['git','-c','gc.auto=0','show','HEAD:'+path],cwd=GAME).decode('utf-8-sig')
def method(source,owner,name):
    return owner+'.'+name+' = function'+source.split(owner+'.'+name+' = function',1)[1].split('\nend',1)[0]+'\nend\n'
L.execute('''
table.clone=table.clone_instance
function table.append(a,b) for _,v in ipairs(b) do a[#a+1]=v end;return a end
Color=setmetatable({}, {__index=function() return function(alpha) return {alpha or 255,180,180,180} end end})
Colors={color_copy=function(a,b) for i=1,4 do b[i]=a[i] end end,color_lerp=function(a,b,t,out) for i=1,4 do out[i]=a[i]+(b[i]-a[i])*t end end}
Fonts={button_primary={font_size=24,text_color={255,255,255,255},default_color={255,180,180,180},hover_color={255,255,255,255},disabled_color={255,90,90,90}},body={font_size=20}}
UIWidget={};UIRenderer={};UIScenegraph={init_scenegraph=function(g) return g end,update_scenegraph=function() end}
TalentView={};UIHud={};InputManager={};InputService={};Definitions={overlay_scenegraph_definition={},widget_definitions={}}
BaseView={}
function BaseView:init(definitions,settings,context)
 self._definitions=definitions;self._ui_scenegraph=table.clone_instance(definitions.scenegraph_definition);self._widgets_by_name={}
 for name,d in pairs(definitions.widget_definitions) do self._widgets_by_name[name]=UIWidget.init(name,d) end
end
function BaseView:on_enter() end
function BaseView:on_exit() end
function BaseView:update() return self._pass_input,self._pass_draw end
function BaseView:_set_scenegraph_position(id,x,y,z) self._ui_scenegraph[id].position={x,y,z or 3} end
function BaseView:_set_scenegraph_size(id,w,h) self._ui_scenegraph[id].size={w,h} end
function class(name,parent) local c={super=_G[parent]};c.__index=c;setmetatable(c,{__index=c.super});_G[name]=c;return c end
''')
for key, value in {
'scripts/utilities/ui/colors':L.globals().Colors,'scripts/managers/ui/ui_font_settings':L.globals().Fonts,
'scripts/managers/ui/ui_widget':L.globals().UIWidget,'scripts/managers/ui/ui_renderer':L.globals().UIRenderer,
'scripts/managers/ui/ui_scenegraph':L.globals().UIScenegraph,'scripts/managers/ui/ui_hud':L.globals().UIHud,
'scripts/managers/input/input_manager':L.globals().InputManager,'scripts/managers/input/input_service':L.globals().InputService,
'scripts/ui/views/talent_builder_view/talent_builder_view':L.globals().TalentView,
'scripts/ui/views/talent_builder_view/talent_builder_view_definitions':L.globals().Definitions,
'scripts/ui/views/base_view':L.globals().BaseView,
}.items():cache[key]=value
cache['scripts/managers/input/input_utils']=L.execute(native('scripts/managers/input/input_utils.lua'))
for key in ('scripts/ui/pass_templates/list_header_templates',
            'scripts/settings/ui/ui_sound_events','scripts/utilities/ui/text','scripts/managers/ui/ui_resolution'):
    cache[key]=tbl({})
buttons=native('scripts/ui/pass_templates/button_pass_templates.lua')
def assignment(symbol):return symbol+' = '+buttons.split(symbol+' = ',1)[1].split('\n}',1)[0]+'\n}\n'
prelude=buttons.split('ButtonPassTemplates.terminal_list_button_background_change_function =',1)[0]
templates=L.execute(prelude+assignment('local default_button_content')+assignment('ButtonPassTemplates.terminal_button')+'\nreturn ButtonPassTemplates')
cache['scripts/ui/pass_templates/button_pass_templates']=templates
cache['scripts/ui/pass_templates/scrollbar_pass_templates']=L.execute(native('scripts/ui/pass_templates/scrollbar_pass_templates.lua'))
for name in ('default_pass_styles','default_pass_values'):
    cache['scripts/ui/'+name]=L.execute(native('scripts/ui/'+name+'.lua'))
cache['scripts/settings/ui/ui_workspace_settings']=L.execute(native('scripts/settings/ui/ui_workspace_settings.lua'))
source=native('scripts/managers/ui/ui_widget.lua')
for name in ('create_definition','add_definition_pass'):
    L.execute('local DefaultPassStyles=require("scripts/ui/default_pass_styles"); local DefaultPassValues=require("scripts/ui/default_pass_values");'+method(source,'UIWidget',name))
L.execute('local UIPasses=setmetatable({}, {__index=function() return {init=function() return {} end} end});'+source[source.index('local function initialize_pass_definitions'):source.index('UIWidget.animate =')])
def plain(value):
    if hasattr(value,'items'):return {k:plain(v) for k,v in value.items()}
    return value
