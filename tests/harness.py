from pathlib import Path
import sys,re,json
work=Path(__file__).resolve().parent
sys.excepthook=lambda typ,value,tb: print(typ.__name__+': '+str(value))
from project_env import PROJECT, GAME, FIXTURES, CHECKS, SOURCES
from isolated_diy_io import isolate
isolate()
from lupa.luajit21 import LuaRuntime
L=LuaRuntime(unpack_returned_tuples=True)
stage=SOURCES; game=GAME
L.execute('''
function settings(_,value) return value end
function table.clone(t) local r={} for k,v in pairs(t or {}) do r[k]=v end return r end
function table.clone_instance(t)
    if type(t)~="table" then return t end
    local r={} for k,v in pairs(t) do r[k]=table.clone_instance(v) end return r
end
function table.merge(a,b) for k,v in pairs(b) do a[k]=v end return a end
function table.merge_recursive(a,b)
    for k,v in pairs(b) do
        if type(v)=="table" and type(a[k])=="table" then table.merge_recursive(a[k],v) else a[k]=table.clone_instance(v) end
    end
    return a
end
function table.merge_recursive_advanced(a,b) return table.merge_recursive(a,b),{} end\nfunction table.enum(...) local r={} for _,s in ipairs({...}) do r[s]=s end return r end
function table.keys(t) local r={} for k in pairs(t) do r[#r+1]=k end return r end
table.enum_id=table.enum
function table.array_contains(t,v) for _,x in ipairs(t) do if x==v then return true end end return false end
function math.clamp(n,a,b) return math.max(a,math.min(n,b)) end
function math.lerp(a,b,t) return a+(b-a)*t end
function math.round(n) return math.floor(n+0.5) end
function math.random_range(a,b) return (a+b)/2 end
function Localize(s)
    local strings=nil
    return strings and strings[s] and (strings[s][test_language or "zh-cn"] or strings[s].en) or s
end
Managers={state={}}
Script={new_map=function() return {} end,new_array=function() return {} end}
CLASS={HudElementBossHealth={}}
Application={user_setting=function() return {} end}
mods={}; hooks={}; classes={}; warnings={}
function get_mod(name) return mods[name] end
function new_test_mod(name)
    local m={_settings={},values={},localization={}}
    function m:get(k) return self.values[k] end
    function m:set(k,v) self.values[k]=table.clone_instance(v) end
    function m:is_enabled() return self._enabled~=false end
    function m:enable_all_hooks() self._hooks_enabled=true end
    function m:disable_all_hooks() self._hooks_enabled=false end
    -- DMF always formats translated text, including calls without arguments.
    function m:localize(k,...) local v=self.localization[k]; local s=v and (v[test_language or "zh-cn"] or v.en) or k; return string.format(s,...) end
    function m:io_dofile(p) return load_mod_file(p) end
    function m:add_global_localize_strings(t) self.global_localization=self.global_localization or {}; for k,v in pairs(t) do self.global_localization[k]=v end end
    function m:hook(target,name,fn) hooks[#hooks+1]={target=target,name=name,fn=fn,owner=self,safe=false} end
    function m:hook_safe(target,name,fn) hooks[#hooks+1]={target=target,name=name,fn=fn,owner=self,safe=true} end
    function m:hook_require(path,fn) hooks[#hooks+1]={path=path,fn=fn,owner=self,require_hook=true} end
    function m:info(...) end
    function m:warning(...) warnings[#warnings+1]={...} end
    function m:error(...) error(string.format(...)) end
    function m:add_require_path(...) end
    function m:register_view(...) end
    function m:command(name,description,fn) self.commands=self.commands or {}; self.commands[name]=fn end
    function m:notify(...) end
    mods[name]=m
    return m
end
''')
def lua_file(path): return L.execute(path.read_text(encoding='utf-8-sig'),name='@'+str(path))
def load_mod(p): return lua_file(stage/(p+'.lua'))
L.globals().load_mod_file=load_mod
cache={'bit':L.eval("require('bit')"),'ffi':L.eval("require('ffi')")}
def tbl(x):
    if isinstance(x,dict): return L.table_from({k:tbl(v) for k,v in x.items()})
    if isinstance(x,list): return L.table_from([tbl(v) for v in x])
    return x

cache['scripts/managers/mission_buffs/mission_buffs_allowed_buffs']=tbl({})
cache['scripts/settings/buff/hordes_buffs/hordes_buffs_data']=tbl({})
cache['scripts/settings/network/matchmaking_constants']=tbl({'HOST_TYPES':{'singleplay':'solo','singleplay_backend_session':'solo_backend','player':'realms'}})
def require(path):
    if path not in cache: raise RuntimeError('Missing test dependency: '+path)
    return cache[path]
L.globals().require=require
L.globals().new_test_mod(PROJECT.name)
lua_file(PROJECT/'tests/route_fixture.lua')
cache['scripts/managers/mission_buffs/mission_buffs_settings']=tbl({'filtering_categories':{'regular':'regular','jackpot':'jackpot','ability':'ability','grenade':'grenade'},'filtering_categories_pick_rate_per_wave':{'wave_3':{'ability':5,'grenade':3,'jackpot':1,'regular':1},'wave_6':{'ability':3,'grenade':3,'jackpot':3,'regular':3},'wave_9':{'ability':5,'grenade':5,'jackpot':2,'regular':0}}})
cache['scripts/settings/hordes_mode_settings']=tbl({'give_legendary_buffs_at_waves':[3,6,9]})
mod=L.globals().mods[PROJECT.name]
mod.localization=load_mod(f'{PROJECT.name}/scripts/mods/{PROJECT.name}/{PROJECT.name}_localization')
data=load_mod(f'{PROJECT.name}/scripts/mods/{PROJECT.name}/{PROJECT.name}_data')
