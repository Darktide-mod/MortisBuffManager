from ui_native_env import *
L.globals().M=mod
L.globals().Controls=load_mod('MortisBuffManager/scripts/mods/MortisBuffManager/modules/mortis_realms_controls')
L.globals().HUD=load_mod('MortisBuffManager/scripts/mods/MortisBuffManager/modules/mortis_draft_hud')
L.execute('''
local active=true; local connection={}; local rules={enabled=true,limit=8,mode="preselect",revision=1}
function M.mortis_realms_controls_active() return active end
function M.mortis_global_rules_snapshot() return active and rules or nil,connection end
function M.set_mortis_global_rules(mode,points,enabled,c)
 assert(c==connection); rules={mode=mode,limit=mode=="draft" and 10 or points,enabled=enabled,revision=rules.revision+1};return true
end
values={};strokes={};input={get=function(_,k) return values[k] end,is_null_service=function() return false end}
Keyboard={BACKSPACE=8,DELETE=127,ENTER=13,ESCAPE=27,keystrokes=function() local s=strokes;strokes={};return s end}
Clipboard={get=function() return clipboard end}
local grid={_mbm_realms_view={_mbm_input=input}}
local blueprint=Controls.blueprint(1262)
local widget=UIWidget.init("rules",UIWidget.create_definition(blueprint.pass_template,"row"))
for k,v in pairs(widget.content) do if type(v)=="table" and k:find("hotspot") then v.parent=widget.content end end
blueprint.init(grid,widget,{widget_type="mbm_global_rules"})
local function tick(v,s,dt) values=v or {};strokes=s or {};Controls.update(grid,widget,input,dt or 0.016) end
local function press(name) widget.content["mbm_"..name.."_hotspot"].on_pressed=true;tick() end
press("points");clipboard="0";tick({clipboard_paste=true});tick({left_pressed=true});assert(rules.limit==0)
press("points");tick({}, {"3","2"});tick({back=true});assert(rules.limit==0)
press("points");clipboard="999";tick({clipboard_paste=true});tick({confirm_pressed=true});assert(rules.limit==99)
press("minus");local h=widget.content.mbm_minus_hotspot;h.is_held=true;tick(nil,nil,0.39);assert(rules.limit==98)
tick(nil,nil,0.02);tick(nil,nil,0.08);assert(rules.limit==96);h.is_held=false
press("competition");assert(rules.mode=="competition")
press("draft");tick();assert(rules.limit==10)
local revision=rules.revision
press("points");press("minus");press("plus")
widget.content.mbm_plus_hotspot.is_held=true;tick(nil,nil,1)
assert(not grid._mbm_edit and rules.revision==revision and rules.limit==10)
for _,name in ipairs({"points","minus","plus"}) do assert(widget.content["mbm_"..name.."_hotspot"].disabled) end
widget.content.mbm_plus_hotspot.is_held=false
press("competition");tick();assert(not widget.content.mbm_points_hotspot.disabled)
press("points");clipboard="20";tick({clipboard_paste=true});tick({confirm_pressed=true});assert(rules.limit==20)
press("points");tick({}, {"6","0"});rules.mode="draft";rules.limit=10;rules.revision=rules.revision+1;tick({confirm_pressed=true})
assert(not grid._mbm_edit and rules.limit==10,"Stale edit cannot change progress quota")
press("enable");assert(not rules.enabled)
active=false;tick();assert(not widget.content.mbm_visible)
-- A single global row coexists with unrelated player and Talent rows.
active=true;local base={player={size={1262,80}}};local layout={{widget_type="player",peer_id="host"},{widget_type="tpm_player_rules"},{widget_type="player",peer_id="guest"}}
local decorated,own=Controls.wrap_layout(grid,layout,base)
assert(#decorated==6 and decorated[1].widget_type=="mbm_global_rules" and decorated[4].widget_type=="tpm_player_rules")
assert(not base.mbm_global_rules and own~=base)
active=false;assert(Controls.wrap_layout(grid,layout,base)==layout)
''')
print('Native widgets: global-only Realms row, Talent-row coexistence, 0 points, typing/paste/click-away/Esc, hold repeat and host-only visibility: PASS')
L.execute('''
P={};Managers.player={local_player_safe=function() return P end}
Managers.world={is_world_enabled=function() return true end}; Managers.package={has_loaded=function() return true end}
using_input=false;Managers.ui={using_input=function() return using_input end}
RESOLUTION_LOOKUP={scale=1,inverse_scale=1}
snapshot={mode="draft",active={id="one",choices={"a","b","c"},remaining=60},spent=0,earned=3,queued=2,limit=8,progress=0}
function M.mortis_draft_snapshot() return snapshot,0,false end
function M.mortis_choice_ui_data(name) return {display_name=name,description="Native description",icon="icon"} end
chosen={};function M.choose_mortis_draft(i) chosen[#chosen+1]=i;return true end
ctrl=false;key=nil;Keyboard.button_index=function(k) return k end
Keyboard.button=function(k) return ctrl and k=="left ctrl" and 1 or 0 end
Keyboard.pressed=function(k) return k==key end
input={is_null_service=function() return false end}
local seen={};UIWidget.draw=function(w) seen[w.name]=w end
UIRenderer.begin_pass=function(_,_,received) assert(received==input,"HUD must preserve input identity") end
UIRenderer.end_pass=function() end
local function hook(name) for _,h in ipairs(hooks) do if h.target==UIHud and h.name==name then return h.fn end end;error(name) end
local hud={_player=P,_world_name="world",_ui_renderer={}}
hook("update")(hud,0.4,1,input);hook("draw")(hud,0.1,1,input)
assert(seen.mbm_draft_card_1 and seen.mbm_draft_card_3)
local function input_tick()
 for _,h in ipairs(hooks) do if h.target==InputManager and h.name=="_update_services" then h.fn({},0.016) end end
end
key="2";input_tick();hook("update")(hud,0.016,1,input);assert(#chosen==0)
key=nil;input_tick()
key="2";ctrl=true;input_tick();hook("update")(hud,0.016,1,input);assert(chosen[1]==2)
using_input=true;hook("update")(hud,0.1,1,input);assert(#chosen==1,"Typing in another UI must not choose")
using_input=false;key=nil
snapshot.last={id="one",index=2};snapshot.active={id="two",choices={"d","e","f"},remaining=60};snapshot.spent=1
hook("update")(hud,0.1,1,input);hook("draw")(hud,0.1,1,input)
assert(seen.mbm_draft_card_2.content.key==M:localize("mortis_draft_chosen"))
hook("update")(hud,0.8,1,input);hook("draw")(hud,0.1,1,input)
assert(seen.mbm_draft_card_1.content.title=="d")
snapshot.mode="competition";snapshot.progress=57.75;M._settings.mortis_competition_hud_style="bar_percent"
hook("update")(hud,.1,1,input);seen={};hook("draw")(hud,.1,1,input)
assert(seen.mbm_draft_progress and seen.mbm_draft_card_1,"Progress stays visible during a draft")
assert(seen.mbm_draft_progress.content.bar)
assert(math.abs(seen.mbm_draft_progress.style.fill.size[1]-196*.5775)<.001)
assert(seen.mbm_draft_progress.content.text=="57.75%")
M._settings.mortis_competition_hud_style="bar";hook("update")(hud,.1,1,input);hook("draw")(hud,.1,1,input)
assert(seen.mbm_draft_progress.content.bar and seen.mbm_draft_progress.content.text=="")
M._settings.mortis_competition_hud_style="hidden";hook("update")(hud,.1,1,input);seen={};hook("draw")(hud,.1,1,input)
assert(not seen.mbm_draft_progress and seen.mbm_draft_card_1,"Hidden indicator must not hide choices")
M._settings.mortis_competition_hud_style="percent";snapshot.active=nil
hook("update")(hud,.8,1,input);seen={};hook("draw")(hud,.1,1,input)
assert(seen.mbm_draft_progress and not seen.mbm_draft_progress.content.bar)
assert(seen.mbm_draft_progress.content.text:find("57.75",1,true))
snapshot.mode="draft";hook("update")(hud,.8,1,input);seen={};hook("draw")(hud,.1,1,input)
assert(not seen.mbm_draft_progress,"Other modes have no competition indicator")
M._enabled=false;seen={};hook("draw")(hud,0.1,1,input);assert(next(seen)==nil)

HUD.cleanup();M._enabled=true
-- Native descriptions are never truncated, including long localized effects.
local long_description=string.rep("Complete effect with numbers and conditions. ",12)
local measured=0
UIRenderer.styled_text_size=function(_,text,style)
 measured=measured+1;return 280,text==long_description and 170 or 40
end
function M.mortis_choice_ui_data(name) return {display_name=name,description=long_description,subtitle="Native rank",icon="icon"} end
snapshot={epoch="awards",version=1,mode="competition",counting=false,completed=0,rewards={},
 active={id="route",kind="family",choices={"a","b"},remaining=60},spent=0,earned=2,queued=1,limit=3,progress=0}
hook("update")(hud,.4,1,input);seen={};hook("draw")(hud,.1,1,input)
assert(not seen.mbm_draft_progress and seen.mbm_draft_card_1 and seen.mbm_draft_card_2 and not seen.mbm_draft_card_3)
assert(seen.mbm_draft_card_1.content.description==long_description and seen.mbm_draft_card_1.style.description.size[2]>=170)
assert(seen.mbm_draft_card_1.content.subtitle=="Native rank")
local card=seen.mbm_draft_card_1
local width=HUD.geometry.card_width
for _,id in ipairs({"title","subtitle","description","key"}) do
 local style=card.style[id]
 assert(style.offset[1]>=20 and style.offset[1]+style.size[1]<=width-20,"Text must clear both card edges")
end
assert(card.style.title.offset[2]>=18)
assert(card.style.subtitle.offset[2]>=card.style.title.offset[2]+card.style.title.size[2]+2)
assert(card.style.description.offset[2]>=card.style.subtitle.offset[2]+card.style.subtitle.size[2]+10)
assert(card.style.key.offset[2]>=card.style.description.offset[2]+card.style.description.size[2]+12,"Long effects must clear the footer")
assert(card.style.frame_top.material_values.texture_map=="content/ui/textures/frames/horde/horde_buff_boon_selected")
assert(card.style.frame_bottom.material_values.texture_map=="content/ui/textures/frames/horde/horde_buff_bottom")
local count=measured;hook("update")(hud,.1,1,input);assert(measured==count,"Unchanged cards do not remeasure their strings")
snapshot={epoch="awards",version=2,mode="competition",counting=false,completed=1,
 rewards={{id=1,name="automatic_route",round=1}},last={id="route",index=2},spent=1,earned=2,queued=0,limit=3,progress=0}
hook("update")(hud,.1,1,input);seen={};hook("draw")(hud,.1,1,input)
assert(seen.mbm_draft_card_2.style.flash.color[1]>0 and seen.mbm_draft_card_1.alpha_multiplier<seen.mbm_draft_card_2.alpha_multiplier)
hook("update")(hud,.8,1,input);seen={};hook("draw")(hud,.1,1,input)
assert(seen.mbm_draft_card_1 and seen.mbm_draft_card_1.content.title=="automatic_route")
assert(seen.mbm_draft_card_1.content.description==long_description)
assert(seen.mbm_draft_card_1.alpha_multiplier==0,"Automatic notices fade in from zero")
using_input=true;hook("update")(hud,4,1,input);using_input=false
hook("draw")(hud,.1,1,input)
assert(seen.mbm_draft_card_1.alpha_multiplier==0,"Other menus pause the award animation and its lifetime together")
hook("update")(hud,.125,1,input);hook("draw")(hud,.1,1,input)
assert(math.abs(seen.mbm_draft_card_1.alpha_multiplier-.5)<.001)
hook("update")(hud,.125,1,input);hook("draw")(hud,.1,1,input)
assert(seen.mbm_draft_card_1.alpha_multiplier==1)
snapshot=table.clone_instance(snapshot);snapshot.version=3;snapshot.completed=2
snapshot.rewards[2]={id=3,name="last_remaining",round=2}
hook("update")(hud,3,1,input);hook("draw")(hud,.1,1,input)
assert(seen.mbm_draft_card_1.alpha_multiplier>.999,"Automatic notice stays fully visible for three seconds after fade-in")
hook("update")(hud,.09,1,input);hook("draw")(hud,.1,1,input)
assert(math.abs(seen.mbm_draft_card_1.alpha_multiplier-.5)<.001,"Automatic notice fades out over the final 180 ms")
hook("update")(hud,.08,1,input);seen={};hook("draw")(hud,.1,1,input)
assert(seen.mbm_draft_card_1.content.title=="automatic_route","Award stays visible through the exit fade")
assert(seen.mbm_draft_card_1.alpha_multiplier>0 and seen.mbm_draft_card_1.alpha_multiplier<.06)
assert(seen.mbm_draft_header.alpha_multiplier==seen.mbm_draft_card_1.alpha_multiplier)
hook("update")(hud,.02,1,input);seen={};hook("draw")(hud,.1,1,input)
assert(seen.mbm_draft_card_1.content.title=="last_remaining","One remaining auto-granted Buff has its own full-effect notice")
assert(seen.mbm_draft_card_1.alpha_multiplier==0,"Queued notices start their own fade-in")
snapshot=table.clone_instance(snapshot);hook("update")(hud,3.42,1,input);seen={};hook("draw")(hud,.1,1,input)
assert(seen.mbm_draft_card_1.content.title=="last_remaining")
assert(seen.mbm_draft_card_1.style.icon.material_values.frame=="content/ui/textures/frames/horde/hex_frame_horde")
hook("update")(hud,.02,1,input)
local passes,reads=0,0
UIRenderer.begin_pass=function() passes=passes+1 end
function M.mortis_draft_snapshot() reads=reads+1;return snapshot,0,false end
for i=1,600 do hook("update")(hud,1/60,i,input);hook("draw")(hud,1/60,i,input) end
assert(passes==0 and reads==600,"Finished HUD renders no empty pass, requests no second snapshot and never replays awards")
HUD.cleanup()

''')
print('Native HUD definitions and live callbacks: three choices, Ctrl-only selection, unchanged input service, other-view input guard, selection animation/next card and disable cleanup: PASS')
# No input or cursor ownership is part of the draw module at all.
hud_source=(SOURCES/'MortisBuffManager/scripts/mods/MortisBuffManager/modules/mortis_draft_hud.lua').read_text(encoding='utf-8')
for forbidden in ('set_input_blocked','_activate_mouse_cursor','push_cursor',':null_service()', 'change_state('):
    assert forbidden not in hud_source,forbidden
