"""Production unified page and native widget definitions; model boundary fixtures."""
from ui_native_env import *
DEV=PROJECT.parents[1]/'development/diy-framework'
for name,stem in [('S','diy_schema'),('E','diy_examples')]:L.globals()[name]=load_mod('MortisBuffManager/scripts/mods/MortisBuffManager/modules/diy/'+stem)
L.globals().ProductionModel=load_mod('MortisBuffManager/scripts/mods/MortisBuffManager/modules/mortis_workspace_model')
L.execute(r'''
M=get_mod('MortisBuffManager');M._enabled=true
M.diy_library={status_message=function()return "Loaded 1 / 1 packages · 16 entries · 0 errors",false end,package_disabled=function()return false end,revision=0,document=E.mortis,options={max_total=6,tier_limits={3,2,1,1}},files={},selected_file=1,
 scan=function()end,copy_directory=function()end,export=function()end}
M.mortis_talent_ui_available=function()return true end
M.mortis_request_assets=function()end
M.mortis_family_names={'fire','unkillable','cowboy','electric','elementalist','critical','unstoppable'}
M.mortis_choice_ui_data=function(name)return {display_name=M:localize('mortis_talent_ui_family_'..name),description='Native family description'}end
function fixture(mode,editable)
 M._enabled=true;selection_calls=0;rules_calls=0;family_removed=0
 local rules={mode=mode,limit=mode=='draft' and 10 or 6,native_enabled=true,diy_enabled=true,locked=not editable,
  diy_limits={max_total=6,tier_limits={3,2,1,1}}}
 snapshot={rules=rules,rows={},editable=editable,selection_editable=editable and mode=='preselect',can_import=editable,
  preselect=mode=='preselect',native_count=2,diy_count=1,limit=6,family='fire'}
 local lang=M:localize('diy_language')
 for _,entry in ipairs(E.mortis.entries)do snapshot.rows[#snapshot.rows+1]={id=entry.id,key='diy/'..entry.id,policy_key=E.mortis.id..'/'..entry.id,source='diy',
  name=S.localize(entry.name,lang),description=S.localize(entry.description,lang),weight=entry.weight,tier=entry.tier,
  allowed=true,available=true,in_build_catalog=true,category='diy',missing={},selected=entry.id=='fivefold_salvo'}end
 snapshot.rows[#snapshot.rows+1]={id='native',key='native/native',source='native',name=lang=='en' and 'Native talent' or lang=='zh-tw' and '原生天賦' or '原生天赋',available=true,in_build_catalog=true,category='generic',missing={},selected=true}
 for i,category in ipairs({'class','family','family','class','generic'})do
  local current=i<4
  snapshot.rows[#snapshot.rows+1]={id='native_'..i,key='native/native_'..i,source='native',name=(lang=='en' and 'Native ' or lang=='zh-tw' and '原生 ' or '原生 ')..i,
   category=category,families=category=='family' and {i==2 and 'fire' or 'electric'} or nil,in_build_catalog=current,available=current,missing={},selected=false}
 end
 return snapshot
end
function row_by_key(key)for _,row in ipairs(snapshot.rows)do if row.key==key then return row end end end
function selected_count()local n=0;for _,row in ipairs(snapshot.rows)do if row.selected then n=n+1 end end;return n end
Model={browse=ProductionModel.browse,family=function(name)
 if name==snapshot.family then return false,'unchanged',0 end
 snapshot.family=name;return true,nil,family_removed
end,snapshot=function()
 snapshot.native_count=0;snapshot.diy_count=0
 for _,row in ipairs(snapshot.rows)do if row.selected and row.available then snapshot[row.source..'_count']=snapshot[row.source..'_count']+1 end end
 return snapshot
end,description=function(row)return row.description or 'Native description'end,
 select=function(row)
  selection_calls=selection_calls+1
  local current=row_by_key(row.key)
  if not snapshot.selection_editable or snapshot.rules.locked or not current then return false end
  if (row.selected==true)~=(current.selected==true)then return true end
  if not current.selected and not current.available then return false end
  current.selected=not current.selected;return true
 end,
 toggle_host=function(row)
  if not snapshot.editable or snapshot.rules.locked then return false end
  local current=row_by_key(row.key);if not current then return false end
  assert(current.source=='diy');current.host_banned=not current.host_banned;current.available=not current.host_banned;return true
 end,
 rules=function(mode,limit,native,diy)
  rules_calls=rules_calls+1
  if not snapshot.editable or snapshot.rules.locked then return false end
  snapshot.rules.mode=mode;snapshot.rules.limit=limit;snapshot.rules.native_enabled=native;snapshot.rules.diy_enabled=diy;return true
 end,
 batch=function(keys,target,add)
  local changed,skipped=0,0
  for _,row in ipairs(snapshot.rows)do if keys[row.key] then
   if target=='pool' then
    if snapshot.editable and not snapshot.rules.locked and row.source=='diy' then
     if row.host_banned==add or not add and row.host_banned==nil then
      row.host_banned=not add;row.available=add;changed=changed+1
     end
    else skipped=skipped+1 end
   elseif (row.selected==true)~=add then
    if Model.select(row)then changed=changed+1 else skipped=skipped+1 end
   end
  end end
  return changed,skipped
 end}
local original=M.io_dofile
function M:io_dofile(path)if path:match('mortis_workspace_model$')then return Model end;return original(self,path)end
function click(key)
 for _,item in ipairs(view._diy_items)do if item.key==key then assert(item.action,key);item.action();view:update(.3,0,{});return end end;error(key)
end
function item(key)for _,v in ipairs(view._diy_items)do if v.key==key then return v end end end
function new_view(mode,editable)
 fixture(mode or 'preselect',editable~=false)
 view=setmetatable({}, {__index=MBMWorkspaceMortisCatalogView});view:init({},{});view:on_enter();return view
end
function hover(key)
 for _,v in ipairs(view._diy_items)do if v.widget.content.hotspot then v.widget.content.hotspot.is_hover=false end end
 local hovered=assert(item(key),key);assert(hovered.on_hover,key);hovered.widget.content.hotspot.is_hover=true
 view:update(.3,0,{})
 for _,v in ipairs(view._diy_items)do if v.widget.content.hotspot then v.widget.content.hotspot.is_hover=false end end
end
-- Run the game's actual scrollbar logic passes. Only rendering allocation and
-- input devices are replaced; no test implementation decides the scroll value.
local Resolution=require('scripts/managers/ui/ui_resolution')
Resolution.inverse_scale_vector=function(v,scale)return {v[1]*scale,v[2]*scale,v[3] and v[3]*scale}end
function math.point_is_inside_2d_box(point,position,size)
 return point[1]>=position[1] and point[1]<=position[1]+size[1] and point[2]>=position[2] and point[2]<=position[2]+size[2]
end
Managers.ui={using_cursor_navigation=function()return true end}
function scrollbar_frame(options)
 options=options or {}
 local widget=assert(view._widgets_by_name[options.widget or 'catalog_scrollbar'])
 local content=widget.content
 local input={get=function(_,key)
  if key=='cursor'then return options.cursor or {200,600,0}
  elseif key=='scroll_axis'then return {0,options.wheel or 0,0}
  elseif key=='left_hold'then return options.hold==true end
 end}
 local renderer={input_service=input,dt=options.dt or 1/60,inverse_scale=options.inverse_scale or 1}
 local passes=0
 for _,pass in ipairs(widget.passes)do if pass.pass_type=='logic'then
  local style=pass.style_id and widget.style[pass.style_id] or widget.style
  style.parent=widget.style
  local scene=assert(view._ui_scenegraph[style.scenegraph_id or pass.scenegraph_id or widget.scenegraph_id])
  local position={scene.position[1],scene.position[2],0};local size=scene.size
  if not pass.visibility_function or pass.visibility_function(content,style)then
   assert(type(content[pass.value_id])=='function','Execute the function held by a real native widget pass')
   content[pass.value_id](pass,renderer,style,content,position,size);passes=passes+1
  end
 end end
 assert(passes>=3,'Thumb sizing, drag and thumb positioning use native logic')
 if options.update~=false then view:update(1/60,0,{})end
 return content
end
function scroll_to(value,name)
 local content=view._widgets_by_name[name or 'catalog_scrollbar'].content
 content.value=value;content.scroll_value=nil;content.scroll_add=nil
 view:update(.3,0,{})
end
''')
load_mod('MortisBuffManager/scripts/mods/MortisBuffManager/modules/mortis_workspace_view')
result={}
for lang in ('en','zh-cn','zh-tw'):
    L.globals().test_language=lang
    for state in ('preselect','draft','competition','missing','batch','library','rules','alloff','class','family','long','selected-many','selection-empty','search-hidden','locked','capacity'):
        L.globals().state=state
        L.execute(r'''
        fixture(state=='draft' and 'draft' or state=='competition' and 'competition' or 'preselect',state~='locked')
        view=setmetatable({}, {__index=MBMWorkspaceMortisCatalogView});view:init({},{});view._workspace_detail='diy/fivefold_salvo'
        if state=='capacity'then
         snapshot.rows={};snapshot.limit=99;snapshot.rules.limit=99;snapshot.rules.diy_limits.max_total=99
         local lang=M:localize('diy_language')
         for i=1,300 do
          local source=i<=138 and 'native' or 'diy';local id='capacity_'..i
          snapshot.rows[i]={id=id,key=source..'/'..id,policy_key='capacity/'..id,source=source,
           name=(lang=='en' and 'Capacity talent ' or lang=='zh-tw' and '容量測試天賦 ' or '容量测试天赋 ')..string.format('%03d',i),
           category=source=='native' and 'generic' or 'diy',available=true,in_build_catalog=true,missing={},allowed=true,
           weight=1,tier=1,selected=i<=99 or i>138 and i<=201}
         end
        end
        if state=='missing'then view._workspace_filter='selected';for _,row in ipairs(snapshot.rows)do if row.id=='fivefold_salvo'then
          row.available=false;row.reason='diy_peer_missing';row.missing={{name='Marek',reason='missing'},{name='Lin',reason='different'},{name='Eva',reason='pending'}}
        end end end
        if state=='alloff'then snapshot.rules.native_enabled=false;snapshot.rules.diy_enabled=false;for _,row in ipairs(snapshot.rows)do row.available=false;row.reason='diy_pool_closed'end end
        if state=='selected-many'then for i,row in ipairs(snapshot.rows)do row.selected=i<=10 end;view._workspace_filter='selected';view._workspace_message=M:localize('diy_family_pruned',99) end
        if state=='selection-empty'then for _,row in ipairs(snapshot.rows)do row.selected=false end;view._workspace_filter='selected' end
        if state=='search-hidden'then view._workspace_search='__no_matching_talents__' end
        view:on_enter()
        assert(view._widgets_by_name.background.visible,'The opaque background survives every catalog refresh')
        assert(view._widgets_by_name.background.style.background.color[1]==255,'The catalog background is fully opaque')
        if state=='capacity'then
         assert(item('filter_available').text:find('300',1,true) and item('filter_diy').text:find('162',1,true) and item('filter_selected').text:find('162',1,true))
         assert(item('category_all').text:find('300',1,true) and item('category_generic').text:find('138',1,true),'Three-digit counts use real catalog totals')
        end
        if state=='class'then click('category_class')end
        if state=='family'then click('choose_family')end
        if state=='long'then for _,row in ipairs(snapshot.rows)do if row.id=='fivefold_salvo'then row.description=string.rep(row.description..' ',8)end end;view._workspace_detail='diy/fivefold_salvo';view:update(.3,0,{});assert(view._widgets_by_name.catalog_detail_scrollbar.visible)end
        if state=='batch'then click('batch');click('batch_target_pool');click('batch_select_all')end
        if state=='library'then click('library_settings')end
        if state=='rules'then click('reward_settings')end
        assert(#M.workspace_pages==1 and M.workspace_pages[1].id=='mortis','One unified navigation page')
        if state=='draft' or state=='competition'then assert(not item('select_skill') and item('skill_1').action,'Browse actions remain available in reward modes')end
        if state=='missing'then assert(item('select_skill').action,'An unavailable saved selection can still be removed')end
        if state=='selected-many'then assert(item('skill_7') and not item('skill_8') and item('clear_selection').action,'Saved choices use the same scrolling catalog')end
        if state=='selection-empty'then assert(item('catalog_empty') and not item('clear_selection').action)end
        if state=='search-hidden'then assert(item('catalog_empty') and item('filter_selected').action,'Saved choices remain one tab away')end
        if state=='locked'then click('filter_selected');assert(not item('clear_selection').action and not item('select_skill').action,'Mission selections remain visible but locked')end
        assert(not item('next_page') and not item('previous_page') and not item('selected_next') and not item('selected_previous'),'The catalog has no page navigation')
        assert(not item('description_next') and not item('description_previous') and not item('peer_next'),'Long details have no page navigation')
        assert(not item('selected_skill_1') and not item('remove_selected_1'),'Saved choices share the source tabs instead of a separate narrow list')
        for _,name in ipairs({'catalog_scrollbar','catalog_detail_scrollbar'})do
         if view._widgets_by_name[name] and view._widgets_by_name[name].visible then
          scrollbar_frame({widget=name,cursor={0,0,0},update=false})
         end
        end
        ''')
        items=[]
        for _,item in L.globals().view._diy_items.items():
            if item.kind=='scrollbar' and not item.widget.visible:
                continue
            d={k:item[k] for k in ('key','x','y','w','h','text','color','font','selected') if item[k] is not None}
            d.update(fill=item.kind=='button',center=item.kind=='button',top=item.kind=='text')
            d.setdefault('font',20)
            d.setdefault('text','')
            assert not re.match(r'(?:diy|mortis|workspace)_', d['text']), ('Missing UI translation', lang, state, d['key'], d['text'])
            assert d['x']>=100 and d['y']>=218 and d['x']+d['w']<=1810 and d['y']+d['h']<=1000,d
            items.append(d)
            if item.kind=='scrollbar':
                d.update(fill=True,panel=True)
                if not item.widget.content.thumb_disabled:
                    thumb=item.widget.style.hotspot
                    items.append(dict(key=item.key+'_thumb',x=d['x'],y=d['y']+thumb.offset[2],w=d['w'],h=thumb.size[2],text='',fill=True,timer=True,panel=True))
        labels={'en':('CHARACTER','Loadouts        Talents        Mortis talents'),'zh-cn':('角色','配装        天赋        死灵天赋'),'zh-tw':('角色','配裝        天賦        死靈天賦')}
        items += [dict(key='header',x=105,y=80,w=1400,h=48,text=labels[lang][0],font=30),dict(key='tabs',x=105,y=152,w=1600,h=42,text=labels[lang][1],font=23)]
        result[lang+'_catalog-'+state]=items
