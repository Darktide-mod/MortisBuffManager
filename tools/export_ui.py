"""Export only this project's actual UI definitions, without launching the game."""
from pathlib import Path
import argparse, json, re, runpy, sys
PROJECT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(PROJECT/'tests'))
from project_env import CHECKS
parser=argparse.ArgumentParser(description=__doc__)
parser.add_argument('--output',type=Path,default=CHECKS/'ui-layouts.json')
layout_output=parser.parse_args().output
globals().update(runpy.run_path(str(PROJECT/'tests/harness.py')))
result={}
name=PROJECT.name
for lang in ('en','zh-cn','zh-tw'):
    L.globals().test_language=lang
    data=load_mod(f'{name}/scripts/mods/{name}/{name}_data')
    loc=L.globals().mods[name].localization
    def tr(k):
        return L.globals().mods[name].localize(L.globals().mods[name],k)
    items=[]
    def add(key,x,y,w,h,text='',**kw):items.append(dict(key=key,x=x,y=y,w=w,h=h,text=text,**kw))
    # Dimensions from installed DMF definitions: category 500px; settings 1000px,
    # right offset180; grid top220; row64; spacing10; group header50+20.
    add('settings_title',740,60,1000,55,tr('mod_name'),font=34,color='gold')
    add('settings_description',740,125,1000,70,tr('mod_description'),font=21,color='muted')
    add('filter',140,180,500,44,{'en':'Search mods','zh-cn':'搜索模组','zh-tw':'搜尋模組'}[lang],fill=True,color='muted')
    add('category_'+name,140,236,500,64,tr('mod_name'),font=24,fill=True,selected=True)
    y=220
    for group in data.options.widgets.values():
        if group.type != 'group':
            add(group.setting_id+'_label',780,y,460,64,tr(group.title),font=23)
            add(group.setting_id,1240,y,500,64,'—',font=24,center=True,fill=True)
            y+=74
            continue
        if group.setting_id == "mortis_competition_group":
            result[lang+"_"+name]=items.copy()
            items=items[:4];y=220
        add('group',740,y,1000,50,tr(group.setting_id),font=27,color='gold');y+=70
        for widget in group.sub_widgets.values():
            title=tr(widget.title)
            add(widget.setting_id+'_label',780,y,460,64,title,font=23)
            if widget.type=='checkbox':
                add(widget.setting_id,1240,y,500,64,{'en':'Enabled' if widget.default_value else 'Disabled','zh-cn':'开启' if widget.default_value else '关闭','zh-tw':'開啟' if widget.default_value else '關閉'}[lang],font=24,checkbox=True,selected=bool(widget.default_value),fill=True)
            elif widget.type=='dropdown':
                option=next(o for o in widget.options.values() if o.value==widget.default_value)
                add(widget.setting_id,1240,y,500,64,tr(option.text),font=24,choice=True,fill=True)
            else:
                add(widget.setting_id+"_track",1240,y+30,360,3,fill=True)
                add(widget.setting_id+"_fill",1240,y+30,max(1,360*widget.default_value/widget.range[2]),3,fill=True,timer=True)
                add(widget.setting_id,1650,y+8,90,48,str(widget.default_value),font=24,center=True,fill=True,input=True)
            y+=74
    result[lang+'_weights']=items
assert result and all(not re.search(r'<ui_\d+>|%[dfs]',i['text']) for items in result.values() for i in items)
layout_output.parent.mkdir(parents=True,exist_ok=True)
layout_output.write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8')
print('Exported',len(result),'localized pages for',PROJECT.name)
