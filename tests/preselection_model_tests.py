"""Fresh-state checks for saved-selection actions from the native catalog."""
from harness import *

L.globals().Model = load_mod('MortisBuffManager/scripts/mods/MortisBuffManager/modules/mortis_workspace_model')
L.execute('''
local m=get_mod('MortisBuffManager')
local family='fire'
local pool_enabled=true
local editing=true
local native_selected={'electric'}
local sources={public={kind='generic'},class_blitz={kind='class',archetype='ogryn',requirement='grenade'},
 fire={kind='family',families={'fire'}},electric={kind='family',families={'electric'}}}
local setup={complete=true,archetype='ogryn',family='fire',resources={},talents={}}
Managers.player={local_player_safe=function()return {}end}
m.mortis_rules=function()return {mode='preselect',native_enabled=pool_enabled,diy_enabled=pool_enabled}end
m.mortis_host_policy={editable=function()return true end,allowed=function()return true end,
 current=function()return {native={},diy={}}end,missing=function()return {}end}
m.mortis_inspect_native=function()return {public=true,class_blitz=true,[family]=true},native_selected,family,64 end
m.mortis_build_setup=function()setup.family=family;return setup end
m.mortis_draft_snapshot=function()return {}end
m.session_context=function()return {}end
m.mortis_selectable_buffs={'public','class_blitz','fire','electric'}
m.mortis_native_sources=sources
m.mortis_buff_ui_data=function(id)return {display_name=id}end
m.diy_library={options={selected={'other_class'}},can_edit=function()return editing end,
 document={id='test',entries={
  {id='compatible',name={en='compatible'},description={en='compatible'},enabled=true,weight=1},
  {id='other_class',name={en='other class'},description={en='other class'},enabled=true,weight=1,availability={archetypes={'psyker'}}}}}}
local function keyset(rows)local keys={}for _,row in ipairs(rows)do keys[row.key]=true end;return keys end
local snapshot=Model.snapshot()
local rows,counts,categories=Model.browse(snapshot)
local keys=keyset(rows)
assert(#rows==4 and keys['native/fire'] and not keys['native/electric'] and not keys['diy/other_class'],
 'The default available tab contains only eligible talents for the chosen family and build')
assert(counts.available==4 and counts.unavailable==2 and counts.diy==2 and counts.selected==2)
assert(categories.all==4 and categories.generic==1 and categories.class==1 and categories.family==1)
for _,row in ipairs(snapshot.rows)do
 if row.id=='class_blitz' then assert(row.category=='class' and row.requirement=='grenade' and row.archetype=='ogryn')end
 if row.id=='fire' then assert(row.category=='family' and row.family=='fire' and row.families[1]=='fire')end
end
pool_enabled=false
local closed=Model.snapshot()
rows,counts=Model.browse(closed)
assert(#rows==0 and counts.available==0 and counts.unavailable==6,'Closing pools moves their entries to unavailable')
assert(#Model.browse(closed,{source='diy'})==2,'The DIY tab includes closed and incompatible entries')
assert(#Model.browse(closed,{source='unavailable'})==6,'Unavailable includes other routes and classes')
assert(#Model.browse(closed,{source='selected'})==2,'Closing pools does not hide saved choices')
assert(#Model.browse(closed,{source='all',status='current'})==4,'Legacy current-build browsing remains pool-independent')
pool_enabled=true
rows=Model.browse(snapshot,{source='selected'})
keys=keyset(rows)
assert(#rows==2 and keys['native/electric'] and keys['diy/other_class'],'Every saved choice remains removable after build changes')
assert(#Model.browse(snapshot,{source='selected',category='family'})==1)
assert(#Model.browse(snapshot,{source='selected',search='OTHER CLASS'})==1,'Saved selections can still be searched case-insensitively')
rows,counts,categories=Model.browse(snapshot,{source='available',category='class'})
assert(#rows==1 and counts.available==1 and counts.unavailable==0 and counts.diy==0 and counts.selected==2)
assert(categories.all==4 and categories.generic==1 and categories.class==1 and categories.family==1,
 'Category counts ignore the active category while respecting the main tab')
rows,counts,categories=Model.browse(snapshot,{source='diy'})
assert(#rows==2 and categories.all==2 and counts.available==4 and counts.diy==2)
rows,counts,categories=Model.browse(snapshot,{source='unavailable'})
assert(#rows==2 and categories.all==2 and categories.family==1)
rows,counts=Model.browse(snapshot,{source='diy',search='OTHER CLASS'})
assert(#rows==1 and counts.available==0 and counts.unavailable==1 and counts.diy==1 and counts.selected==2,
 'Tab counts respect search while the saved total stays visible')
assert(#Model.browse(snapshot,{search='class_'})==1,'Internal talent IDs remain searchable')
assert(#Model.browse(snapshot,{search='[literal]'})==0,'Search treats punctuation literally')
family='electric'
local electric=Model.snapshot()
rows,counts=Model.browse(electric,{category='family'})
assert(#rows==1 and rows[1].id=='electric' and counts.available==1,'Changing the actual family changes visible family talents')
assert(snapshot.family=='fire' and snapshot.rows[1].selected==electric.rows[1].selected,
 'Browsing does not alter the prior snapshot or saved choices')

-- Exercise family changes through the production snapshot and DIY eligibility,
-- with storage boundaries recording every attempted write.
local family_writes,native_writes,diy_writes=0,0,0
local freeze_after_family=false
m.set_mortis_family_from_talent_ui=function(_,name)
 if name=='broken' then return false,'storage','injected failure' end
 if name==family then return false,'unchanged' end
 local kept={};for _,id in ipairs(native_selected)do
  if id=='public' or id=='class_blitz' or id==name then kept[#kept+1]=id end
 end
 local removed=#native_selected-#kept
 if removed>0 then native_writes=native_writes+1;native_selected=kept end
 family=name;family_writes=family_writes+1
 if freeze_after_family then editing=false end
 return true,'changed',removed
end
m.toggle_mortis_buff_from_talent_ui=function(_,id)
 for i,saved in ipairs(native_selected)do if id==saved then table.remove(native_selected,i);native_writes=native_writes+1;return true end end
 error('Family cleanup may only remove existing native choices')
end
m.diy_library.toggle=function(id)
 for i,saved in ipairs(m.diy_library.options.selected)do
  if id==saved then table.remove(m.diy_library.options.selected,i);diy_writes=diy_writes+1;return true end
 end
 error('Family cleanup may only remove existing DIY choices')
end
local entries=m.diy_library.document.entries
entries[#entries+1]={id='fire_only',name='Fire only',description='Fire only',enabled=true,weight=1,availability={families={'fire'}}}
entries[#entries+1]={id='electric_only',name='Electric only',description='Electric only',enabled=true,weight=1,availability={families={'electric'}}}
family='fire';native_selected={'public','class_blitz','fire'}
m.diy_library.options.selected={'compatible','other_class','fire_only','electric_only'}
local changed,reason,removed=Model.family('electric')
assert(changed and reason=='changed' and removed==3 and native_writes==1 and diy_writes==2)
local remaining=keyset(Model.browse(Model.snapshot(),{source='selected'}))
assert(remaining['native/public'] and remaining['native/class_blitz'] and remaining['diy/compatible'] and remaining['diy/electric_only'])
assert(not remaining['native/fire'] and not remaining['diy/fire_only'] and not remaining['diy/other_class'],
 'A family change prunes old-route native, old-route DIY and other incompatible choices, retaining compatible rewards')
local writes=family_writes+native_writes+diy_writes
Model.browse(Model.snapshot(),{source='unavailable',category='family'})
assert(not Model.family('electric') and writes==family_writes+native_writes+diy_writes,
 'Browsing or choosing the same family never prunes or saves choices')
local failed,error,detail=Model.family('broken')
assert(not failed and error=='storage' and detail=='injected failure' and writes==family_writes+native_writes+diy_writes,
 'Failed family storage must not prune any choices')
editing=false
assert(not Model.family('fire') and family=='electric' and writes==family_writes+native_writes+diy_writes,
 'A frozen snapshot prevents both family and selection writes')
editing=true
changed,reason,removed=Model.family('fire')
assert(changed and removed==1 and native_writes==1 and diy_writes==3,'Compatible native choices are not redundantly saved')
changed,reason,removed=Model.family('electric')
assert(changed and removed==0 and native_writes==1 and diy_writes==3,'No selection writes occur when everything remains compatible')
pool_enabled=false
changed,reason,removed=Model.family('fire')
assert(changed and removed==3 and #native_selected==0 and #m.diy_library.options.selected==0,
 'Explicit family changes also remove saved choices whose native or DIY pool is closed')
freeze_after_family=true;writes=native_writes+diy_writes
changed,reason=Model.family('electric')
assert(not changed and reason=='diy_edit_in_hub' and writes==native_writes+diy_writes,
 'If preparation freezes after the family write, cleanup performs no further selection writes')
''')
print('Catalog model: available/DIY/selected/unavailable tabs, current build/route filtering, native categories, counts and invalid saved choices: PASS')
print('Family changes: prune native/DIY incompatibilities, preserve compatible choices, avoid unchanged writes and honor storage failures/mission freeze: PASS')
L.execute('''
local m=get_mod('MortisBuffManager')
local state={editable=true,rows={
 {id='native',key='native/native',source='native',selected=false,available=true},
 {id='diy',key='diy/diy',source='diy',selected=false,available=true}}}
local writes=0
Model.snapshot=function()return {selection_editable=state.editable,rows=table.clone_instance(state.rows),player={}}end
local function toggle(id)
 for _,row in ipairs(state.rows)do if row.id==id then row.selected=not row.selected;writes=writes+1;return true end end
 error('Unknown selection write')
end
m.diy_library={toggle=toggle}
m.toggle_mortis_buff_from_talent_ui=function(_,id)return toggle(id)end
for _,row in ipairs(state.rows)do
 local index=row.source=='native' and 1 or 2
 local function captured()return Model.snapshot().rows[index]end
 local add=captured();assert(Model.select(add) and row.selected)
 local remove=captured();assert(Model.select(remove) and not row.selected)
 local before=writes
 assert(Model.select(remove) and not row.selected and writes==before,'Old removal must not re-add a talent')
 row.selected=true;assert(Model.select(add) and row.selected and writes==before,'Old add must not remove an existing choice')
 row.available=false;assert(Model.select(captured()) and not row.selected,'Unavailable saved selections remain removable')
 local ok,reason=Model.select(captured());assert(not ok and reason=='incompatible' and not row.selected)
 row.available=true;add=captured();row.available=false
 assert(not Model.select(add) and not row.selected,'A newly unavailable talent cannot be added through an old button')
 row.available=true;state.editable=false
 assert(not Model.select(captured()) and not row.selected,'Mission lock is checked at action time')
 state.editable=true
end
local keys={['native/native']=true,['diy/diy']=true}
local changed,skipped=Model.batch(keys,'preselection',true)
assert(changed==2 and skipped==0 and state.rows[1].selected and state.rows[2].selected)
local before=writes;changed,skipped=Model.batch(keys,'preselection',true)
assert(changed==0 and skipped==0 and writes==before,'Batch add is idempotent')
state.rows[2].available=false
changed,skipped=Model.batch(keys,'preselection',false)
assert(changed==2 and skipped==0 and not state.rows[1].selected and not state.rows[2].selected)
state.rows[1].selected=true;state.rows[2].selected=true;state.editable=false
changed,skipped=Model.batch(keys,'preselection',false)
assert(changed==0 and skipped==2 and state.rows[1].selected and state.rows[2].selected)
state.editable=true
local removed=Model.snapshot().rows[2];state.rows[2]=nil
assert(not Model.select(removed),'Removed package entries cannot be resurrected by old controls')
''')
print('Preselection model: fresh eligibility, mission lock, stale add/remove, unavailable removal and batch clear: PASS')
