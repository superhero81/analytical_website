from pathlib import Path
import numpy as np
import pandas as pd

SEED, CUTOFF = 20260829, pd.Timestamp("2026-07-01")
EMP = Path("output/employee_data_clean.csv")
OUT = Path("output/training_and_development_data_clean.csv")
REPORT = Path("output/training_and_development_cleaning_report.md")
PROGRAMS = {
 "Employee Onboarding":("Onboarding",2,.70,False),"Safety & Compliance":("Compliance",1,.65,True),
 "Equipment Operation":("Technical",2,1.25,True),"Technical Skills":("Technical",2,1.30,True),
 "Quality Management":("Operational Excellence",2,1.10,False),"Cybersecurity Awareness":("Compliance",1,.70,True),
 "Data & BI Skills":("Technical",2,1.35,True),"Secure Coding":("Technical",2,1.40,True),
 "IT Infrastructure":("Technical",2,1.35,True),"Project Management":("Professional Skills",2,1.20,True),
 "Leadership Development":("Leadership",2,1.35,False),"Agile Delivery":("Professional Skills",2,1.15,False),
 "Customer Service":("Customer Skills",1,.90,False),"Communication Skills":("Professional Skills",1,.85,False),
 "Sales Excellence":("Customer Skills",2,1.15,True),"Business Compliance":("Compliance",1,.65,True),
 "Strategic Leadership":("Leadership",2,1.50,False)}
TRAINERS=[f"Internal Trainer {i:02d}" for i in range(1,19)]
PROVIDERS=["NorthStar Learning","SkillForge Institute","DataCraft Academy","Leadership Partners",
           "SafeWorks Institute","ProjectPro Academy","CustomerFirst Training","TechCore Education"]
EXT_LOCS=["EXT-BOS-01","EXT-NYC-01","EXT-CHI-01","EXT-DAL-01"]
LOW_TRAINER="Internal Trainer 17"
MONTH_W={1:.70,2:.92,3:1.18,4:1.20,5:1.10,6:.92,7:.68,8:.72,9:1.18,10:1.24,11:1.05,12:.62}

def manager(t): return any(w in t.lower() for w in ["manager","director","president","ceo","cio"])
def options(p):
 d=p.DepartmentType
 if d=="Production": n,w=["Safety & Compliance","Equipment Operation","Technical Skills","Quality Management","Communication Skills"],[.28,.24,.23,.16,.09]
 elif d=="Sales": n,w=["Sales Excellence","Customer Service","Communication Skills","Project Management","Business Compliance"],[.28,.25,.20,.15,.12]
 elif d=="Software Engineering": n,w=["Secure Coding","Technical Skills","Agile Delivery","Project Management","Cybersecurity Awareness"],[.30,.23,.20,.15,.12]
 elif d=="IT/IS": n,w=["Data & BI Skills","IT Infrastructure","Technical Skills","Project Management","Cybersecurity Awareness"],[.27,.21,.21,.16,.15]
 elif d=="Executive Office": n,w=["Strategic Leadership","Leadership Development","Project Management","Business Compliance","Communication Skills"],[.34,.25,.17,.12,.12]
 else: n,w=["Business Compliance","Communication Skills","Project Management","Customer Service","Data & BI Skills"],[.25,.23,.20,.15,.17]
 if manager(p.Title) and "Leadership Development" not in n: n.append("Leadership Development"); w=[x*.78 for x in w]+[.22]
 return n,w

def delivery(r,p,program):
 q=[.68,.14,.18] if p.DepartmentType=="Production" else [.25,.18,.57]
 if program=="Equipment Operation": q=[.64,.10,.26]
 elif program=="Technical Skills": q=[.50,.16,.34]
 elif program in {"Data & BI Skills","Cybersecurity Awareness","Business Compliance"}: q=[.22,.13,.65]
 elif program=="Safety & Compliance": q=[.72,.12,.16]
 elif "Leadership" in program: q=[.50,.22,.28]
 return str(r.choice(["In-person","Hybrid","Online"],p=q))
def tr_type(r,program):
 q={"Strategic Leadership":.65,"Leadership Development":.45,"Project Management":.40,
    "Data & BI Skills":.35,"Secure Coding":.35,"Technical Skills":.30}.get(program,.16)
 return "External" if r.random()<q else "Internal"
