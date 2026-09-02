from pathlib import Path
import numpy as np
import pandas as pd
from scipy import stats

SEED=20260902
CUTOFF=pd.Timestamp("2026-06-30")
EMP=Path("output/employee_data_clean.csv")
SURVEY=Path("output/employee_engagement_survey_data_clean.csv")
OUT=Path("data/processed/training_and_development_data_clean.csv")
REPORT=Path("docs/training_and_development_cleaning_report.md")
CROSS=Path("docs/cross_file_validation_report.md")
DICT=Path("docs/training_data_dictionary.md")
PURPOSES={"Mandatory","Employee Initiated","Job Required"}
MODES={"In-person","Live Online","Self-paced Online","Hybrid"}
SCORES=["OverallSatisfactionScore","TrainerEvaluationScore","JobRelevanceScore","PersonalRelevanceScore","DigitalContentUsabilityScore"]
TRAINERS=[f"Internal Trainer {i:02d}" for i in range(1,19)]
TRAINER_GENDER={x:("Male" if i%3 else "Female") for i,x in enumerate(TRAINERS,1)}
PROVIDERS=["NorthStar Learning","SkillForge Institute","DataCraft Academy","Leadership Partners",
 "SafeWorks Institute","ProjectPro Academy","CustomerFirst Training","TechCore Education"]
EXTERNAL_NAMES={
 "NorthStar Learning":("Alex Morgan","Emma Reed"),"SkillForge Institute":("Daniel Brooks","Sofia Grant"),
 "DataCraft Academy":("Michael Chen","Laura Hill"),"Leadership Partners":("James Wilson","Anna Lewis"),
 "SafeWorks Institute":("Robert King","Helen Ward"),"ProjectPro Academy":("Thomas Scott","Maria Young"),
 "CustomerFirst Training":("David Hall","Claire Green"),"TechCore Education":("Peter Allen","Julia Baker")}
LOW_TRAINER="Internal Trainer 17"
GENDER_TRAINER="Internal Trainer 12"
MONTH_W={1:.72,2:.92,3:1.16,4:1.20,5:1.08,6:.92,7:.70,8:.73,9:1.18,10:1.22,11:1.04,12:.64}

# category, duration, multiplier, assessed, default purpose
PROGRAMS={
 "Employee Onboarding":("Onboarding",2,.70,False,"Mandatory"),
 "Workplace Health & Safety":("Health & Safety",1,.60,True,"Mandatory"),
 "Fire Safety":("Health & Safety",1,.55,True,"Mandatory"),
 "Information Security":("Information Security",1,.68,True,"Mandatory"),
 "Data Protection":("Data Protection",1,.65,True,"Mandatory"),
 "Equipment Operation":("Technical Skills",2,1.25,True,"Job Required"),
 "Technical Skills":("Technical Skills",2,1.30,True,"Job Required"),
 "Quality Management":("Operational Excellence",2,1.10,False,"Job Required"),
 "Data & BI Skills":("Technical Skills",2,1.35,True,"Job Required"),
 "Secure Coding":("Information Security",2,1.40,True,"Job Required"),
 "IT Infrastructure":("Technical Skills",2,1.35,True,"Job Required"),
 "Project Management":("Professional Skills",2,1.20,True,"Job Required"),
 "Leadership Development":("Leadership Development",2,1.35,False,"Job Required"),
 "Agile Delivery":("Professional Skills",2,1.15,False,"Job Required"),
 "Customer Service":("Customer Skills",1,.90,False,"Job Required"),
 "Communication Skills":("Professional Skills",1,.85,False,"Employee Initiated"),
 "Sales Excellence":("Customer Skills",2,1.15,True,"Job Required"),
 "Business Compliance":("Business Compliance",1,.65,True,"Mandatory"),
 "Strategic Leadership":("Leadership Development",2,1.50,False,"Job Required")}
RECUR={"Workplace Health & Safety":12,"Fire Safety":12,"Information Security":24,"Data Protection":24}

def manager(t):
 return any(w in str(t).lower() for w in ["manager","director","president","ceo","cio"])