L.execute(r'''
-- Source and semantic category tabs use production filtering and truthful counts.
new_view()
local rows,counts,categories=ProductionModel.browse(snapshot,{})
for _,legacy in ipairs({'all','native','obsolete'})do
 view._workspace_filter=legacy;view._workspace_category='old_route'
 view._diy_revision=nil;view:update(.3,0,{})
 assert(view._workspace_filter=='available' and view._workspace_category=='all')
 assert(item('filter_available').selected and not item('filter_all') and not item('filter_native'),
  'Retained page state cannot reopen removed tabs or show incompatible talents')
end
for _,source in ipairs({'available','diy','selected','unavailable'})do
 assert(item('filter_'..source).text:find(tostring(counts[source]),1,true),'Every source tab displays its result count')
 assert(item('filter_'..source).y==item('filter_available').y,'Saved choices are a peer of Eligible, DIY and Ineligible')
end
for _,category in ipairs({'all','generic','class','family'})do
 assert(item('category_'..category).text:find(tostring(categories[category]),1,true),'Every category button displays its count')
end
click('category_class');assert(not item('host_permission'),'No individual native pool control')
assert(item('skill_1') and not item('skill_2'),'Class category actually narrows eligible talents')
hover('skill_1');assert(row_by_key(view._workspace_detail).category=='class')
click('category_family');assert(item('skill_2') and not item('skill_3'),'Route category actually narrows eligible talents')
click('category_generic');assert(item('skill_1') and not item('skill_2'),'Generic category actually narrows eligible talents')
click('category_all');click('filter_unavailable')
assert(item('skill_2') and not item('skill_3'),'Ineligible tab contains unavailable talents')
hover('skill_1');assert(not row_by_key(view._workspace_detail).available)
click('filter_available');local saved_choices=selected_count();click('choose_family');click('family_fire')
assert(not view._workspace_subpage and not view._workspace_message and selected_count()==saved_choices,'Choosing the existing family returns to browsing without a cleanup message or selection changes')
family_removed=3;click('choose_family');click('family_electric')
assert(snapshot.family=='electric' and not view._workspace_subpage,'The family chooser changes the saved route')
assert(view._workspace_message==M:localize('diy_family_pruned',3),'The native family result supplies the cleanup count shown in the catalog')
click('category_class');click('filter_diy')
assert(view._workspace_category=='all' and item('skill_7'),'Opening DIY resets the native class filter so its talents stay visible')
assert(not item('filter_all') and not item('filter_native') and not item('status_filter'),'There are exactly four requested main filters')
assert(not item('next_page') and not item('previous_page'))

-- Existing bulk, text-input, reward editing and navigation flows remain usable.
new_view();click('filter_diy');click('batch');click('batch_target_pool');click('batch_select_all');click('batch_remove');assert(item('batch_result').text~='')
click('batch')
local saved=item('diy_pool').action;M._enabled=false;saved();assert(snapshot.rules.diy_enabled,'Stale callbacks stop after disable');M._enabled=true
Keyboard={ENTER=1,ESCAPE=2,BACKSPACE=3,DELETE=4,keystrokes=function()return keys or {}end}
click('search');keys={'五','重'};view:update(.3,0,{});keys={};assert(view._workspace_search=='五重' and view.is_text_input_focused)
keys={Keyboard.BACKSPACE};view:update(.3,0,{});keys={};assert(view._workspace_search=='五','Backspace removes a complete UTF-8 character')
keys={Keyboard.ENTER};view:update(.3,0,{});keys={};assert(not view.is_text_input_focused)
click('search_clear');click('library_settings');assert(not item('native_limit') and not item('diy_limit') and not item('tier_limit_1'),'Package management contains no reward controls')
click('back');click('reward_settings');click('native_limit');keys={'1','2',Keyboard.ENTER};view:update(.3,0,{});keys={}
assert(snapshot.rules.limit==12 and not view._workspace_number)
click('native_limit');keys={'9','9',Keyboard.ENTER};view:update(.3,0,{});keys={};assert(snapshot.rules.limit==99 and not view._workspace_number)
click('native_limit');keys={'1','0','0',Keyboard.ENTER};view:update(.3,0,{});keys={};assert(snapshot.rules.limit==99 and view._workspace_number)
keys={Keyboard.ESCAPE};view:update(.3,0,{});keys={};assert(not view._workspace_number)
click('back');view._workspace_focus='native_pool';view:update(.3,0,{get=function(_,name)return name=='navigate_down_continuous'end})
assert(view._workspace_focus~='native_pool','Directional navigation moves focus through the catalog controls')
''')
L.execute(r'''
-- Native widget callbacks, selected colors and hover/focus all use production UI.
new_view()
local first=snapshot.rows[1];local before=selected_count();local was_selected=first.selected==true
assert(item('skill_1').widget.content.hotspot.pressed_callback==item('skill_1').action)
item('skill_1').widget.content.hotspot.pressed_callback();view:update(.3,0,{})
assert(first.selected~=was_selected and selected_count()==before+(was_selected and -1 or 1),'One catalog click toggles a saved choice')
assert(item('skill_1').widget.content.hotspot.is_selected==first.selected,'The native selected state follows the saved choice')
assert(item('skill_1_label').color==(first.selected and 'gold' or 'text'),'Saved choice state changes row color')
assert(item('skill_1_label').text:find('\238\128\129',1,true),'Selected rows use the native ready-check glyph')
assert(not item('diy_pool').text:find('○',1,true) and not item('diy_pool').text:find('□',1,true),'Pool toggles avoid unsupported empty-circle or square glyphs')
click('skill_1');assert((first.selected==true)==was_selected and selected_count()==before,'A second click cancels the choice')
local untouched=selected_count();local calls=selection_calls
hover('skill_2');assert(view._workspace_detail==snapshot.rows[2].key and selected_count()==untouched and selection_calls==calls,'Hover inspects without modifying selection')

-- Saved choices are one click away regardless of the active search/category.
view._workspace_search='__no_matching_talents__';view._workspace_category='class';view:update(.3,0,{})
assert(item('catalog_empty'));click('filter_selected')
assert(not view._workspace_search or view._workspace_search=='','Saved tab clears search')
assert((view._workspace_category or 'all')=='all','Saved tab clears category constraints')
assert(item('skill_1') and item('skill_2') and not item('skill_3'),'Saved tab contains the complete saved set')
assert(selected_count()==untouched,'Opening saved choices preserves selection')
hover('skill_1');local selected_key=view._workspace_detail
local unavailable=row_by_key(selected_key);unavailable.available=false;unavailable.in_build_catalog=false;unavailable.reason='diy_incompatible'
view:update(.3,0,{})
assert(item('skill_1').widget.content.hotspot.is_selected and item('skill_1').action,'Incompatible saved choices remain visible and removable')
click('skill_1');assert(not unavailable.selected and selected_count()==untouched-1,'Clicking a saved choice removes it')
click('filter_unavailable');view._workspace_search=unavailable.id;view:update(.3,0,{})
calls=selection_calls;click('skill_1')
assert(not unavailable.selected and selection_calls==calls and view._workspace_detail==unavailable.key,'Unavailable catalog rows inspect without selecting')

-- Clear applies to all saved choices even if search currently hides some.
new_view();for i,row in ipairs(snapshot.rows)do row.selected=i<=10 end;view:update(.3,0,{})
click('filter_selected');view._workspace_search=snapshot.rows[1].id;view:update(.3,0,{})
click('clear_selection')
assert(selected_count()==0 and item('catalog_empty') and not item('clear_selection').action,'Clear removes all saved choices across search and scrolling')
assert(not item('selected_skill_1') and not item('remove_selected_1'),'The separate saved pane was removed')

-- Bulk actions mutate actual choices and exclude incompatible candidates.
new_view();click('batch');click('batch_select_all');click('batch_remove');assert(selected_count()==0,'Bulk removal clears actual saved choices')
click('batch_add');assert(selected_count()==#snapshot.rows-2,'Bulk addition changes the current-build candidates')
click('batch');click('filter_selected');assert(item('skill_7') and view._widgets_by_name.catalog_scrollbar.content.scroll_length>0,'Bulk results remain scrollable')

-- Keyboard/controller focus inspects without activating a row.
new_view();view._workspace_focus='skill_1';untouched=selected_count();calls=selection_calls
view:update(.3,0,{get=function(_,name)return name=='navigate_down_continuous'end})
assert(view._workspace_focus=='skill_2' and view._workspace_detail==snapshot.rows[2].key,'Directional row focus synchronizes details')
assert(selected_count()==untouched and selection_calls==calls,'Directional focus never toggles selection')
view:update(.3,0,{get=function(_,name)return name=='confirm_pressed'end});view:update(.3,0,{})
assert(selection_calls==calls+1,'Confirm activates the focused choice once')

-- A disappearing last row must keep confirm inside saved choices, never jump
-- to the first control (the room-wide native pool switch).
new_view();for i,row in ipairs(snapshot.rows)do row.selected=i<=7 end
view:update(.3,0,{});click('filter_selected');view._workspace_focus='skill_7'
assert(selected_count()==7 and item('skill_7') and not item('skill_8'))
for remaining=7,1,-1 do
 view:update(.3,0,{get=function(_,name)return name=='confirm_pressed'end});view:update(.3,0,{})
 assert(selected_count()==remaining-1,'Repeated confirm removes exactly one saved talent')
 local expected=remaining>1 and 'skill_'..(remaining-1) or 'filter_selected'
 assert(view._workspace_focus==expected,'Removing the last visible row clamps focus to a surviving row, then the selected tab')
 assert(rules_calls==0 and snapshot.rules.native_enabled and snapshot.rules.diy_enabled,'Removing selected rows never toggles either room pool')
end
calls=selection_calls
view:update(.3,0,{get=function(_,name)return name=='confirm_pressed'end});view:update(.3,0,{})
assert(view._workspace_focus=='filter_selected' and selected_count()==0 and selection_calls==calls and rules_calls==0,'Confirm on an empty selected tab performs no selection or room-rule writes')
new_view();view._workspace_filter='diy';view._workspace_focus=nil;untouched=selected_count()
view:update(.3,0,{get=function(_,name)return name=='confirm_pressed'end});view:update(.3,0,{})
assert(view._workspace_focus=='filter_diy' and view._workspace_filter=='diy','Initial keyboard focus prefers the current source tab')
assert(selected_count()==untouched and selection_calls==0 and rules_calls==0 and snapshot.rules.native_enabled,'The first confirm without prior focus cannot change room rules')

-- Mission changes and retained callbacks cannot perform stale mutations.
new_view();click('filter_selected');local saved_remove=item('skill_1').action;local saved_clear=item('clear_selection').action
untouched=selected_count();snapshot.editable=false;snapshot.selection_editable=false;snapshot.rules.locked=true
saved_remove();saved_clear();view:update(.3,0,{})
assert(selected_count()==untouched and not item('clear_selection').action,'Mission lock blocks retained mutating callbacks')
calls=selection_calls;click('skill_1');assert(selection_calls==calls and selected_count()==untouched,'Locked clicks only inspect')
new_view();click('filter_selected');saved_remove=item('skill_1').action;calls=selection_calls;untouched=selected_count();M._enabled=false
saved_remove();assert(selection_calls==calls and selected_count()==untouched,'Disabled mods reject retained callbacks before reaching the model');M._enabled=true
new_view();click('filter_selected');saved_remove=item('skill_1').action
hover('skill_1');local old_key=view._workspace_detail
snapshot.rows=table.clone_instance(snapshot.rows);row_by_key(old_key).selected=false;untouched=selected_count()
saved_remove();assert(selected_count()==untouched and not row_by_key(old_key).selected,'A stale remove never restores a choice removed elsewhere')
new_view();local saved_add=item('skill_1').action
local old_first=snapshot.rows[1];table.remove(snapshot.rows,1);untouched=selected_count()
saved_add();assert(not row_by_key(old_first.key) and selected_count()==untouched,'Removed entries cannot be resurrected by stale callbacks')
''')
L.execute(r'''
-- Native wheel momentum, draggable thumb, bounds and row virtualization.
new_view()
for i=1,120 do snapshot.rows[#snapshot.rows+1]={id='long_'..i,key='native/long_'..i,source='native',name='Long native '..i,
 category='generic',in_build_catalog=true,available=true,missing={},selected=false}end
view:update(.3,0,{})
local visible_rows=ProductionModel.browse(snapshot,{})
local content=view._widgets_by_name.catalog_scrollbar.content
assert(content.scroll_length==#visible_rows-7 and content.area_length==#visible_rows,'Scrollbar range represents rows beyond the seven-row viewport')
local untouched=selected_count();local calls=selection_calls
assert((view._workspace_scroll_index or 0)==0 and item('skill_7') and not item('skill_8'))
for frame=1,30 do scrollbar_frame({wheel=frame==1 and -1 or 0})end
local first_scroll=view._workspace_scroll_index
assert(first_scroll>0 and first_scroll<7,'One wheel notch moves rows without skipping a full page')
hover('skill_1');assert(view._workspace_detail==visible_rows[first_scroll+1].key,'Scrolling changes visible talent identities')
assert(selected_count()==untouched and selection_calls==calls,'Scrolling never changes saved choices')
scroll_to(0)
for frame=1,30 do scrollbar_frame({cursor={1500,600,0},wheel=frame==1 and -1 or 0})end
assert(view._workspace_scroll_index==0,'Wheel input over details does not scroll the catalog')
for frame=1,30 do scrollbar_frame({cursor={400,300,0},wheel=frame==1 and -1 or 0})end
assert(view._workspace_scroll_index==0,'Wheel input outside both panes does not scroll the catalog')

-- Drag through the actual native input logic, including release.
scrollbar_frame({update=false})
local bar=view._ui_scenegraph[view._widgets_by_name.catalog_scrollbar.scenegraph_id]
content=view._widgets_by_name.catalog_scrollbar.content
content.hotspot.on_pressed=true
scrollbar_frame({cursor={bar.position[1]+2,bar.position[2]+5,0},hold=true})
content.hotspot.on_pressed=false
scrollbar_frame({cursor={bar.position[1]+2,bar.position[2]+bar.size[2],0},hold=true})
scrollbar_frame({cursor={bar.position[1]+2,bar.position[2]+bar.size[2],0}})
assert(view._workspace_scroll_index==#visible_rows-7,'Dragging the thumb reaches the final seven talents')
hover('skill_7');assert(view._workspace_detail==visible_rows[#visible_rows].key,'The last catalog talent is reachable')
assert(not content.drag_active and selected_count()==untouched,'Release ends dragging without changing choices')
click('filter_diy');assert(view._workspace_scroll_index==0,'A source change resets the scroll position')
scroll_to(1);click('category_generic');assert(view._workspace_scroll_index==0 and item('catalog_empty'),'A category change resets and narrows the scrolling list')
click('filter_available');click('category_all');scroll_to(1);click('filter_unavailable');assert(view._workspace_scroll_index==0,'Eligibility changes reset scrolling');click('filter_available')
scroll_to(1);click('search');keys={'__no_match__'};view:update(.3,0,{});keys={};assert(view._workspace_scroll_index==0 and item('catalog_empty'),'Text search resets scrolling')
keys={Keyboard.ENTER};view:update(.3,0,{});keys={};click('search_clear')
assert(view._workspace_scroll_index==0)

-- Moving keyboard/controller focus past a visible boundary scrolls one row.
view:update(.3,0,{})
view._workspace_focus='skill_7';view._nav_wait=0
view:update(.3,0,{get=function(_,name)return name=='navigate_down_continuous'end})
assert(view._workspace_scroll_index==1 and view._workspace_focus=='skill_7' and view._workspace_detail==visible_rows[8].key,'Down from row seven reveals the next talent without moving into the footer')
view._workspace_focus='skill_1';view._nav_wait=0
view:update(.3,0,{get=function(_,name)return name=='navigate_up_continuous'end})
assert(view._workspace_scroll_index==0 and view._workspace_focus=='skill_1' and view._workspace_detail==visible_rows[1].key,'Up from the first visible row reveals the preceding talent')
assert(selected_count()==untouched and selection_calls==calls)

-- Long details use their own native scroll area and reveal trailing peer data.
new_view()
local row=row_by_key('diy/fivefold_salvo')
row.description=string.rep('A long description with complete readable words. ',100)..'\nLAST_DESCRIPTION_MARKER'
row.missing={{name='Marek',reason='missing'},{name='Lin',reason='different'},{name='Eva',reason='pending'}}
view._workspace_detail=row.key;view:update(.3,0,{})
local detail=view._widgets_by_name.catalog_detail_scrollbar.content
assert(detail.scroll_length>0 and not item('description_next') and not item('description_previous'),'Long descriptions use a separate scrollbar')
local before=view._workspace_scroll_index or 0
for frame=1,30 do scrollbar_frame({widget='catalog_detail_scrollbar',cursor={1300,600,0},wheel=frame==1 and -1 or 0})end
assert(view._workspace_detail_scroll_index>0 and view._workspace_scroll_index==before,'Details scroll independently of the catalog')
scroll_to(1,'catalog_detail_scrollbar')
assert(item('detail_description').text:find('LAST_DESCRIPTION_MARKER',1,true) and item('detail_description').text:find('Marek',1,true),'The end of a long description and peer requirements are both reachable')
local detail_before=view._workspace_detail_scroll_index
for frame=1,30 do scrollbar_frame({widget='catalog_detail_scrollbar',cursor={200,600,0},wheel=frame==1 and 1 or 0})end
assert(view._workspace_detail_scroll_index==detail_before,'Wheel input over talents does not scroll details')
hover('skill_1');assert((view._workspace_detail_scroll_index or 0)==0,'Inspecting a different talent starts its details at the top')
''')
# Exercise the actual native renderer wrapper too. Only the engine's font
# measurement primitive is replaced; it splits this explicitly line-broken
# fixture and records its arguments instead of providing a fixed page.
L.execute('local UIFonts={data_by_type=function(name)assert(name=="proxima_nova_bold");return {path="native-proxima-font",render_flags=17}end};'+method(native('scripts/managers/ui/ui_renderer.lua'),'UIRenderer','word_wrap'))
L.execute(r'''
Gui={};native_wrap_calls=0;native_wrap_rows={}
function Gui.slug_word_wrap(gui,text,font,size,width,returns,dividers,reuse,flags)
 native_wrap_calls=native_wrap_calls+1
 native_wrap_arguments={gui=gui,text=text,font=font,size=size,width=width,returns=returns,dividers=dividers,reuse=reuse,flags=flags}
 for key in pairs(native_wrap_rows)do native_wrap_rows[key]=nil end
 for line in (text..'\n'):gmatch('(.-)\n')do native_wrap_rows[#native_wrap_rows+1]=line end
 return native_wrap_rows,{}
end
new_view()
local row=row_by_key('diy/fivefold_salvo');local lines={}
for i=1,18 do lines[i]=string.format('Native line %02d',i)end
lines[1]='{#color(255,100,0)}Native color{#reset()}';lines[2]='';lines[18]='NATIVE_WRAP_FINAL'
row.description=table.concat(lines,'\n');view._workspace_detail=row.key
local gui={};view._ui_renderer={gui=gui,scale=1.25};view:update(.3,0,{})
local args=native_wrap_arguments
assert(args.gui==gui and args.font=='native-proxima-font' and args.size==21 and args.width==598*1.25,'The view delegates font and scaled width to native word_wrap')
assert(args.returns=='\n' and args.dividers==' -+&/*' and args.reuse==true and args.flags==17,'Native wrapping retains engine newline, divider and font settings')
assert(args.text:find(lines[1],1,true) and args.text:find('\n\n',1,true),'Color markup and explicit blank lines reach native wrapping unchanged')
assert(item('detail_description').text:find(lines[1],1,true) and item('detail_description').text:find('\n\n',1,true),'The resulting visible lines preserve markup and blank lines')
local calls=native_wrap_calls
native_wrap_rows[1]='ENGINE_REUSED_STORAGE'
view:update(.3,0,{})
assert(native_wrap_calls==calls and not item('detail_description').text:find('ENGINE_REUSED_STORAGE',1,true),'Cached lines own their strings after the native renderer reuses its table')
scroll_to(1,'catalog_detail_scrollbar')
assert(item('detail_description').text:find('NATIVE_WRAP_FINAL',1,true),'Native wrapped output scrolls through the final description line')
view._ui_renderer.scale=2;view:update(.3,0,{})
assert(native_wrap_calls==calls+1 and native_wrap_arguments.width==598*2,'Changing render scale invalidates the line-wrap cache')
row.description=row.description..'\nCONTENT_CHANGED';view:update(.3,0,{})
assert(native_wrap_calls==calls+2 and (view._workspace_detail_scroll_index or 0)==0,'Changed text is wrapped again and starts from the top')
''')
(DEV/'qa/catalog-layouts.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8')
print('Unified native UI: 48 three-language layouts including 300 talents, counted source/category filters, saved-choice tab, real native wheel/drag scrolling, independent long details, direct toggles, focus, bulk, locks and stale callbacks: PASS')
