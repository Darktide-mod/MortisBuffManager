from pathlib import Path

import json,re,sys,argparse
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'tests'))
from project_env import CHECKS
from PIL import Image,ImageDraw,ImageFont
parser=argparse.ArgumentParser(description='Render offline UI assets to an explicit release location.')
parser.add_argument('--layouts',type=Path,default=CHECKS/'ui-layouts.json')
parser.add_argument('--output',type=Path,default=ROOT/'publishing')
parser.add_argument('--report',type=Path,default=CHECKS/'ui-images.json')
args=parser.parse_args()
OUT=args.output

layouts=json.loads(args.layouts.read_text(encoding='utf-8'))
fonts={}
def font(n):
    if n not in fonts:fonts[n]=ImageFont.truetype('C:/Windows/Fonts/msyh.ttc',n)
    return fonts[n]
names_en={'chaos_armored_infected':'Armoured Groaner','chaos_lesser_mutated_poxwalker':'Mutated Poxwalker','chaos_mutated_poxwalker':'Mutated Poxwalker','chaos_newly_infected':'Groaner','chaos_poxwalker':'Poxwalker','cultist_assault':'Dreg Stalker','cultist_melee':'Dreg Bruiser','cultist_vanguard':'Dreg Vanguard','renegade_assault':'Scab Stalker','renegade_melee':'Scab Bruiser','renegade_rifleman':'Scab Shooter','renegade_vanguard':'Scab Vanguard'}
names_cn={'chaos_armored_infected':'披甲呻吟者','chaos_lesser_mutated_poxwalker':'变异瘟疫行者','chaos_mutated_poxwalker':'触手瘟疫行者','chaos_newly_infected':'呻吟者','chaos_poxwalker':'瘟疫行者','cultist_assault':'渣滓潜行者','cultist_melee':'渣滓格斗兵','cultist_vanguard':'渣滓先锋','renegade_assault':'血痂潜行者','renegade_melee':'血痂格斗兵','renegade_rifleman':'血痂射手','renegade_vanguard':'血痂先锋'}
from opencc import OpenCC
_converter=OpenCC('s2twp')
def tw(text): return _converter.convert(text)
palette={'gold':(221,194,122),'muted':(151,167,152)}
issues=[];records=[]
for key,specs in layouts.items():
    lang,kind=key.split('_',1)
    name=ROOT.name
    filename={'MortisBuffManager': '01-settings', 'picker':'02-picker', 'realms':'03-realms', 'draft':'04-draft', 'competition':'05-competition', 'weights':'06-kill-settings','diy_mortis':'07-diy-talents','diy_conditions':'08-diy-conditions'}.get(kind,'09-'+kind)+'.'+lang+'.png'
    path=OUT/'images'/filename;path.parent.mkdir(parents=True,exist_ok=True)
    im=Image.new('RGB',(1920,1080),(9,16,13));draw=ImageDraw.Draw(im)
    dmf=kind.endswith('Manager') or kind=='weights'
    title=({'en':'Mod options','zh-cn':'模组选项','zh-tw':'模組選項'} if dmf else {'en':'Local game','zh-cn':'本地游戏','zh-tw':'本地遊戲'})[lang]
    caption=({'en':'Havoc Condition Manager · UI preview','zh-cn':'浩劫词条管理器 · 界面预览','zh-tw':'浩劫詞條管理器 · 介面預覽'} if kind=='diy_conditions' else {'en':'Mortis Buff Manager · UI preview','zh-cn':'死灵 Buff 管理器 · 界面预览','zh-tw':'死靈 Buff 管理器 · 介面預覽'})[lang]
    draw.text((180,65) if dmf else (92,28),title if dmf else caption,font=font(38 if dmf else 26),fill=palette['gold'])
    note={'en':'UI layout preview · Sample configuration · Not a gameplay capture','zh-cn':'界面布局预览 · 示例配置 · 非游戏实拍','zh-tw':'介面佈局預覽 · 範例配置 · 非遊戲實拍'}[lang]
    draw.text((120,1032),note,font=font(18 if lang=='en' else 20),fill=(126,145,132))
    # Each feature page draws its own native panels.
    for item in sorted(specs,key=lambda x:(bool(x.get('overlay')),not bool(x.get('panel')))):
        x,y,w,h=(item[k] for k in ('x','y','w','h'))
        if item.get('fill'):
            bg=(225,185,85) if item.get('timer') else (15,23,19) if item.get('panel') else (51,70,44) if item.get('selected') else (25,35,27)
            draw.rectangle((x,y,x+w-1,y+h-1),fill=bg)
            if not item.get('panel'):draw.line((x,y+h-1,x+w-1,y+h-1),fill=(57,69,50))
        if item.get('selected'):draw.rectangle((x,y,x+2,y+h),fill=palette['gold'])
        if item.get('input'):draw.rectangle((x,y,x+w-1,y+h-1),outline=palette['gold'],width=1)
        if item.get('frame'):draw.rectangle((x,y,x+w-1,y+h-1),outline=(167,146,82),width=1)
        text=item['text']
        if item['key'].startswith('unit_'):
            unit=item['key'][5:]
            text=(names_en if lang=='en' else names_cn).get(unit,text)
            if lang=='zh-tw':text=tw(text)
        if item.get('icon'):
            cx,cy=x+w/2,y+h/2;r=min(w,h)*0.4
            draw.regular_polygon((cx,cy,r),6,rotation=30,outline=palette['gold'],width=2)
            draw.polygon([(cx,cy-r*.55),(cx+r*.35,cy),(cx,cy+r*.55),(cx-r*.35,cy)],outline=palette['gold'],width=2)
        if item.get('panel'):continue
        fs=item.get('font',22);f=font(fs)
        color=(220,133,117) if item.get('danger') else tuple(item['rgb']) if item.get('rgb') else palette.get(item.get('color'),palette['gold'] if item.get('selected') else (222,229,214))
        pad=item.get('text_padding',42 if item.get('checkbox') else 2 if item.get('center') else 12)
        right=item.get('text_right_padding') or (40 if item.get('choice') else 2 if item.get('center') else 12)
        if item.get('checkbox'):
            cx,cy=x+24,y+h/2;draw.rectangle((cx-10,cy-10,cx+10,cy+10),outline=(120,143,119),width=1)
            if item.get('selected'):draw.line((cx-6,cy,cx-1,cy+5,cx+7,cy-6),fill=palette['gold'],width=2)
        if item.get('choice'):
            cx,cy=x+w-21,y+h/2;direction=-1 if item.get('expanded') and not item.get('upwards') else 1
            draw.line((cx-6,cy-direction*3,cx,cy+direction*3,cx+6,cy-direction*3),fill=palette['gold'],width=2)
        # Native Proxima Nova includes the selection symbol; the offline CJK
        # font does not. Draw its check here instead of displaying a missing glyph.
        if text.startswith('\ue001  '):
            cx,cy=x+pad+8,y+fs*.6
            draw.line((cx-6,cy,cx-1,cy+5,cx+7,cy-6),fill=color,width=2)
            text=text[3:];pad+=25
        if not text:continue
        lines=[]
        for para in text.split('\n'):
            line=''
            tokens=para.split(' ') if lang=='en' else list(para)
            for token in tokens:
                candidate=line+(' ' if lang=='en' and line else '')+token
                if line and draw.textlength(candidate,font=f)>w-pad-right:lines.append(line);line=token
                else:line=candidate
            lines.append(line)
        lh=round(fs*1.28);bh=lh*len(lines)
        if bh>h+3:issues.append((key,item['key'],text,bh,h))
        ty=y-1 if item.get('top') else y+(h-bh)/2-1
        for line in lines:
            tx=x+(w-draw.textlength(line,font=f))/2 if item.get('center') else x+pad
            draw.text((tx,ty),line,font=f,fill=color);ty+=lh
    if lang=='en':assert not any(re.search('[\u3400-\u9fff]',i['text']) for i in specs),key
    im.save(path,optimize=True)
    records.append({'mod':name,'language':lang,'file':str(path.relative_to(OUT)).replace('\\','/'),'kind':kind})
assert not issues,issues
if args.report:
    args.report.parent.mkdir(parents=True,exist_ok=True)
    args.report.write_text(json.dumps(records,ensure_ascii=False,indent=2),encoding='utf-8')
print('Rendered',len(records),'UI images; English text and all text bounds checked.')