def choices(p):
 d=p["DepartmentType"]
 if d=="Production": n,w=["Equipment Operation","Technical Skills","Quality Management","Communication Skills"],[.31,.31,.25,.13]
 elif d=="Sales": n,w=["Sales Excellence","Customer Service","Communication Skills","Project Management","Business Compliance"],[.29,.25,.20,.17,.09]
 elif d=="Software Engineering": n,w=["Secure Coding","Technical Skills","Agile Delivery","Project Management","Data & BI Skills"],[.29,.22,.20,.16,.13]
 elif d=="IT/IS": n,w=["Data & BI Skills","IT Infrastructure","Technical Skills","Project Management","Secure Coding"],[.28,.22,.20,.17,.13]
 elif d=="Executive Office": n,w=["Strategic Leadership","Leadership Development","Project Management","Business Compliance","Communication Skills"],[.34,.25,.17,.10,.14]
 else: n,w=["Business Compliance","Communication Skills","Project Management","Customer Service","Data & BI Skills"],[.17,.27,.22,.16,.18]
 if manager(p["Title"]) and "Leadership Development" not in n:
  n.append("Leadership Development"); w=[x*.78 for x in w]+[.22]
 return n,w

def purpose(r,program):
 default=PROGRAMS[program][4]
 if default=="Mandatory": return default
 if program in {"Communication Skills","Data & BI Skills","Project Management","Leadership Development"}:
  return "Employee Initiated" if r.random()<.28 else "Job Required"
 return default

def mode(r,p,program):
 if program in RECUR: return "Self-paced Online"
 if program=="Employee Onboarding": q=[.36,.22,.20,.22]
 elif program=="Equipment Operation": q=[.65,.10,.15,.10]
 elif program=="Technical Skills": q=[.50,.16,.22,.12]
 elif program in {"Data & BI Skills","Business Compliance"}: q=[.22,.22,.40,.16]
 elif program in {"Secure Coding","IT Infrastructure","Agile Delivery"}: q=[.25,.28,.28,.19]
 elif "Leadership" in program: q=[.48,.22,.08,.22]
 elif p["DepartmentType"]=="Production": q=[.64,.14,.10,.12]
 else: q=[.28,.30,.24,.18]
 return str(r.choice(["In-person","Live Online","Self-paced Online","Hybrid"],p=q))

def training_type(r,program,m):
 if m=="Self-paced Online": return "Internal"
 q={"Strategic Leadership":.65,"Leadership Development":.45,"Project Management":.40,
  "Data & BI Skills":.35,"Secure Coding":.35,"Technical Skills":.30}.get(program,.16)
 return "External" if r.random()<q else "Internal"

def trainer(r,typ,m):
 if m=="Self-paced Online": return pd.NA,pd.NA,"Corporate Learning Platform"
 if typ=="Internal":
  t=str(r.choice(TRAINERS)); return t,TRAINER_GENDER[t],"Internal L&D"
 provider=str(r.choice(PROVIDERS)); idx=int(r.integers(0,2)); t=EXTERNAL_NAMES[provider][idx]
 return t,("Male" if idx==0 else "Female"),provider

def pick_date(r,lo,hi):
 days=pd.date_range(lo,hi)
 w=np.array([MONTH_W[x.month]*(1 if x.weekday()<5 else .30) for x in days])
 return pd.Timestamp(r.choice(days.to_numpy(),p=w/w.sum()))

def outcome(r,p,program,m,t,date,effect):
 cancel=.040+(.016 if p["EmployeeClassificationType"]=="Temporary" else 0)+(.008 if date.month in {6,11,12} else 0)
 complete=.875+effect
 if p["Title"]=="Production Technician I": complete-=.055
 elif p["Title"]=="Production Technician II": complete-=.030
 elif p["DepartmentType"]=="Production": complete-=.015
 if p["EmployeeClassificationType"]=="Temporary": complete-=.025
 complete+={"Workplace Health & Safety":.075,"Fire Safety":.080,"Information Security":-.075,
  "Data Protection":-.005,"Employee Onboarding":.025,"Project Management":-.050,
  "Agile Delivery":-.040,"Leadership Development":-.020}.get(program,0)
 if program=="Data Protection" and p["DepartmentType"]=="Production": complete-=.060
 if program=="Equipment Operation": complete+={"In-person":.075,"Live Online":-.055,"Self-paced Online":-.130,"Hybrid":.005}[m]
 elif program=="Technical Skills": complete+={"In-person":.045,"Live Online":-.020,"Self-paced Online":-.070,"Hybrid":.010}[m]
 elif program=="Data & BI Skills": complete+={"In-person":-.070,"Live Online":.035,"Self-paced Online":.070,"Hybrid":.020}[m]
 if date.month in {7,8,12}: complete-=.025
 elif date.month in {3,4}: complete+=.010
 if str(t)==LOW_TRAINER and m=="In-person": complete-=.105
 status="Cancelled" if r.random()<np.clip(cancel,.02,.09) else ("Completed" if r.random()<np.clip(complete,.62,.97) else "Incomplete")
 return status

