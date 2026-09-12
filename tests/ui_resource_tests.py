"""Native button/widget definitions plus a model of the logged resource unload.

The model checks material ownership, not the proprietary renderer. The old
release must reproduce the secondary-material dependency; new buttons must
use only the host talent view's own terminal-button materials.
"""
from harness import *
import zipfile

L.execute('''
function table.append(a,b) for _,value in ipairs(b) do a[#a+1]=value end; return a end
Color=setmetatable({}, {__index=function() return function(alpha) return {alpha or 255,180,180,180} end end})
TestColors={color_copy=function(a,b) for i=1,4 do b[i]=a[i] end end,
    color_lerp=function(a,b,t,out) for i=1,4 do out[i]=a[i]+(b[i]-a[i])*t end end}
TestFonts={button_primary={font_size=24,text_color={255,255,255,255},default_color={255,180,180,180},
    hover_color={255,255,255,255},disabled_color={255,90,90,90}},body={font_size=20}}
''')
cache['scripts/utilities/ui/colors']=L.globals().TestColors
cache['scripts/managers/ui/ui_font_settings']=L.globals().TestFonts
for key in ('scripts/managers/input/input_utils','scripts/ui/pass_templates/list_header_templates',
            'scripts/managers/ui/ui_renderer','scripts/settings/ui/ui_sound_events',
            'scripts/utilities/ui/text','scripts/managers/ui/ui_resolution'):
    cache[key]=tbl({})

buttons=(GAME/'scripts/ui/pass_templates/button_pass_templates.lua').read_text(encoding='utf-8-sig')
def table_assignment(symbol):
    return symbol+' = '+buttons.split(symbol+' = ',1)[1].split('\n}',1)[0]+'\n}\n'
prelude=buttons.split('ButtonPassTemplates.terminal_list_button_background_change_function =',1)[0]
prelude+=table_assignment('local default_button_content')
prelude+='local default_button_small_text_style=table.clone(UIFontSettings.button_primary)\ndefault_button_small_text_style.font_size=20\n'
templates=L.execute(prelude+table_assignment('ButtonPassTemplates.default_button_small')+
    table_assignment('ButtonPassTemplates.terminal_button')+'\nreturn ButtonPassTemplates')
cache['scripts/ui/pass_templates/button_pass_templates']=templates
cache['scripts/ui/pass_templates/scrollbar_pass_templates']=lua_file(GAME/'scripts/ui/pass_templates/scrollbar_pass_templates.lua')
for name in ('default_pass_styles','default_pass_values'):
    cache['scripts/ui/'+name]=lua_file(GAME/('scripts/ui/'+name+'.lua'))

uiwidget=tbl({}); cache['scripts/managers/ui/ui_widget']=uiwidget
widget_source=(GAME/'scripts/managers/ui/ui_widget.lua').read_text(encoding='utf-8-sig')
for name in ('create_definition','add_definition_pass'):
    body=widget_source.split('UIWidget.'+name+' = function',1)[1].split('\nend',1)[0]
    uiwidget[name]=L.execute('''
local UIWidget=require("scripts/managers/ui/ui_widget")
local DefaultPassStyles=require("scripts/ui/default_pass_styles")
local DefaultPassValues=require("scripts/ui/default_pass_values")
return function'''+body+'\nend')
cache['scripts/ui/views/talent_builder_view/talent_builder_view']=tbl({})
L.globals().Buttons=templates
L.globals().Widget=uiwidget
L.globals().M=mod
L.execute('''
local material="content/ui/materials/buttons/secondary"
crash_material=material
talent_materials={}
for _,pass in ipairs(Buttons.terminal_button) do
    if pass.pass_type=="texture" then talent_materials[pass.value]=true end
end
assert(not talent_materials[material])
snapshot={selected_count=1,limit=32,entries={{buff_name="sample_buff",display_name="Sample",description="Description",
    source_kind="generic",valid=true,selected=true}},family="fire",archetype="zealot",abilities_ready=true,apply_to_self=true}
available=true; pending={}; loads={}; next_load=0; release_count=0
Managers.package={load=function(_,package,reference,callback)
    next_load=next_load+1; loads[next_load]=package; pending[next_load]=callback; return next_load
end,release=function(_,id) assert(loads[id]); loads[id]=nil; pending[id]=nil; release_count=release_count+1 end}
function complete_packages()
    local work=pending; pending={}
    for id,callback in pairs(work) do callback(id) end
end
function M.mortis_talent_ui_snapshot() return available and snapshot or nil end
function M.mortis_talent_ui_available() return available end
function M.mortis_talent_ui_editable() return available and snapshot.editable ~= false end
function M.set_mortis_family_from_talent_ui(_,family) snapshot.family=family; return true end
function M.clear_mortis_buffs_from_talent_ui() snapshot.selected_count=0; return true end
function M.toggle_mortis_buff_from_talent_ui() snapshot.selected_count=1; return true end
function new_view(definitions)
    local view={_widgets_by_name=table.clone_instance(definitions.widget_definitions),_is_own_player=true,_preview_player={}}
    view._widgets_by_name.summary_button={content={hotspot={}}}
    return view
end
function draw_buttons(view)
    local held={}
    for name,widget in pairs(view._widgets_by_name) do
        if widget.visible and (name=="tamm_mortis_button" or name=="tamm_mortis_clear" or name=="tamm_mortis_close"
            or name:match("^tamm_mortis_family_%d+$")) then
            local hotspot=widget.content.hotspot
            hotspot.anim_focus_progress=0; hotspot.anim_select_progress=0; hotspot.anim_hover_progress=0; hotspot.anim_input_progress=0
            for _,pass in ipairs(widget.passes) do
                if pass.change_function then pass.change_function(widget.content,widget.style[pass.style_id]) end
                if pass.pass_type=="texture" then
                    local content=pass.content_id and widget.content[pass.content_id] or widget.content
                    local value=content[pass.value_id]; held[value]=true
                end
            end
        end
    end
    return held
end
function unload_inventory(held)
    assert(not held[crash_material],"InventoryView0 unload: secondary material still held by TalentBuilderView_ui_renderer")
end
function assert_talent_owned(held)
    for name in pairs(held) do assert(talent_materials[name],"Button has a material absent from the native talent template: "..name) end
end
''')