def date_pick(r,lo,hi):
 days=pd.date_range(lo,hi); w=np.array([MONTH_W[x.month]*(1 if x.weekday()<5 else .32) for x in days])
 return pd.Timestamp(r.choice(days.to_numpy(),p=w/w.sum()))

def outcome_probs(p,program,mode,trainer,date,effect):
 cancel=.045+(.018 if p.EmployeeClassificationType=="Temporary" else 0)+(.010 if date.month in {6,11,12} else 0)-(.020 if program=="Employee Onboarding" else 0)
 complete=.895+effect
 complete-=.075 if p.Title=="Production Technician I" else (.045 if p.Title=="Production Technician II" else 0)
 if p.DepartmentType=="Production" and "Technician" not in p.Title: complete-=.025
 if p.EmployeeClassificationType=="Temporary": complete-=.035
 complete+={"Employee Onboarding":.035,"Safety & Compliance":.025,"Project Management":-.055,
           "Leadership Development":-.025,"Agile Delivery":-.045,"Strategic Leadership":-.030}.get(program,0)
 if program=="Equipment Operation": complete+={"In-person":.085,"Hybrid":-.015,"Online":-.145}[mode]
 elif program=="Technical Skills": complete+={"In-person":.045,"Hybrid":.005,"Online":-.070}[mode]
 elif program=="Data & BI Skills": complete+={"Online":.075,"Hybrid":.020,"In-person":-.085}[mode]
 elif program in {"Cybersecurity Awareness","Business Compliance"}: complete+={"Online":.045,"Hybrid":.010,"In-person":-.045}[mode]
 complete+=-.025 if date.month in {6,11} else (-.040 if date.month in {7,8,12} else (.012 if date.month in {3,4} else 0))
 if trainer==LOW_TRAINER and mode=="In-person": complete-=.105
 return np.clip(cancel,.02,.10),np.clip(complete,.64,.97)

def add(r,rows,num,p,date,program,effect):
 cat,base,mult,exam=PROGRAMS[program]
 dur=base+int(r.random()<.18 and program not in {"Employee Onboarding","Safety & Compliance","Cybersecurity Awareness","Business Compliance"})
 mode,typ=delivery(r,p,program),tr_type(r,program)
 trainer=str(r.choice(PROVIDERS if typ=="External" else TRAINERS))
 cp,fp=outcome_probs(p,program,mode,trainer,date,effect)
 status="Cancelled" if r.random()<cp else ("Completed" if r.random()<fp else "Incomplete")
 if not exam: result="Not Applicable"
 elif status=="Cancelled": result="Not Taken"
 elif status=="Incomplete": result="Failed" if r.random()<.62 else "Not Taken"
 else:
  pp=.925-(.075 if program=="Equipment Operation" and mode=="Online" else 0)+(.025 if program=="Data & BI Skills" and mode=="Online" else 0)-(.055 if trainer==LOW_TRAINER and mode=="In-person" else 0)
  result="Passed" if r.random()<np.clip(pp,.74,.97) else "Failed"
 loc="Online" if mode=="Online" else (str(r.choice(EXT_LOCS)) if typ=="External" else p.LocationCode)
 daily={"Online":85.,"Hybrid":145.,"In-person":205.}[mode]
 cost=round(dur*daily*mult*(1.65 if typ=="External" else 1)*r.uniform(.88,1.12),2)
 rows.append({"TrainingRecordID":f"TRN-{num:06d}","EmpID":int(p.EmpID),"TrainingDate":date.strftime("%Y-%m-%d"),
  "TrainingProgramName":program,"TrainingCategory":cat,"TrainingType":typ,"DeliveryMode":mode,"LocationCode":loc,
  "TrainerOrProvider":trainer,"TrainingDurationDays":dur,"TrainingCostUSD":cost,"CompletionStatus":status,"TrainingResult":result})
 return num+1

