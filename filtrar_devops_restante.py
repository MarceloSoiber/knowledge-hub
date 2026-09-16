import json
p='/tmp/platos-838113.json'; d=json.load(open(p,encoding='utf-8'))
d['aulas']=[a for a in d['aulas'] if a['modulo'] not in ('Módulo 01','Módulo 02')]
d['modulos']=[m for m in d['modulos'] if m['nome'] not in ('Módulo 01','Módulo 02')]
open('/tmp/platos-838113-restante.json','w',encoding='utf-8').write(json.dumps(d,ensure_ascii=False))
