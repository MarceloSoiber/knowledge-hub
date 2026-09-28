import json
links=json.load(open('.playwright-mcp/devops-links.json',encoding='utf-8'))
disc='06 - Ferramentas de IA para DevOps'; account='5e6f83ae335cdd1163e16b5b'
groups={113683:('Módulo 01',1),113684:('Módulo 01',2),113685:('Módulo 01',3),113686:('Módulo 01',4),113688:('Módulo 02',1),113689:('Módulo 02',2),113690:('Módulo 02',3),113692:('Módulo 03',1),113693:('Módulo 03',2),113694:('Módulo 03',3),113696:('Módulo 04',1),113697:('Módulo 04',2),113698:('Módulo 04',3),113700:('Módulo 05',1),113701:('Módulo 05',2),113702:('Módulo 05',3),113704:('Módulo 06',1),113705:('Módulo 06',2),113706:('Módulo 06',3),113708:('Módulo 07',1),113709:('Módulo 07',2),113710:('Módulo 07',3),113712:('Módulo 08',1),113713:('Módulo 08',2),113714:('Módulo 08',3),113715:('Módulo 08',4),113717:('Módulo 09',1),113794:('Módulo 09',2),113796:('Módulo 10',1),113797:('Módulo 10',2),113799:('Módulo 11',1),113800:('Módulo 11',2),113802:('Módulo 12',1),113803:('Módulo 12',2),113804:('Módulo 12',3),113807:('Módulo 13',1),113808:('Módulo 13',2),113809:('Módulo 13',3),113810:('Módulo 13',4),113811:('Módulo 13',5),113812:('Módulo 13',6),113813:('Módulo 13',7),113814:('Módulo 13',8),113815:('Módulo 13',9),113816:('Módulo 13',10),113818:('Módulo 13',11),113819:('Módulo 13',12),113820:('Módulo 13',13),113821:('Módulo 13',14),113823:('Podcast',1)}
aulas=[]
for x in links:
    mod,ordem=groups[x['id']]; m3u8=x['m3u8']; vid=m3u8.split('?',1)[0].rsplit('/',1)[-1].split('.')[0]
    tracks=x.get('tracks') or []; vtt=tracks[0] if tracks else f'https://platform-static.cdn.mdstrm.com/subs/{account}_{vid}.vtt'
    aulas.append({'disciplina':disc,'modulo':mod,'ordem':ordem,'titulo':f'{mod} - Aula {ordem:02d}','arquivo':f'Aula {ordem:02d} - {mod}','m3u8':m3u8,'vtt':vtt,'transcricao_json':f'https://platform-static.cdn.mdstrm.com/transcription/{account}/{vid}/transcription.json','referer':f'https://mdstrm.com/embed/{vid}?jsapi=true&autoplay=false'})
counts={}
for m,_ in groups.values(): counts[m]=counts.get(m,0)+1
mods=[{'ordem':i+1,'nome':m,'aulas_esperadas':n,'documentos_esperados':0} for i,(m,n) in enumerate(counts.items())]
docs=[('01 - Indicação de leitura.pdf','43dbeb82-7ff2-4531-b676-b1cce9a478b9'),('02 - Material autoral.pdf','72b17947-f111-464f-a259-c55b5fdc1e79')]
documentos=[{'disciplina':disc,'modulo':'Documentos','ordem':i+1,'titulo':n.rsplit('.',1)[0][5:],'arquivo':n,'url':f'https://kosmos-cronograma-anexo.s3.amazonaws.com/11042/{u}.pdf','referer':'https://infoprod.platosedu.io/v2/lms/aluno/disciplina/conteudo/14063639/838113'} for i,(n,u) in enumerate(docs)]
mods.append({'ordem':'Documentos','nome':'Documentos','aulas_esperadas':0,'documentos_esperados':2})
manifest={'portal_url':'https://infoprod.platosedu.io/v2/lms/aluno/disciplina/conteudo/14063639/838113/3871','course_id':'838113','disciplina':disc,'coletado_em':'2026-09-14T13:30:00-03:00','modulos':mods,'aulas':aulas,'documentos':documentos}
open('/tmp/platos-838113.json','w',encoding='utf-8').write(json.dumps(manifest,ensure_ascii=False))