# Native Tab uses actual buff extension entries even outside Survival.
tab=native('scripts/ui/hud/elements/tactical_overlay/hud_element_tactical_overlay.lua')
L.execute('''
HudElementTacticalOverlay={}; HordeBuffsData={a={title="Buff A",is_family_buff=true,icon="a"},b={title="Buff B",icon="b"}}
MissionBuffsParser={get_formated_buff_description=function() return "Description" end}
local buffs={}
function set_live_buffs(names)
 buffs={};for _,name in ipairs(names) do
  local n=name
  buffs[#buffs+1]={is_negative=function() return false end,template=function() return {buff_category="hordes_buff"} end,
   get_hud_data=function() return {title=n,show=true} end,has_hud=function() return true end}
 end
end
Managers.player={local_player=function() return {profile=function() return {} end} end}
Tab={_parent={player_extensions=function() return {buff={buffs=function() return buffs end}} end},_add_class_buffs_data=function() end,_add_items_buffs_data=function() end}
'''+method(tab,'HudElementTacticalOverlay','_add_player_buffs')+'''
set_live_buffs({"a","b"})
local rows=HudElementTacticalOverlay._add_player_buffs(Tab)
assert(#rows==2 and rows[1].category=="horde" and rows[1].sub_category=="hordes_minor_buff" and rows[2].sub_category=="hordes_major_buff")
set_live_buffs({"b"});rows=HudElementTacticalOverlay._add_player_buffs(Tab);assert(#rows==1 and rows[1].title=="Buff B")
set_live_buffs({});assert(#HudElementTacticalOverlay._add_player_buffs(Tab)==0)
''')
print('Actual native Tab collector: acquired native Buffs appear in Mortis categories, removed Buffs disappear, no candidate/queue entries: PASS')
