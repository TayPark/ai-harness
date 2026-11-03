"""Conservative preservation checks; semantic changes need human or model review."""
import re
def check_preservation(original, revised, mapping):
    errors=[]; unverified=[]
    old={r['requirement_id']:r for r in original}; new={r['requirement_id']:r for r in revised}
    if len(old)!=len(original) or len(new)!=len(revised): errors.append('duplicate requirement IDs')
    rows={m['requirement_id']:m for m in mapping}
    if len(rows)!=len(mapping): errors.append('duplicate mapping IDs')
    for identifier,r in old.items():
        if r['status'] not in ('EXPLICIT','DECISION_REQUIRED'): continue
        m=rows.get(identifier)
        if not m: errors.append('missing preservation mapping '+identifier); continue
        authorized=bool(m.get('authorization')) and m.get('classification') in ('AUTHORIZED_CHANGE','REMOVED_WITH_AUTHORIZATION')
        if identifier not in new:
            if not authorized: errors.append('removed requirement '+identifier)
            continue
        n=new[identifier]
        if r['status']=='DECISION_REQUIRED' and n['status']!='DECISION_REQUIRED' and not authorized: errors.append('hidden unresolved decision '+identifier)
        if r['status']=='EXPLICIT' and n['status']!='EXPLICIT' and not authorized: errors.append('weakened status '+identifier)
        if r['description']!=n['description'] and not authorized:
            if re.findall(r'\d+(?:\.\d+)?',r['description'])!=re.findall(r'\d+(?:\.\d+)?',n['description']): errors.append('changed numeric constraint '+identifier)
            if not m.get('semantic_review') or not m.get('explanation'): unverified.append('semantic preservation '+identifier)
        if not m.get('revised_location') or not m.get('preservation_status'): errors.append('incomplete mapping '+identifier)
    for identifier,n in new.items():
        if (identifier not in old or old[identifier]['status'] in ('ASSUMPTION','PROPOSED_DEFAULT')) and n['status']=='EXPLICIT':
            if not rows.get(identifier,{}).get('authorization'): errors.append('unsupported confirmed default '+identifier)
    for r in revised:
        if r.get('contradiction_unresolved'): errors.append('new unresolved contradiction '+r['requirement_id'])
    return dict(passed=not errors and not unverified,failed=errors,unverified=unverified)
