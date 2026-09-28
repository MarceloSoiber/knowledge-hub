import json
meta=json.load(open('.playwright-mcp/gestao-meta.json',encoding='utf-8'))
out={'portal_url':'https://infoprod.platosedu.io/v2/lms/aluno/disciplina/conteudo/14063639/838114/3872','course_id':'838114','disciplina':'07 - Ferramentas de IA para Gestão de projetos','coletado_em':'2026-09-14T00:00:00Z','modulos':sorted({x['modulo'] for x in meta}), 'aulas':[], 'documentos':[]}
for x in meta:
    out['aulas'].append({'disciplina':out['disciplina'],'modulo':x['modulo'],'ordem':x['ordem'],'titulo':x.get('title') or f"{x['modulo']} - Aula {x['ordem']:02d}",'arquivo':f"Aula {x['ordem']:02d} - {x['modulo']}",'m3u8':x['hls'],'vtt':('https:'+x['subtitle']) if x.get('subtitle','').startswith('//') else x.get('subtitle'),'transcricao_json':x['transcricao_json'],'referer':f"https://mdstrm.com/embed/{x['id']}?jsapi=true&autoplay=false"})
json.dump(out,open('/tmp/838114.json','w',encoding='utf-8'),ensure_ascii=False,indent=2)
