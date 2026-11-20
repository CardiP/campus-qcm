import re,sys,json,unicodedata
from pathlib import Path
files=sorted(Path('tmp/anki/extracted').glob('COURS*'))
def norm(s):return ''.join(c for c in unicodedata.normalize('NFKD',s.lower()) if not unicodedata.combining(c))
for i,pattern in json.loads(sys.argv[1]):
 p=files[i];t=p.read_text(); parts=re.split(r'===== PAGE (\d+) =====',t)
 print('\nCOURSE',i,p.name,'QUERY',pattern)
 count=0
 for j in range(1,len(parts),2):
  body=parts[j+1];n=norm(body)
  matches=list(re.finditer(pattern,n))
  if matches:
   print('p.',parts[j],re.sub(r'\s+',' ',body[max(0,matches[0].start()-100):matches[0].end()+350]))
   count+=1
   if count>=5:break
