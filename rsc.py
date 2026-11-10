import re,json,sys
def rsc(html):
    chunks=re.findall(r'self\.__next_f\.push\(\[1,"(.*?)"\]\)',html,flags=re.S)
    return ''.join(json.loads('"'+c+'"') for c in chunks)
def arr_after(t,key,start=0):
    i=t.find('"'+key+'":',start)
    if i<0: return None
    return json.JSONDecoder().raw_decode(t[i+len(key)+3:])[0]
