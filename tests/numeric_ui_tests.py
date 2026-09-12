"""Native DMF decimal commit paths plus this mod's scoped numeric affordance."""
from harness import *
L.globals().M=mod
cache['scripts/managers/ui/ui_renderer']=tbl({})
L.execute('''
local dmf=new_test_mod("DMF")
dmf.io_dofile=function() return {clear_selection=function() end,update_validation_style=function() end} end
Utf8={string_length=string.len}
''')
native=lua_file(FIXTURES/'mods/dmf/scripts/mods/dmf/modules/ui/options/numeric/numeric_input.lua')
L.globals().Native=native
L.globals().Numeric=load_mod('MortisBuffManager/scripts/mods/MortisBuffManager/modules/mortis_numeric_ui')
L.execute('''
local value,calls=.25,0
local entry={setting_id="mortis_kill_horde",num_decimals=2,min_value=0,max_value=100,default_value=.25,
 get_function=function() return value end,on_activated=function(v) value=v;calls=calls+1 end,changed_callback=function() end}
local function hidden(c) return c.is_writing end
local function widget()
 local w={content={entry=entry,input_hotspot={}},style={},passes={
  {style_id="background",visibility_function=hidden},
  {style_id="baseline",visibility_function=hidden},{style_id="display_text",visibility_function=hidden}}}
 Native.init(w,entry);return w
end
local w=widget();Numeric.decorate(w,entry)
assert(w.passes[1].visibility_function(w.content))
assert(not w.passes[3].visibility_function(w.content),"Caret/text must not overlay idle value")
M._enabled=false;assert(not w.passes[1].visibility_function(w.content));M._enabled=true
local other=widget();Numeric.decorate(other,{setting_id="other_mod_setting"});assert(not other._mbm_numeric)
local view={_selected_settings_widget=w}
local input={get=function(_,name) return name=="confirm_pressed" end}
w.content.is_writing=true;w.content.input_text="2.75"
Native.update(view,w,entry,input,false,false);assert(value==2.75 and calls==1 and not w.content.is_writing)
input.get=function(_,name) return name=="left_pressed" end
w.content.is_writing=true;w.content.input_text="0.25";w.content.input_hotspot.is_hover=false
Native.update(view,w,entry,input,false,false);assert(value==.25 and calls==2)
input.get=function(_,name) return name=="back" end
w.content.is_writing=true;w.content.input_text="90.00"
Numeric.cancel(view,input);Native.update(view,w,entry,input,false,false);assert(value==.25 and calls==2)
input.get=function(_,name) return name=="confirm_pressed" end
for _,bad in ipairs({"0.001","100.01","-1","nan","1e2","invalid"}) do
 w.content.is_writing=true;w.content.input_text=bad
 Native.update(view,w,entry,input,false,false);assert(value==.25 and calls==2,bad)
end
w.content.is_writing=false;w.content.numeric_input_was_writing=true;w.content.input_text="5.50"
Native.update(view,w,entry,input,false,false);assert(value==5.5 and calls==3,"Click-away state transition")
''')
print('Native DMF: two-decimal input, confirm/click-away, Esc cancel, invalid values and other-mod/disabled widget isolation PASS')
L.execute('''
local value,calls=32,0
local entry={setting_id="mortis_buff_limit",num_decimals=0,min_value=0,max_value=99,default_value=10,
 get_function=function() return value end,on_activated=function(v) value=v;calls=calls+1 end,changed_callback=function() end}
M._settings.mortis_mode="preselect";Numeric.configure(entry)
local w={content={entry=entry,input_hotspot={},hotspot={}},style={},passes={}}
Native.init(w,entry);Numeric.decorate(w,entry)
local view={};Numeric.sync_limit(view,w)
entry.on_activated(48);assert(value==48 and entry.max_value==99 and not entry.disabled)
local input={get=function(_,name) return name=="confirm_pressed" end}
w.content.is_writing=true;w.content.numeric_input_was_writing=true;w.content.input_text="63"
view._selected_settings_widget=w;view.is_text_input_focused=true
w.content.drag_active=true;w.content.drag_previously_active=true
M._settings.mortis_mode="draft";Numeric.sync_limit(view,w)
assert(entry.disabled and w.content.disabled and w.content.input_hotspot.disabled)
assert(entry.get_function(entry)==10 and entry.max_value==10 and w.content.input_text=="10")
assert(not w.content.is_writing and not w.content.numeric_input_was_writing and not w.content.drag_active and not w.content.drag_previously_active)
assert(not view._selected_settings_widget and not view.is_text_input_focused)
Native.update(view,w,entry,input,false,entry.disabled)
entry.on_activated(0);assert(value==48 and calls==1,"Neither a stale slider callback nor a typed value changes fixed progress rules")
M._settings.mortis_mode="competition";Numeric.sync_limit(view,w)
assert(not entry.disabled and entry.max_value==99 and entry.get_function(entry)==48)
assert(w.content.text==M:localize("mortis_limit_competition"))
w.content.is_writing=true;w.content.input_text="7";Native.update(view,w,entry,input,false,entry.disabled)
assert(value==7 and calls==2)
M._settings.mortis_mode="preselect";Numeric.sync_limit(view,w);assert(entry.get_function(entry)==7 and entry.max_value==99)
''')
print('DMF mode controls: 0–99 slider/direct entry, fixed grey 10, typed/drag cancellation, mode labels and editable value preservation PASS')