relative='MortisBuffManager/scripts/mods/MortisBuffManager/modules/mortis_talent_ui.lua'
old_zip=PROJECT/'release/2.0.1/files/MortisBuffManager-2.0.1.zip'
with zipfile.ZipFile(old_zip) as archive:
    old_source=archive.read(relative).decode('utf-8-sig')

def load_ui(source):
    definitions=tbl({'overlay_scenegraph_definition':{},'widget_definitions':{}})
    cache['scripts/ui/views/talent_builder_view/talent_builder_view_definitions']=definitions
    L.execute(source)
    L.globals().Definitions=definitions
    return definitions

old_definitions=load_ui(old_source)
L.execute('''
local view=new_view(Definitions)
M.mortis_talent_ui_on_enter(view)
assert(not view._tamm_mortis_panel_open and view._widgets_by_name.tamm_mortis_button.visible)
assert(not pcall(unload_inventory,draw_buttons(view)),"Old entry button must reproduce the logged missing dependency, even with the panel closed")
M.mortis_talent_ui_on_exit(view)
''')


# New page uses its own BaseView and definitions. Keep the original native
# definition object to prove loading/enter/disable cannot inject an I-key popup.
native_definitions=tbl({'overlay_scenegraph_definition':{},'widget_definitions':{}})
cache['scripts/ui/views/talent_builder_view/talent_builder_view_definitions']=native_definitions
L.execute("""
BaseView={}
function BaseView:init(definitions,settings,context)
 self._definitions=definitions; self._widgets_by_name=table.clone_instance(definitions.widget_definitions)
 for _,w in pairs(self._widgets_by_name) do w.visible=true end
end
function BaseView:on_enter() end
function BaseView:on_exit() end
function BaseView:update() return self._pass_input,self._pass_draw end
function BaseView:can_exit() return true end
function class(name,parent)
 local c={super=_G[parent]};c.__index=c;setmetatable(c,{__index=c.super});_G[name]=c;return c
end
P={}; Managers.player={local_player_safe=function() return P end}
Managers.ui={close_view=function(_,name) closed=name end}
function new_private_view()
 local view=setmetatable({}, {__index=MBMWorkspaceMortisView})
 view:init({}, {player=P,parent={view_name="workspace"}})
 view:on_enter();return view
end
""")
cache['scripts/ui/views/base_view']=L.globals().BaseView
L.globals().MortisView=L.execute((SOURCES/relative).read_text(encoding='utf-8-sig'))
assert not list(native_definitions.widget_definitions.keys())
assert not list(native_definitions.overlay_scenegraph_definition.keys())
L.execute("""
available=true; snapshot.editable=true
for cycle=1,3 do
 view=new_private_view()
 local scene=view._definitions.scenegraph_definition
 local panel=scene.tamm_mortis_panel
 local top=scene.canvas.position[2]+(scene.canvas.size[2]-panel.size[2])/2
 assert(top>=220 and top+panel.size[2]<=1020,"Keep content below native tabs and above the Back legend")
 local footer_y=panel.size[2]-scene.tamm_mortis_clear.size[2]+scene.tamm_mortis_clear.position[2]
 for _,name in ipairs({"tamm_mortis_list","tamm_mortis_detail_panel"}) do
  local part=scene[name]
  assert(part.position[2]+part.size[2]<footer_y,"Content must not cover the footer")
 end
 local detail=scene.tamm_mortis_detail_panel
 for _,name in ipairs({"icon","title","state","description"}) do
  local part=scene["tamm_mortis_detail_"..name]
  assert(part.position[2]+part.size[2]<=detail.size[2],"Detail remains inside its panel")
 end
 assert(scene.tamm_mortis_row_10 and not scene.tamm_mortis_row_11,"Keep ten visible choices")
 assert(not view._widgets_by_name.tamm_mortis_button,"No duplicate Mortis button")
 assert(view._tamm_mortis_panel_open and view:can_exit())
 assert(next(loads)); complete_packages()
 local family=view._widgets_by_name.tamm_mortis_family_2
 family.content.hotspot.pressed_callback()
 local held=draw_buttons(view);unload_inventory(held);assert_talent_owned(held)
 assert(family.content.hotspot.is_selected and family.style.text.font_size==20)
 view._widgets_by_name.tamm_mortis_clear.content.hotspot.pressed_callback()
 assert(snapshot.selected_count==0)
 view._widgets_by_name.tamm_mortis_row_1.content.hotspot.pressed_callback()
 assert(snapshot.selected_count==1)
 local a,b=view:update(0.25,0,{})
 assert(a==true and b==true,"Top workspace header must receive input/draw")
 assert(not view._widgets_by_name.tamm_mortis_close and not view._widgets_by_name.tamm_mortis_panel and not view._widgets_by_name.tamm_mortis_dimmer,"One integrated page; the workspace owns its Back legend")
 view:on_exit();assert(next(loads)==nil)
end
snapshot.editable=false
assert(M.workspace_page.available(P),"Draft/competition retains catalog access; editing is guarded separately")
snapshot.editable=true
view=new_private_view()
snapshot.editable=false;view:update(0.25,0,{})
assert(view._widgets_by_name.tamm_mortis_clear.content.hotspot.disabled)
for i=1,7 do assert(view._widgets_by_name["tamm_mortis_family_"..i].content.hotspot.disabled) end
view:on_exit();snapshot.editable=true

-- Real DMF disable order: disabled state before cleanup, plus old callbacks
-- and asynchronous resources returning after the page has been closed.
view=new_private_view()
local stale=view._widgets_by_name.tamm_mortis_clear.content.hotspot.pressed_callback
local late=pending;local selected=snapshot.selected_count
M._enabled=false;M.cleanup_mortis_talent_ui()
assert(not view._tamm_mortis_panel_open and next(loads)==nil)
for _,w in pairs(view._widgets_by_name) do assert(w.visible==false and w.content.visible==false) end
stale(); assert(snapshot.selected_count==selected)
for id,callback in pairs(late) do callback(id) end
assert(next(loads)==nil)
view:on_exit()
local off=new_private_view();assert(not off._tamm_mortis_initialized and next(loads)==nil)
for _,w in pairs(off._widgets_by_name) do
 for _,pass in ipairs(w.passes) do assert(pass.visibility_function and not pass.visibility_function()) end
end
off:on_exit()
M._enabled=true;view=new_private_view();complete_packages()
assert(view._tamm_mortis_panel_open);view:on_exit();assert(next(loads)==nil)
""")
assert not list(native_definitions.widget_definitions.keys())
graph=L.globals().view._definitions.scenegraph_definition
assert graph.screen.scale=='fit'
assert graph.tamm_mortis_panel.size[1] ==1920-192
assert graph.tamm_mortis_panel.size[2]<=1004
assert graph.tamm_mortis_detail_description.position[2]+graph.tamm_mortis_detail_description.size[2]<=graph.tamm_mortis_detail_panel.size[2]
assert templates.terminal_button[7].style.font_size==24
source=(SOURCES/relative).read_text(encoding='utf-8-sig')
assert 'mod:hook(' not in source and 'mod:hook_safe(' not in source
assert 'require("scripts/ui/views/talent_builder_view/' not in source
print('Old resource crash reproduced; independent Mortis page, native definitions untouched, native materials, header input/draw, callbacks, mode lock, close/reopen, disabled startup, stale callbacks and late resource cleanup: PASS')