def rates(df,groups,minimum=0):
 z=df.groupby(groups,dropna=False).agg(records=("TrainingRecordID","size"),
  completed=("CompletionStatus",lambda s:(s=="Completed").sum()),incomplete=("CompletionStatus",lambda s:(s=="Incomplete").sum()),
  cancelled=("CompletionStatus",lambda s:(s=="Cancelled").sum())).reset_index()
 z=z[z.records>=minimum].copy(); den=z.completed+z.incomplete
 z["completion_rate"]=z.completed/den; z["incomplete_rate"]=z.incomplete/den; z["cancellation_rate"]=z.cancelled/z.records
 return z

def markdown(df):
 def cell(x):
  if isinstance(x,(float,np.floating)): return f"{x:.3f}"
  return str(x).replace("|","\\|")
 lines=["| "+" | ".join(map(str,df.columns))+" |","|"+"|".join(["---"]*len(df.columns))+"|"]
 lines += ["| "+" | ".join(cell(x) for x in row)+" |" for row in df.itertuples(index=False,name=None)]
 return "\n".join(lines)

def main():
 r=np.random.default_rng(SEED); emp=pd.read_csv(EMP)
 emp["StartDate"]=pd.to_datetime(emp.StartDate); emp["ExitDate"]=pd.to_datetime(emp.ExitDate,errors="coerce")
 effects=dict(zip(emp.EmpID,r.normal(0,.032,len(emp)))); rows=[]; num=1
 for _,p in emp.iterrows():
  start=p.StartDate; end=p.ExitDate if pd.notna(p.ExitDate) else CUTOFF; tenure=(end-start).days
  if tenure<2: continue
  if tenure>=12:
   dt=start+pd.Timedelta(days=int(r.integers(10,min(45,tenure-1)+1)))
   num=add(r,rows,num,p,dt,"Employee Onboarding",effects[p.EmpID])
  names,weights=options(p)
  for year in range(start.year,end.year+1):
   lo=max(start+pd.Timedelta(days=2),pd.Timestamp(year,1,5)); hi=min(end-pd.Timedelta(days=3),pd.Timestamp(year,12,20),CUTOFF-pd.Timedelta(days=3))
   if hi<lo: continue
   for _ in range(int(r.random()<.64)+int(r.random()<.17)):
    program=str(r.choice(names,p=weights)); latest=hi-pd.Timedelta(days=PROGRAMS[program][1])
    if latest>=lo: num=add(r,rows,num,p,date_pick(r,lo,latest),program,effects[p.EmpID])
 training=pd.DataFrame(rows).sort_values(["TrainingDate","EmpID","TrainingRecordID"]).reset_index(drop=True)
 training["TrainingRecordID"]=[f"TRN-{i:06d}" for i in range(1,len(training)+1)]
 OUT.parent.mkdir(parents=True,exist_ok=True); training.to_csv(OUT,index=False,encoding="utf-8")
 merged=training.merge(emp[["EmpID","StartDate","ExitDate","DepartmentType","Title","EmployeeClassificationType"]],on="EmpID",how="left",validate="many_to_one")
 merged["TrainingDate"]=pd.to_datetime(merged.TrainingDate); end=merged.TrainingDate+pd.to_timedelta(merged.TrainingDurationDays-1,unit="D")
 valid=(merged.TrainingDate>=merged.StartDate)&(merged.ExitDate.isna()|(end<=merged.ExitDate))&(end<=CUTOFF)
 exam=merged.TrainingProgramName.map(lambda x:PROGRAMS[x][3])
 bad=((~exam&(merged.TrainingResult!="Not Applicable"))|(exam&(merged.TrainingResult=="Not Applicable"))|
      ((merged.CompletionStatus=="Cancelled")&(merged.TrainingResult=="Passed"))|
      ((merged.CompletionStatus=="Completed")&exam&~merged.TrainingResult.isin(["Passed","Failed"])))
 wm=merged.assign(Month=merged.TrainingDate.dt.to_period("M")); monthly=rates(wm,["Month"])
 monthly["participants"]=monthly.Month.map(wm.groupby("Month").EmpID.nunique())
 active=[]
 for period in monthly.Month:
  ms,me=period.start_time,min(period.end_time.normalize(),CUTOFF)
  active.append(int(((emp.StartDate<=me)&(emp.ExitDate.isna()|(emp.ExitDate>=ms))).sum()))
 monthly["active_employees"]=active; monthly["participation_rate"]=monthly.participants/monthly.active_employees
 overall=rates(merged.assign(All="All"),["All"]).iloc[0]
 titles=rates(merged,["Title"],80).sort_values("completion_rate")
 programs=rates(merged,["TrainingProgramName"],30).sort_values("completion_rate")
 comparable=rates(merged,["TrainingProgramName","DeliveryMode"],40).sort_values(["TrainingProgramName","DeliveryMode"])
 trainers=rates(merged[merged.DeliveryMode=="In-person"],["TrainerOrProvider"],100).sort_values("completion_rate")
 checks={"rows":len(training),"unique_training_record_id":training.TrainingRecordID.nunique(),
  "unknown_employee_id":int(merged.StartDate.isna().sum()),"training_outside_employment":int((~valid).sum()),
  "duplicate_training_record_id":int(training.TrainingRecordID.duplicated().sum()),
  "invalid_program_category":int((merged.TrainingCategory!=merged.TrainingProgramName.map(lambda x:PROGRAMS[x][0])).sum()),
  "invalid_completion_result_pair":int(bad.sum()),"online_location_mismatch":int(((merged.DeliveryMode=="Online")!=(merged.LocationCode=="Online")).sum()),
  "negative_or_zero_cost":int((training.TrainingCostUSD<=0).sum())}
 cols=["records","completed","incomplete","cancelled","completion_rate","incomplete_rate","cancellation_rate"]
 costs=training.groupby("DeliveryMode").TrainingCostUSD.mean().round(2).to_dict()
 report=f"""# Training and development – generálási és validációs riport

## Adatmodell és összesített eredmény

- Megtartott séma: **{len(training.columns)} oszlop**, változatlan oszlopnevekkel.
- Képzési rekordok: **{len(training):,}**; résztvevő munkavállalók: **{training.EmpID.nunique():,}**.
- Időszak: **{training.TrainingDate.min()} – {training.TrainingDate.max()}**.
- Teljesítési arány: Completed / (Completed + Incomplete); a Cancelled nincs a nevezőben.
- Összesített teljesítési arány: **{overall.completion_rate:.1%}**.
- Összesített félbehagyási arány: **{overall.incomplete_rate:.1%}**; törlési arány: **{overall.cancellation_rate:.1%}**.
- Átlagos költség megvalósítási mód szerint: **{costs}**.

## Szándékosan beépített elemzési történetek

1. A Production Technician I–II, Production és Temporary csoportok mérsékelten alacsonyabb befejezési esélyt kapnak. Védett tulajdonság nincs a szabályokban.
2. A Project Management és Agile Delivery gyakrabban marad félbe; az onboarding és compliance programok stabilabbak.
3. Az Equipment Operation és Technical Skills jelenléti formában jobb; a Data & BI Skills, Cybersecurity Awareness és Business Compliance online formában jobb.
4. {LOW_TRAINER} többféle jelenléti programot tart, de nála mérsékelten alacsonyabb a befejezési és vizsgasiker-esély.
5. Minden hatás valószínűségi; egyéni és rekordszintű szórás marad.
6. A részvétel tavasszal és ősszel magasabb, nyáron és év végén alacsonyabb.

## Munkaköri mintázatok (legalább 80 rekord)

{markdown(titles[["Title"]+cols])}

## Program szerinti mintázatok

{markdown(programs[["TrainingProgramName"]+cols])}

## Azonos programon belüli forma-összehasonlítás (legalább 40 rekord/cella)

{markdown(comparable[["TrainingProgramName","DeliveryMode"]+cols])}

## Jelenléti oktatói mintázatok (legalább 100 rekord)

{markdown(trainers[["TrainerOrProvider"]+cols])}

## Havi részvételi, teljesítési, félbehagyási és törlési mutatók

{markdown(monthly[["Month","records","participants","active_employees","participation_rate","completion_rate","incomplete_rate","cancellation_rate"]])}

## Automatikus ellenőrzések

"""+"\n".join(f"- {k}: {v}" for k,v in checks.items())+"\n"
 REPORT.write_text(report,encoding="utf-8"); print(report[:5000])

if __name__=="__main__": main()
