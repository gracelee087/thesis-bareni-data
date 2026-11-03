"""Small provider-neutral post contract; semantic adequacy is audited separately."""
import json
import re

ID_PATTERN = r'E-(WRITE-3\d{2}|OPT-4\d{2})'

def require(condition, message):
    if not condition: raise ValueError(message)

def validate_input(value):
    require(type(value) is dict,'input must be an object')
    role = value.get('role')
    require(role in ('writer','optimizer'),'unknown role')
    common = {'role','item_id','brief','common_evidence','task_evidence','required_content','prohibited_claims','preservation_constraints'}
    extra = {'fixed_plan'} if role=='writer' else {'draft','fixed_critique'}
    require(set(value)==common|extra,'unexpected or missing input fields')
    iid = value['item_id']
    require(type(iid) is str and re.fullmatch(ID_PATTERN,iid) is not None,'invalid input ID')
    require(iid.startswith('E-WRITE-') if role=='writer' else iid.startswith('E-OPT-'),'role/ID mismatch')
    require(type(value['brief']) is str and value['brief'].strip(),'missing brief')
    sources = value['common_evidence']+value['task_evidence']
    require(all(type(x) is dict and set(x)=={'source_id','text'} and all(type(v) is str and v.strip() for v in x.values()) for x in sources),'invalid evidence')
    require(len({x['source_id'] for x in sources})==len(sources),'duplicate evidence IDs')
    for name in ('required_content','prohibited_claims','preservation_constraints', 'fixed_plan' if role=='writer' else 'fixed_critique'):
        require(type(value[name]) is list and value[name] and all(type(x) is str and x.strip() for x in value[name]),'invalid '+name)
    if role=='optimizer':
        require(type(value['draft']) is dict and set(value['draft'])=={'title','body'},'invalid draft')
        validate_output({'item_id':iid,**value['draft']},iid)
    return value

def output_schema(iid):
    require(type(iid) is str and re.fullmatch(ID_PATTERN,iid) is not None,'invalid schema ID')
    return dict(type='object',additionalProperties=False,properties={
        'item_id':{'type':'string','enum':[iid]},'title':{'type':'string'},'body':{'type':'string'}},
        required=['item_id','title','body'])

def validate_output(value, iid):
    require(type(value) is dict and set(value)=={'item_id','title','body'},'output fields mismatch')
    require(all(type(x) is str for x in value.values()),'output values must be strings')
    require(value['item_id']==iid,'wrong item ID')
    require(1<=len(value['title'])<=80 and value['title'].strip(),'invalid title')
    require(150<=len(value['body'])<=600 and value['body'].strip(),'body outside 150-600 characters')
    return value

def parse_output(raw, iid):
    def unique(pairs):
        result = {}
        for k,v in pairs:
            require(k not in result,'duplicate JSON property')
            result[k]=v
        return result
    value = json.loads(raw,object_pairs_hook=unique,parse_constant=lambda _:(_ for _ in ()).throw(ValueError('non-finite JSON')))
    return validate_output(value,iid)