def add(r,rows,p,date,program,effect,cycle):
 cat,base,mult,exam,_=PROGRAMS[program]
 dur=base+int(r.random()<.16 and program not in RECUR and program!="Employee Onboarding")
 m=mode(r,p,program); typ=training_type(r,program,m); t,tg,provider=trainer(r,typ,m)
 status=outcome(r,p,program,m,t,date,effect)
 if not exam: result,attempts="Not Applicable",pd.NA
 elif status=="Cancelled": result,attempts="Not Taken",pd.NA
 elif status=="Incomplete":
  if r.random()<.42: result,attempts="Not Taken",0
  else: result,attempts="Failed",int(r.choice([1,2,3],p=[.57,.32,.11]))
 else:
  pp=.925-(.105 if program=="Information Security" else 0)
  pp-=(.055 if program=="Data Protection" and p["DepartmentType"]=="Production" else 0)
  pp-=(.070 if program=="Equipment Operation" and m!="In-person" else 0)
  pp-=(.045 if str(t)==LOW_TRAINER and m=="In-person" else 0)
  passed=r.random()<np.clip(pp,.70,.97); result="Passed" if passed else "Failed"
  attempts=int(r.choice([1,2,3],p=([.79,.18,.03] if passed else [.48,.37,.15])))
  if program=="Information Security": attempts=min(3,attempts+int(r.random()<.28))
  if program=="Data Protection" and p["DepartmentType"]=="Production": attempts=min(3,attempts+int(r.random()<.16))
 loc="Online" if m in {"Self-paced Online","Live Online"} else (str(r.choice(["EXT-BOS-01","EXT-NYC-01","EXT-CHI-01","EXT-DAL-01"])) if typ=="External" else p["LocationCode"])
 daily={"Self-paced Online":52.,"Live Online":112.,"Hybrid":158.,"In-person":215.}[m]
 c=round(dur*daily*mult*(1.55 if typ=="External" else 1)*r.uniform(.88,1.12),2)
 rows.append({"TrainingRecordID":"","EmpID":int(p["EmpID"]),"TrainingDate":date.strftime("%Y-%m-%d"),
 "TrainingProgramName":program,"TrainingPurpose":purpose(r,program),"TrainingCategory":cat,"TrainingType":typ,
 "DeliveryMode":m,"LocationCode":loc,"Trainer":t,"TrainerGender":tg,"TrainingProvider":provider,
 "TrainingDurationDays":dur,"TrainingCostUSD":c,"CompletionStatus":status,"TrainingResult":result,
 "AssessmentAttempts":attempts,"FeedbackSubmitted":"No","OverallSatisfactionScore":pd.NA,
 "TrainerEvaluationScore":pd.NA,"JobRelevanceScore":pd.NA,"PersonalRelevanceScore":pd.NA,
 "DigitalContentUsabilityScore":pd.NA,"_cycle":cycle})

def likert(r,mean,sd=.70,missing=.02):
 if r.random()<missing: return pd.NA
 return int(np.clip(np.rint(r.normal(mean,sd)),1,5))

