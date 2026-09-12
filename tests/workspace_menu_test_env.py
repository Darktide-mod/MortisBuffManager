"""Native menu-panel behavior; renderer/font measurement are engine boundaries."""
import re, subprocess

def install(L, root):
    game=root/'dev-support/game-source'
    def native(path):
        return subprocess.check_output(
            ['git','-c','gc.auto=0','show','HEAD:'+path],cwd=game).decode('utf-8-sig')
    sources={}
    for path in ('scripts/settings/ui/ui_workspace_settings',
                 'scripts/ui/view_elements/view_element_menu_panel/view_element_menu_panel_settings',
                 'scripts/ui/view_elements/view_element_menu_panel/view_element_menu_panel_definitions',
                 'scripts/ui/view_elements/view_element_menu_panel/view_element_menu_panel',
                 'scripts/ui/pass_templates/scrollbar_pass_templates'):
        sources[path]=native(path+'.lua')
    L.globals().native_menu_sources=L.table_from(sources)
    L.execute('''
RESOLUTION_LOOKUP={width=1920,height=1080,scale=1}
table.clone=table.clone_instance
function table.append(t,other) for _,value in ipairs(other) do t[#t+1]=value end;return t end
function settings(_,t) return t end
function math.index_wrapper(n,total) return (n-1)%total+1 end
Utf8={upper=string.upper}
Color=setmetatable({}, {__index=function() return function(a) return {a or 255,1,1,1} end end})
function callback(object,name,...)
 if type(object)=="function" then return object end
 local args={...};return function() return object[name](object,unpack(args)) end
end
local old_require=require
local cache={}
local buttons={menu_panel_button={{content_id="hotspot",pass_type="hotspot",style_id="hotspot"},
 {pass_type="text",style_id="text",value_id="text",style={font_size=36,text_fit_with=true}}}}
local uiwidget={create_definition=function(passes,scene,content,size)
 local d={passes=passes,scenegraph_id=scene,content=table.clone_instance(content or {}),style={}}
 d.content.size=table.clone_instance(size or {100,100})
 for _,pass in ipairs(passes) do
  if pass.content_id then d.content[pass.content_id]=table.clone_instance(pass.content or {}) end
  if pass.value_id and d.content[pass.value_id]==nil then d.content[pass.value_id]=pass.value end
  if pass.style_id then d.style[pass.style_id]=table.clone_instance(pass.style or {}) end
 end
 return d
end}
ViewElementBase={};ViewElementBase.__index=ViewElementBase
function ViewElementBase:init(parent,layer,scale,defs)
 self._parent=parent;self._render_scale=scale;self._draw_layer=layer
 self._ui_scenegraph=table.clone_instance(defs.scenegraph_definition)
 BaseView.init(self,defs,{},{});self._using_cursor_navigation=true
end
for _,name in ipairs({"_create_widget","_unregister_widget_name"}) do ViewElementBase[name]=BaseView[name] end
function ViewElementBase:set_render_scale(v) self._render_scale=v end
function ViewElementBase:on_resolution_modified(v) self._render_scale=v end
function ViewElementBase:_set_scenegraph_position(id,x,y)
 local p=self._ui_scenegraph[id].position;if x then p[1]=x end;if y then p[2]=y end
end
function ViewElementBase:_play_sound(s) self._last_sound=s end
function ViewElementBase:update() end
function ViewElementBase:destroy() self._destroyed=true;self._widgets_by_name={};self._widgets={} end
function class(name,parent)
 local base=parent=="ViewElementBase" and ViewElementBase or BaseView
 local c={super=base};c.__index=c;setmetatable(c,{__index=base})
 function c:new(...) local o=setmetatable({},self);o:init(...);return o end
 return c
end
local Grid={}
function Grid:new(widgets,alignment,scene,id,direction,spacing)
 local length=0
 for i,w in ipairs(widgets) do
  w.offset[1]=length;length=length+w.content.size[1]+(i<#widgets and spacing[1] or 0)
 end
 return {length=function() return length end,set_render_scale=function() end,
  update=function() end,on_resolution_modified=function() end}
end
local Legend={}
function Legend:new() return setmetatable({_entries={}}, {__index=self}) end
function Legend:set_render_scale() end
function Legend:add_entry(label,action,visible,cb,side)
 self._entries[#self._entries+1]={display_name=label,input_action=action,visibility_function=visible,on_pressed_callback=cb,side=side}
end
function Legend:update(_,_,input)
 for _,e in ipairs(self._entries) do
  e.is_visible=not e.visibility_function or e.visibility_function()
  if e.is_visible and input:get(e.input_action) then e.on_pressed_callback() end
 end
end
function Legend:destroy() self._destroyed=true end
function require(path)
 if cache[path] then return cache[path] end
 if native_menu_sources[path] then
  local result=assert(loadstring(native_menu_sources[path],"@"..path))();cache[path]=result;return result
 end
 if path=="scripts/managers/ui/ui_font_settings" then return {body={}} end
 if path=="scripts/managers/ui/ui_widget" then return uiwidget end
 if path=="scripts/ui/pass_templates/button_pass_templates" then return buttons end
 if path=="scripts/managers/input/input_utils" then return {input_text_for_current_input_device=function(_,k) return k end} end
 if path=="scripts/managers/ui/ui_renderer" then return {} end
 if path=="scripts/managers/ui/ui_resolution" or path=="scripts/utilities/ui/colors" then return {} end
 if path=="scripts/ui/widget_logic/ui_widget_grid" then return Grid end
 if path=="scripts/settings/ui/ui_sound_events" then return {tab_button_pressed="native_tab_pressed"} end
 if path=="scripts/utilities/ui/text" then return {text_width=function(_,text) return #text*18 end} end
 if path=="scripts/ui/view_elements/view_element_input_legend/view_element_input_legend" then return Legend end
 return old_require(path)
end
function Managers.ui:get_input_alias_key(key) return key end
local old_init=BaseView.init
function BaseView:init(...)
 old_init(self,...);self._render_scale=1;self._ui_renderer={scale=1}
 self._elements={};self._elements_array={};self._element_to_pivot={}
end
function BaseView:update(dt,t,input)
 for _,e in ipairs(self._elements_array) do e:update(dt,t,input) end
end
function BaseView:on_exit()
 for _,e in ipairs(self._elements_array) do e:destroy() end
 self._elements_array={};self._elements={}
end
function input:null_service() return null_input end
null_input={get=function() return false end};function null_input:null_service() return self end
''')
    source=native('scripts/ui/views/base_view.lua')
    for name in ('_add_element','_remove_element'):
        body=re.search(r'^BaseView\.'+name+r' = function\b.*?^end$',source,re.M|re.S)
        assert body
        L.execute(body.group(0))
