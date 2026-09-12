"""Native Realms widgets: independent DIY limits, typed edits and stale-input guards."""
from ui_native_env import *
L.globals().M=mod
L.globals().Controls=load_mod('MortisBuffManager/scripts/mods/MortisBuffManager/modules/mortis_realms_controls')
L.execute(r'''
active=true;connection={};rules={enabled=true,native_enabled=false,diy_enabled=true,diy_limits={max_total=6},limit=8,mode='preselect',revision=1}
M.mortis_realms_controls_active=function()return active end
M.mortis_global_rules_snapshot=function()return active and rules or nil,connection end
function M.set_mortis_global_rules(mode,limit,native,c)
 assert(c==connection and not rules.locked);rules.mode=mode;rules.limit=mode=='draft' and 10 or limit;rules.native_enabled=native
 rules.enabled=native or rules.diy_enabled;rules.revision=rules.revision+1;return true
end
function M.set_mortis_diy_rules(limit,enabled,c)
 assert(c==connection and not rules.locked and limit>=0 and limit<=99 and limit%1==0)
 rules.diy_limits.max_total=limit;rules.diy_enabled=enabled;rules.enabled=rules.native_enabled or enabled;rules.revision=rules.revision+1;return true
end
values={};strokes={};input={get=function(_,k)return values[k]end,is_null_service=function()return false end}
Keyboard={BACKSPACE=8,DELETE=127,ENTER=13,ESCAPE=27,keystrokes=function()local s=strokes;strokes={};return s end}
Clipboard={get=function()return clipboard end}
grid={_mbm_realms_view={_mbm_input=input}}
blueprint=Controls.blueprint(1262)
widget=UIWidget.init('rules',UIWidget.create_definition(blueprint.pass_template,'row'))
for k,v in pairs(widget.content)do if type(v)=='table' and k:find('hotspot')then v.parent=widget.content end end
blueprint.init(grid,widget,{widget_type='mbm_global_rules'})
function tick(v,s,dt)values=v or {};strokes=s or {};Controls.update(grid,widget,input,dt or .016)end
function press(name)widget.content['mbm_'..name..'_hotspot'].on_pressed=true;tick()end
press('points');tick({}, {'1','2',Keyboard.ENTER});assert(rules.limit==12 and not rules.native_enabled,'Editing the native limit cannot enable a disabled source')
press('diy_plus');assert(rules.diy_limits.max_total==7 and rules.limit==12)
press('diy_minus');widget.content.mbm_diy_minus_hotspot.is_held=true;tick(nil,nil,.39);tick(nil,nil,.02);tick(nil,nil,.08)
assert(rules.diy_limits.max_total==4 and rules.limit==12);widget.content.mbm_diy_minus_hotspot.is_held=false
press('diy_points');clipboard='0';tick({clipboard_paste=true});tick({left_pressed=true});assert(rules.diy_limits.max_total==0)
press('diy_points');tick({}, {'2','0',Keyboard.ESCAPE});assert(rules.diy_limits.max_total==0)
press('diy_points');clipboard='999';tick({clipboard_paste=true});tick({confirm_pressed=true});assert(rules.diy_limits.max_total==99)
press('diy_plus');assert(rules.diy_limits.max_total==99)
press('diy_points');tick({}, {'1','1'});rules.revision=rules.revision+1;tick({confirm_pressed=true});assert(not grid._mbm_edit and rules.diy_limits.max_total==99)
press('diy_points');tick({}, {'1','1'});connection={};tick({confirm_pressed=true});assert(not grid._mbm_edit and rules.diy_limits.max_total==99)
press('draft');press('diy_points');tick({}, {'1','7',Keyboard.ENTER});assert(rules.limit==10 and rules.diy_limits.max_total==17,'Fixed progress rounds do not lock the independent DIY allowance')
for _,key in ipairs({'points','minus','plus'})do assert(widget.content['mbm_'..key..'_hotspot'].disabled)end
press('diy_enable');assert(not rules.diy_enabled and not rules.native_enabled and not rules.enabled)
press('diy_enable');assert(rules.diy_enabled and not rules.native_enabled)
press('diy_points');tick({}, {'3'});rules.locked=true;tick({confirm_pressed=true});assert(not grid._mbm_edit and rules.diy_limits.max_total==17)
local revision=rules.revision;press('diy_plus');press('diy_enable');assert(rules.revision==revision)
for _,key in ipairs({'enable','minus','points','plus','diy_enable','diy_minus','diy_points','diy_plus','preselect','draft','competition'})do assert(widget.content['mbm_'..key..'_hotspot'].disabled)end
rules.locked=false
for _,pass in ipairs(blueprint.pass_template)do assert(pass.pass_type~='slider','No slider control is used')end
assert(blueprint.size[2]==156)
''')
layouts={}
for lang in ('en','zh-cn','zh-tw'):
 L.globals().test_language=lang
 for mode in ('preselect','draft','competition'):
  L.globals().test_mode=mode
  L.execute("rules.mode=test_mode;rules.limit=test_mode=='draft' and 10 or 99;rules.diy_limits.max_total=99;tick()")
  widget=L.globals().widget
  items=[dict(key='heading',x=310,y=144,w=1290,h=55,text={'en':'Realms · Mortis settings','zh-cn':'Realms · 死灵天赋设置','zh-tw':'Realms · 死靈天賦設定'}[lang],font=30)]
  for _,p in L.globals().blueprint.pass_template.items():
   if p.pass_type!='text':continue
   s=widget.style[p.style_id];o=s.offset;size=s.size
   button=widget.content[p.value_id+'_hotspot'] is not None
   assert o[1]>=0 and o[2]>=0 and o[1]+size[1]<=1262 and o[2]+size[2]<=156
   items.append(dict(key=p.value_id,x=310+o[1],y=230+o[2],w=size[1],h=size[2],text=widget.content[p.value_id],font=s.font_size,center=button,fill=button,text_padding=2))
  layouts[lang+'_realms-reward-'+mode]=items
dev=PROJECT.parents[1]/'development/diy-framework'
(dev/'qa/reward-controls-layouts.json').write_text(json.dumps(layouts,ensure_ascii=False,indent=2),encoding='utf-8')
print('Realms DIY controls: separate limits/source switches, zero/max, typing/paste/Enter/click-away/Esc, hold repeat, stale room/revision rejection, fixed-progress independence, mission lock and three-language native geometry PASS')