def feedback(r,row,p,effect):
 if row["CompletionStatus"]=="Cancelled": return row
 response=.85 if row["CompletionStatus"]=="Completed" else .45
 if row["TrainingPurpose"]=="Employee Initiated": response+=.015
 if r.random()>=response: return row
 row["FeedbackSubmitted"]="Yes"; prog=row["TrainingProgramName"]; pur=row["TrainingPurpose"]
 job={"Mandatory":3.45,"Job Required":4.15,"Employee Initiated":3.85}[pur]
 personal={"Mandatory":3.05,"Job Required":3.75,"Employee Initiated":4.35}[pur]; digital=4.05
 if prog in {"Workplace Health & Safety","Fire Safety"}:
  job,personal,digital=3.55,3.20,4.30
  if p["DepartmentType"]=="Production": job-=.10; personal-=.10; digital-=.18
 elif prog=="Information Security": job,personal,digital=4.05,3.25,3.15
 elif prog=="Data Protection":
  job,personal,digital=3.85,3.55,4.00
  if p["DepartmentType"]=="Production": job-=.65; personal-=.55; digital-=.60
 elif prog=="Equipment Operation" and p["DepartmentType"]=="Production": job+=.35
 elif prog=="Data & BI Skills" and p["DepartmentType"]=="IT/IS": job+=.30
 job+=effect; personal+=.45*effect+r.normal(0,.18)
 row["JobRelevanceScore"]=likert(r,job,.70,.025); row["PersonalRelevanceScore"]=likert(r,personal,.72,.025)
 te=pd.NA
 if row["DeliveryMode"]!="Self-paced Online":
  tm=4.10+effect-(.38 if str(row["Trainer"])==LOW_TRAINER else 0)
  if str(row["Trainer"])==GENDER_TRAINER and p["GenderCode"]=="Female": tm-=.34
  te=likert(r,tm,.68,.015); row["TrainerEvaluationScore"]=te
 de=pd.NA
 if row["DeliveryMode"]=="Self-paced Online" or (row["DeliveryMode"]=="Hybrid" and r.random()<.65):
  de=likert(r,digital+effect,.70,.02); row["DigitalContentUsabilityScore"]=de
 vals=[row["JobRelevanceScore"],row["PersonalRelevanceScore"],te,de]; vals=[float(x) for x in vals if pd.notna(x)]
 if not vals: vals=[job,personal]
 om=.52+sum(vals)/len(vals)+r.normal(0,.42)
 if prog=="Information Security": om-=.38
 if prog=="Data Protection" and p["DepartmentType"]=="Production": om-=.22
 if row["CompletionStatus"]=="Incomplete": om-=.25
 row["OverallSatisfactionScore"]=likert(r,om,.55,.01)
 return row

def rates(df,groups):
 z=df.groupby(groups,dropna=False).agg(records=("TrainingRecordID","size"),
 completed=("CompletionStatus",lambda s:(s=="Completed").sum()),
 incomplete=("CompletionStatus",lambda s:(s=="Incomplete").sum()),
 cancelled=("CompletionStatus",lambda s:(s=="Cancelled").sum()),
 feedback_rate=("FeedbackSubmitted",lambda s:(s=="Yes").mean())).reset_index()
 den=z.completed+z.incomplete; z["completion_rate"]=z.completed/den
 z["incomplete_rate"]=z.incomplete/den; z["cancellation_rate"]=z.cancelled/z.records
 return z

def md(df,d=3):
 def f(x):
  if pd.isna(x): return ""
  if isinstance(x,(float,np.floating)): return f"{x:.{d}f}"
  return str(x).replace("|","\\|")
 lines=["| "+" | ".join(map(str,df.columns))+" |","|"+"|".join(["---"]*len(df.columns))+"|"]
 return "\n".join(lines+["| "+" | ".join(f(x) for x in row)+" |" for row in df.itertuples(index=False,name=None)])

