-- Synthetic pools for transport/timing tests; native data is tested separately.
function route_test_pool()
    local pool = { families = { "fire", "electric", "critical" }, routes = {}, categories = { "regular" },
        legendary = { regular = {} }, legendary_waves = { [3]=true, [6]=true, [9]=true },
        wave_weights = { wave_3={regular=1}, wave_6={regular=1}, wave_9={regular=1} } }
    for _, family in ipairs(pool.families) do
        local route = { priority = { "family_" .. family .. "_1" }, buffs = {} }
        for i=2,10 do route.buffs[#route.buffs+1]="family_"..family.."_"..i end
        pool.routes[family]=route
    end
    for i=1,32 do pool.legendary.regular[i]="buff_"..i end
    return pool
end
function route_test_known(name) return type(name)=="string" and (name:match("^buff_%d+$")~=nil or name:match("^family_%a+_%d+$")~=nil) end
function route_test_family(name) return name=="fire" or name=="electric" or name=="critical" end
