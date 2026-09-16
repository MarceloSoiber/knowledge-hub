import json
meta=json.load(open('.playwright-mcp/arquitetura-meta.json',encoding='utf8'))
d={'portal_url':'https://infoprod.platosedu.io/v2/lms/aluno/disciplina/conteudo/14063639/838115/3873','course_id':'838115','disciplina':'08 - Arquitetura de Sistemas com IA','coletado_em':'2026-09-14T00:00:00Z','modulos':[{'nome':m} for m in sorted({x['modulo'] for x in meta})],'aulas':[],'documentos':[]}
for x in meta:
 d['aulas'].append({'disciplina':d['disciplina'],'modulo':x['modulo'],'ordem':x['ordem'],'titulo':x.get('title') or f"{x['modulo']} - Aula {x['ordem']:02d}",'arquivo':f"Aula {x['ordem']:02d} - {x['modulo']}",'m3u8':x['hls'],'vtt':('https:'+x['subtitle']) if x.get('subtitle','').startswith('//') else x.get('subtitle'),'transcricao_json':x['transcricao_json'],'referer':f"https://mdstrm.com/embed/{x['id']}?jsapi=true&autoplay=false"})
json.dump(d,open('/tmp/838115.json','w'),ensure_ascii=False,indent=2)