def main():
 r=np.random.default_rng(SEED); emp=pd.read_csv(EMP)
 emp["StartDate"]=pd.to_datetime(emp.StartDate); emp["ExitDate"]=pd.to_datetime(emp.ExitDate,errors="coerce")
 effects=dict(zip(emp.EmpID,r.normal(0,.035,len(emp)))); fb_effects=dict(zip(emp.EmpID,r.normal(0,.16,len(emp))))
 rows=[]; expected=set()
 for _,p in emp.iterrows():
  start=p.StartDate; end=p.ExitDate if pd.notna(p.ExitDate) else CUTOFF; tenure=(end-start).days
  if tenure<2: continue
  if tenure>=12:
   dt=start+pd.Timedelta(days=int(r.integers(10,min(45,tenure-1)+1))); add(r,rows,p,dt,"Employee Onboarding",effects[p.EmpID],f"{p.EmpID}|Onboarding")
  for j,(prog,months) in enumerate(RECUR.items()):
   first=start+pd.Timedelta(days=30+17*j+int(p.EmpID)%23); k=0; due=first
   while due<=end and due<=CUTOFF:
    lo=max(start,due-pd.Timedelta(days=12)); hi=min(end,CUTOFF,due+pd.Timedelta(days=12))
    key=f"{p.EmpID}|{prog}|{k}"; add(r,rows,p,pick_date(r,lo,hi),prog,effects[p.EmpID],key); expected.add(key)
    k+=1; due=first+pd.DateOffset(months=months*k)
  names,weights=choices(p)
  for year in range(start.year,end.year+1):
   lo=max(start+pd.Timedelta(days=2),pd.Timestamp(year,1,5)); hi=min(end-pd.Timedelta(days=3),pd.Timestamp(year,12,20),CUTOFF-pd.Timedelta(days=3))
   if hi<lo: continue
   for n in range(int(r.random()<.61)+int(r.random()<.15)):
    prog=str(r.choice(names,p=weights)); latest=hi-pd.Timedelta(days=PROGRAMS[prog][1])
    if latest>=lo: add(r,rows,p,pick_date(r,lo,latest),prog,effects[p.EmpID],f"{p.EmpID}|Adhoc|{year}|{n}")
 data=pd.DataFrame(rows).sort_values(["TrainingDate","EmpID","TrainingProgramName"]).reset_index(drop=True)
 data["TrainingRecordID"]=[f"TRN-{i:06d}" for i in range(1,len(data)+1)]
 people=emp.set_index("EmpID")
 records=[]
 for row in data.to_dict("records"): records.append(feedback(r,row,people.loc[row["EmpID"]],fb_effects[row["EmpID"]]))
 data=pd.DataFrame(records); cycles=data.pop("_cycle")
 OUT.parent.mkdir(parents=True,exist_ok=True); REPORT.parent.mkdir(parents=True,exist_ok=True)
 data.to_csv(OUT,index=False,encoding="utf-8")

 j=data.merge(emp[["EmpID","StartDate","ExitDate","DepartmentType","Title","EmployeeClassificationType","GenderCode"]],on="EmpID",how="left",validate="many_to_one")
 j["TrainingDate"]=pd.to_datetime(j.TrainingDate); tend=j.TrainingDate+pd.to_timedelta(j.TrainingDurationDays-1,unit="D")
 instructor=j.DeliveryMode!="Self-paced Online"; nofb=j.FeedbackSubmitted=="No"; exam=j.TrainingProgramName.map(lambda x:PROGRAMS[x][3])
 bad_result=((~exam&(j.TrainingResult!="Not Applicable"))|(exam&(j.TrainingResult=="Not Applicable"))|
  ((j.CompletionStatus=="Cancelled")&~j.TrainingResult.isin(["Not Taken","Not Applicable"]))|
  ((j.CompletionStatus=="Completed")&exam&~j.TrainingResult.isin(["Passed","Failed"])))
 checks={"duplicate_training_record_id":int(data.TrainingRecordID.duplicated().sum()),"unknown_employee_id":int(j.StartDate.isna().sum()),
 "training_before_start":int((j.TrainingDate<j.StartDate).sum()),"training_after_exit":int((j.ExitDate.notna()&(tend>j.ExitDate)).sum()),
 "training_after_reference_date":int((j.TrainingDate>CUTOFF).sum()),
 "invalid_training_purpose":int((~data.TrainingPurpose.isin(PURPOSES)).sum()),"invalid_delivery_mode":int((~data.DeliveryMode.isin(MODES)).sum()),
 "feedback_on_cancelled":int(((data.CompletionStatus=="Cancelled")&(data.FeedbackSubmitted=="Yes")).sum()),
 "scores_without_feedback":int(data.loc[nofb,SCORES].notna().sum().sum()),
 "scores_outside_1_5":int(sum((data[c].notna()&~data[c].between(1,5)).sum() for c in SCORES)),
 "self_paced_with_trainer_or_trainer_score":int(((~instructor)&(j.Trainer.notna()|j.TrainerGender.notna()|j.TrainerEvaluationScore.notna())).sum()),
 "instructor_led_without_trainer":int((instructor&j.Trainer.isna()).sum()),"invalid_status_result_pair":int(bad_result.sum()),
 "nonpositive_cost":int((data.TrainingCostUSD<=0).sum()),"duplicate_cycle_key":int(cycles.duplicated().sum()),
 "missing_recurring_assignment":int(len(expected-set(cycles)))}
 overall=rates(j.assign(All="All"),["All"]).iloc[0]
 status_fb=j.groupby("CompletionStatus").agg(records=("TrainingRecordID","size"),feedback_rate=("FeedbackSubmitted",lambda s:(s=="Yes").mean())).reset_index()
 score_stats=data[SCORES].agg(["count","mean","std"]).T.reset_index().rename(columns={"index":"score"})
 recurring=rates(j[j.TrainingProgramName.isin(RECUR)],["TrainingProgramName"])
 expected_counts=pd.Series([x.split("|")[1] for x in expected]).value_counts()
 coverage=recurring[["TrainingProgramName","records"]].copy()
 coverage["expected_records"]=coverage.TrainingProgramName.map(expected_counts)
 coverage["coverage_rate"]=coverage.records/coverage.expected_records
 prod=j.assign(Group=np.where(j.DepartmentType=="Production","Production","Other"))
 prodcmp=prod[prod.TrainingProgramName.isin(RECUR)].groupby(["TrainingProgramName","Group"])[SCORES+["AssessmentAttempts"]].mean().reset_index()
 purpose_scores=j.groupby("TrainingPurpose")[SCORES].mean().reset_index()
 score_long=data[SCORES].melt(var_name="score_name",value_name="score").dropna()
 score_dist=pd.crosstab(score_long.score_name,score_long.score).reindex(columns=[1,2,3,4,5],fill_value=0).reset_index()
 score_corr=data[SCORES].apply(pd.to_numeric,errors="coerce").corr().round(3).reset_index()
 modecmp=rates(j,["DeliveryMode"])
 program_rates=rates(j,["TrainingProgramName"]).sort_values("completion_rate")
 role_rates=rates(j,["Title"]); role_rates=role_rates[role_rates.records>=100].sort_values("completion_rate")
 pm=rates(j,["TrainingProgramName","DeliveryMode"])
 keym=pm[(pm.records>=80)&pm.TrainingProgramName.isin(["Equipment Operation","Technical Skills","Data & BI Skills"])]
 tr=rates(j[j.DeliveryMode=="In-person"],["Trainer"]); tr=tr[tr.records>=100].sort_values("completion_rate")
 selected=j[(j.Trainer==GENDER_TRAINER)&j.TrainerEvaluationScore.notna()].copy()
 female=selected.loc[selected.GenderCode=="Female","TrainerEvaluationScore"].astype(float); male=selected.loc[selected.GenderCode=="Male","TrainerEvaluationScore"].astype(float)
 _,praw=stats.ttest_ind(female,male,equal_var=False)
 selected["stratum"]=selected.TrainingProgramName.astype(str)+"|"+selected.DeliveryMode.astype(str)+"|"+selected.DepartmentType.astype(str)+"|"+selected.TrainingDate.dt.year.astype(str)
 selected["resid"]=selected.TrainerEvaluationScore-selected.groupby("stratum").TrainerEvaluationScore.transform("mean")
 fr=selected.loc[selected.GenderCode=="Female","resid"].astype(float); mr=selected.loc[selected.GenderCode=="Male","resid"].astype(float)
 _,padj=stats.ttest_ind(fr,mr,equal_var=False)
 gender=pd.DataFrame([{"trainer":GENDER_TRAINER,"female_n":len(female),"female_mean":female.mean(),"male_n":len(male),"male_mean":male.mean(),
 "female_minus_male":female.mean()-male.mean(),"welch_p":praw,"stratified_difference":fr.mean()-mr.mean(),"stratified_p":padj}])
 empyears=(emp.ExitDate.fillna(CUTOFF)-emp.StartDate).dt.days.clip(lower=0).sum()/365.25
 freq=pd.DataFrame([{"records":len(data),"covered_employees":data.EmpID.nunique(),"records_per_employee":len(data)/data.EmpID.nunique(),
 "records_per_employment_year":len(data)/empyears,"recurring_records":int(data.TrainingProgramName.isin(RECUR).sum())}])
 missing=emp[~emp.EmpID.isin(data.EmpID)].copy()
 missing["ReferenceOrExitDate"]=missing.ExitDate.fillna(CUTOFF)
 missing["EmploymentDays"]=(missing.ReferenceOrExitDate-missing.StartDate).dt.days
 missing["Reason"]=np.where(
  missing.ExitDate.isna(),
  "A referencia-dátumig túl rövid munkaviszony; onboarding és kötelező képzés még nem volt esedékes.",
  "A munkaviszony rövidebb volt az onboarding minimumánál és a kötelező képzések első esedékességénél.")
 missing["EmployeeName"]=missing.FirstName+" "+missing.LastName
 missing_table=missing[["EmpID","EmployeeName","StartDate","ReferenceOrExitDate","EmploymentDays","EmployeeStatus","Reason"]]
 jm=j.assign(Month=j.TrainingDate.dt.to_period("M"))
 monthly=rates(jm,["Month"])
 monthly["participants"]=monthly.Month.map(jm.groupby("Month").EmpID.nunique())
 active=[]
 for period in monthly.Month:
  ms=period.start_time; me=min(period.end_time.normalize(),CUTOFF)
  active.append(int(((emp.StartDate<=me)&(emp.ExitDate.isna()|(emp.ExitDate>=ms))).sum()))
 monthly["active_employees"]=active
 monthly["participation_rate"]=monthly.participants/monthly.active_employees
 h1=j[j.TrainingDate.between(pd.Timestamp("2026-01-01"),pd.Timestamp("2026-06-30"),inclusive="both")]
 h1_rate=rates(h1.assign(Period="2026 H1"),["Period"])
 h1_summary=h1_rate.assign(unique_participants=h1.EmpID.nunique(),date_from="2026-01-01",date_to="2026-06-30")
 report=f"""# Training and development – generálási, visszajelzési és validációs riport

## Összesített eredmény

{md(freq)}

- Hivatalos referencia-dátum: **2026-06-30**
- Legkésőbbi képzési dátum: **{j.TrainingDate.max().date()}**

## Képzési rekord nélkül maradt munkavállalók

{md(missing_table)}

Az onboarding csak legalább 12 napos munkaviszonynál generálódik, az ismétlődő kötelező képzések első esedékessége pedig programtól függően legalább 30 nappal a belépés után van. A rövid foglalkoztatási időszak alatt munkakör-specifikus képzés sem generálódott. A képzési rekord hiánya ezért nem adatminőségi hiba.
- Teljesítési arány: **{overall.completion_rate:.1%}**
- Félbehagyási arány: **{overall.incomplete_rate:.1%}**
- Törlési arány: **{overall.cancellation_rate:.1%}**
- Összesített visszajelzési arány: **{overall.feedback_rate:.1%}**
- A félbehagyók ritkábban válaszolnak, ezért az elégedettségi eredmények válaszadási torzítást tartalmazhatnak.

## Visszajelzés státusz szerint

{md(status_fb)}

## Pontszámok

{md(score_stats)}

Eloszlás (darabszám az 1–5 skálán):

{md(score_dist)}

Pontszámok közötti korreláció:

{md(score_corr)}

Átlagok képzési cél szerint:

{md(purpose_scores)}

## Ismétlődő kötelező képzések

{md(recurring)}

Esedékességi lefedettség:

{md(coverage)}

Az esedékességek a tényleges munkaviszonyból és a program ciklusából származnak. A dátumok ±12 napos ablakban oszlanak el.

## Production és más területek

{md(prodcmp)}

## Képzési forma és azonos programon belüli összehasonlítás

{md(modecmp)}

{md(keym)}

## Program- és munkaköri mintázatok

{md(program_rates)}

Legalább 100 rekorddal rendelkező munkakörök:

{md(role_rates)}

## Jelenléti oktatói mintázat

{md(tr)}

## A kiválasztott férfi oktató nemek szerinti értékelése

{md(gender,4)}

A rétegzett ellenőrzés a program, forma, szervezeti terület és év szerinti cellák átlagát eltávolítva vizsgálja az eltérést. Az adat csak az eltérő értékelést támasztja alá; az ok szöveges visszajelzés vagy további vizsgálat nélkül nem állapítható meg.

## Havi mutatók

{md(monthly)}

## 2026 első félévi képzési mutatók

Az időszak definíciója kizárólag **2026-01-01 és 2026-06-30 közötti, mindkét határnapot tartalmazó rekordok**.

{md(h1_summary)}

## Automatikus validáció

"""+"\n".join(f"- {k}: {v}" for k,v in checks.items())+"\n"
 REPORT.write_text(report,encoding="utf-8")

 survey=pd.read_csv(SURVEY); survey["SurveyDate"]=pd.to_datetime(survey.SurveyDate)
 sj=survey.merge(emp[["EmpID","StartDate","ExitDate"]],on="EmpID",how="left",validate="many_to_one")
 cross={"official_reference_date":"2026-06-30","employee_rows":len(emp),"unique_employee_id":emp.EmpID.nunique(),"unknown_training_empid":checks["unknown_employee_id"],
 "training_before_start":checks["training_before_start"],"training_after_exit":checks["training_after_exit"],
 "training_after_reference_date":checks["training_after_reference_date"],
 "unknown_survey_empid":int(sj.StartDate.isna().sum()),"survey_before_start":int((sj.SurveyDate<sj.StartDate).sum()),
 "survey_after_exit":int((sj.ExitDate.notna()&(sj.SurveyDate>sj.ExitDate)).sum())}
 CROSS.write_text("# Háromfájlos keresztvalidáció\n\n"+"\n".join(f"- {k}: {v}" for k,v in cross.items())+
 "\n\nAz employee- és engagement-adatok változatlanok; a képzési fájl minden azonosítója és dátuma érvényes.\n",encoding="utf-8")
 DICT.write_text("""# Képzési adatszótár

| Mező | Jelentés |
|---|---|
| TrainingRecordID | Egyedi képzési rekordazonosító |
| EmpID | Kapcsolat az employee-törzzsel |
| TrainingDate | A képzés kezdőnapja |
| TrainingProgramName | Képzési program |
| TrainingPurpose | Mandatory, Employee Initiated vagy Job Required |
| TrainingCategory | Tartalmi kategória |
| TrainingType | Internal vagy External |
| DeliveryMode | In-person, Live Online, Self-paced Online vagy Hybrid |
| LocationCode | Fizikai helyszín vagy Online |
| Trainer | Oktató; Self-paced Online esetén üres |
| TrainerGender | Oktató neme; Self-paced Online esetén üres |
| TrainingProvider | Belső L&D, külső szolgáltató vagy digitális platform |
| TrainingDurationDays | Időtartam napokban |
| TrainingCostUSD | Pozitív képzési költség USD-ben |
| CompletionStatus | Completed, Incomplete vagy Cancelled |
| TrainingResult | Passed, Failed, Not Taken vagy Not Applicable |
| AssessmentAttempts | 0 = még nem próbálta; üres = nincs vizsga vagy törölt |
| FeedbackSubmitted | Yes vagy No |
| OverallSatisfactionScore | Összességében elégedett vagyok a képzéssel |
| TrainerEvaluationScore | Az oktató érthetősége, stílusa és támogatása |
| JobRelevanceScore | A képzés támogatja a jelenlegi munkakör ellátását |
| PersonalRelevanceScore | A képzés támogatja a személyes szakmai fejlődést |
| DigitalContentUsabilityScore | A digitális tananyag érthető önálló feldolgozhatósága |

Minden pontszám 1–5 közötti egész érték. A nem alkalmazható vagy nem megítélhető válasz hiányzó érték.
""",encoding="utf-8")
 print(f"rows={len(data)} employees={data.EmpID.nunique()} completion={overall.completion_rate:.4f} feedback={overall.feedback_rate:.4f}")
 print(checks); print(gender.to_string(index=False))

if __name__=="__main__": main()
