"""Count actual catalog/native calls, including quota exhaustion and recovery."""
from harness import *
L.execute('perf={valid=0,pool=0,profile=0}')
def counted_load(path):
    value=load_mod(path)
    if path.endswith('/mortis_catalog'):
        L.globals().CountedCatalog=value
        L.execute('''
        for key,counter in pairs({valid_for_setup="valid",draft_for_setup="pool",resolve_profile_abilities="profile"}) do
            local original=CountedCatalog[key]
            CountedCatalog[key]=function(...) perf[counter]=perf[counter]+1; return original(...) end
        end
        ''')
    return value
L.globals().load_mod_file=counted_load
import runtime_tests
L.execute('''
M._settings.mortis_mode="competition";M._settings.mortis_buff_limit=99
M.update_mortis_buffs(.5);assert(M.choose_mortis_draft(1))
local attack
for _,h in ipairs(hooks) do if h.target==AttackReports and h.name=="add_attack_result" then attack=h.fn end end
M._settings.mortis_kill_horde=100
for i=1,98 do attack({_is_server=true},nil,{breed={breed_type="minion",kind="horde"}},unit,nil,nil,nil,1,"died") end
M.update_mortis_buffs(.5)
assert(not M.mortis_draft_snapshot().counting and M.mortis_draft_snapshot().active,"Earned quota stops counting while queued choices remain available")
while M.mortis_draft_snapshot().active do assert(M.choose_mortis_draft(1));M.update_mortis_buffs(.5) end
assert(table.size(applied)==197)
local checks,breed_calls=0,0
local saved_check=handler.does_player_have_buff_saved
handler.does_player_have_buff_saved=function(...) checks=checks+1;return saved_check(...) end
local breed_lookup=TestBreed.unit_breed_or_nil
TestBreed.unit_breed_or_nil=function(...) breed_calls=breed_calls+1;return breed_lookup(...) end
local before=M.mortis_draft_snapshot()
local v,p,f=perf.valid,perf.pool,perf.profile
for i=1,3600 do M.update_mortis_buffs(1/60) end
for i=1,1000 do attack({_is_server=true},nil,{},unit,nil,nil,nil,1,"died") end
local after=M.mortis_draft_snapshot()
assert(before==after and not after.counting and after.progress==0)
assert(perf.valid==v and perf.pool==p and perf.profile==f,"No repeated catalog builds/profile ability scans for unchanged live setup")
assert(checks<=197*13 and checks>=197*10,"Recovery checks retain 5-second coverage rather than 2 Hz full scans")
assert(breed_calls==0,"Finished players do not classify victims or accumulate progress")
-- Changes within the same talent table invalidate eligibility immediately.
P:profile().talents.changed_in_place=1
M.update_mortis_buffs(.5);assert(perf.valid>v)
-- Outside removal is recovered, without repeatedly reapplying native Buffs.
local name=after.selected[1];saved[name]=nil;applied[name]=nil
local adds=calls.add
for i=1,10 do M.update_mortis_buffs(.5) end
assert(applied[name] and calls.add==adds+1)
-- Respawn/handler replacement cannot reuse the previous recovery audit.
local replacement={};P.player_unit=replacement;ALIVE[replacement]=true
local checked=checks;M.update_mortis_buffs(.5);assert(checks>checked)
M.cleanup_mortis_buffs();assert(table.size(applied)==0)
''')
print('Mortis performance: 60 seconds / 197 Buffs, zero unchanged catalog rebuilds, zero victim classifications after quota, cached HUD snapshots, <=13 recovery audits, in-place build and respawn invalidation, external-removal recovery: PASS')

L.execute('''
mode="hub";M._settings.mortis_mode="preselect";M._settings.mortis_buff_limit=99
M.mortis_buffs_on_setting_changed("mortis_mode")
local snapshot=M.mortis_talent_ui_snapshot(P)
local rows=snapshot.entries;assert(#rows>0)
local sorts=0;local original_sort=table.sort
table.sort=function(...) sorts=sorts+1;return original_sort(...) end
for i=1,100 do assert(M.mortis_talent_ui_snapshot(P).entries==rows) end
assert(sorts==0,"Unchanged editor snapshots do not allocate/re-sort the entire catalog")
-- Filtering a UI snapshot must not consume the shared catalog cache.
snapshot.entries={};assert(M.mortis_talent_ui_snapshot(P).entries==rows)
local stored=M:get("tamm_mortis_selections_v1")
stored.hero={rows[1].buff_name}
local changed=M.mortis_talent_ui_snapshot(P)
assert(changed.entries~=rows and changed.selected_count==1 and sorts>0)
rows=changed.entries;local before=sorts
stored.hero[1]=rows[2].buff_name
assert(M.mortis_talent_ui_snapshot(P).entries~=rows and sorts>before,"In-place saved selection changes invalidate rows")
rows=M.mortis_talent_ui_snapshot(P).entries
P:profile().talents.changed_again=1
assert(M.mortis_talent_ui_snapshot(P).entries~=rows,"Changed talent eligibility invalidates the editor catalog")
table.sort=original_sort
''')
print('Mortis editor: 100 unchanged snapshots reuse sorted rows; filter replacement, in-place selections and talent eligibility changes are isolated and refreshed: PASS')

parser=cache['scripts/ui/constant_elements/elements/mission_buffs/utilities/mission_buffs_parser']
L.globals().EditorParser=parser
L.execute('''
local formatted=0
EditorParser.get_formated_buff_description=function(data) formatted=formatted+1;return "effect: "..data.description end
for i=1,5 do
 local name="editor_new_"..i
 Allowed.legendary_buffs.generic[#Allowed.legendary_buffs.generic+1]=name
 Data[name]={title=name,description=name};M.mortis_known_buffs[name]=true
end
P:profile().talents.new_editor_catalog=1
local rows=M.mortis_talent_ui_snapshot(P).entries
assert(formatted==0,"Opening the list must not format every unseen tooltip")
assert(M.mortis_talent_ui_description("editor_new_1")=="effect: editor_new_1")
assert(formatted==1)
for i=1,100 do M.mortis_talent_ui_description("editor_new_1") end
assert(formatted==1,"Unchanged details use the formatted native tooltip cache")
assert(M.mortis_talent_ui_description("editor_new_2")=="effect: editor_new_2" and formatted==2)
''')
print('Mortis first opening: unseen descriptions format only on display, once per Buff; unchanged details reused: PASS')
