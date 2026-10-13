"use strict";
/* Deterministic thresholds correspond to agents/workers.py. */
function evaluateExample(x) {
  if (!Number.isFinite(x.primary_metric) || !Number.isFinite(x.secondary_metric)) throw new Error("Metrics must be finite numbers.");
  if (!x.task_id.trim() || !x.target_identifier.trim()) throw new Error("Both synthetic identifiers are required.");
  const alerts = [];
  if (x.primary_metric > 25) alerts.push({ worker:"InvariantQCWorker", urgency:"ELEVATED_RISK", summary:"Primary metric exceeds 25." });
  if (x.is_critical_flag || x.secondary_metric > 12) alerts.push({ worker:"SafetyEscalationWorker", urgency:x.is_critical_flag?"CRITICAL_STAT_PANIC":"ELEVATED_RISK", summary:x.is_critical_flag?"Critical override was selected.":"Secondary metric exceeds 12." });
  if (["DISCORDANT","ANOMALY","MUTANT","VIOLATION","FAIL","REJECT"].some(function(word){return String(x.status_descriptor).toUpperCase().includes(word);})) alerts.push({worker:"ProtocolConformanceWorker",urgency:"ELEVATED_RISK",summary:"Descriptor includes an alert keyword."});
  const overall = alerts.some(function(a){return a.urgency==="CRITICAL_STAT_PANIC";})?"CRITICAL_STAT_PANIC":alerts.length?"ELEVATED_RISK":"ROUTINE";
  return { demo_only:true,task_id:x.task_id,target_identifier:x.target_identifier,overall_urgency:overall,total_alerts:alerts.length,alerts:alerts,disclaimer:"Not clinically validated; synthetic educational example only." };
}
if (typeof module !== "undefined" && module.exports) module.exports = {evaluateExample:evaluateExample};
if (typeof document !== "undefined") document.addEventListener("DOMContentLoaded",function(){
  const form=document.getElementById("form"),out=document.getElementById("result"),err=document.getElementById("error"),save=document.getElementById("export");
  let last=null;
  function node(tag,text,cls){const el=document.createElement(tag);el.textContent=text;if(cls)el.className=cls;return el;}
  form.addEventListener("submit",function(ev){
    ev.preventDefault();err.textContent="";
    try{
      last=evaluateExample({
        task_id:document.getElementById("task").value.trim(),
        target_identifier:document.getElementById("target").value.trim(),
        primary_metric:document.getElementById("primary").valueAsNumber,
        secondary_metric:document.getElementById("secondary").valueAsNumber,
        status_descriptor:document.getElementById("descriptor").value,
        is_critical_flag:document.getElementById("critical").checked
      });
      const cls=last.overall_urgency==="ROUTINE"?"routine":last.overall_urgency==="ELEVATED_RISK"?"elevated":"critical";
      out.replaceChildren(node("h3",last.overall_urgency,cls),node("p",last.total_alerts+" rule(s) triggered."));
      const list=document.createElement("ul");
      last.alerts.forEach(function(a){const li=node("li",a.worker+": "+a.summary);list.appendChild(li);});
      out.appendChild(list);out.appendChild(node("p",last.disclaimer,"muted"));save.disabled=false;
    }catch(e){last=null;save.disabled=true;out.replaceChildren();err.textContent=e.message;}
  });
  form.addEventListener("reset",function(){last=null;save.disabled=true;err.textContent="";out.replaceChildren(node("p","Select Evaluate example to run the checks.","muted"));});
  save.addEventListener("click",function(){
    if(!last)return;
    const url=URL.createObjectURL(new Blob([JSON.stringify(last,null,2)],{type:"application/json"}));
    const a=document.createElement("a");a.href=url;a.download="icu-demo-result.json";a.click();URL.revokeObjectURL(url);
  });
});