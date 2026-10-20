"""Publish a complete prerelease from CI; the token is never printed."""
import hashlib
import json
import os
import re
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
def main():
    version=(ROOT/'release/version.txt').read_text().strip()
    if not re.fullmatch(r'\d+\.\d+\.\d+-beta\.\d+',version):raise ValueError('Esta publicação aceita somente versões beta explícitas.')
    tag='v'+version;repo=os.environ['GITHUB_REPOSITORY'];token=os.environ['GH_TOKEN'];commit=os.environ['GITHUB_SHA']
    api='https://api.github.com/repos/'+repo
    headers={'Authorization':'Bearer '+token,'Accept':'application/vnd.github+json','X-GitHub-Api-Version':'2022-11-28','User-Agent':'Guitar-Lab-release'}
    def request(url,data=None,method=None,content_type='application/json'):
        body=json.dumps(data).encode() if isinstance(data,dict) else data
        req=urllib.request.Request(url,data=body,method=method,headers=headers|{'Content-Type':content_type})
        with urllib.request.urlopen(req,timeout=180) as response:
            raw=response.read();return json.loads(raw) if raw else None
    folder=ROOT/'build/release-assets'
    files=[folder/f'GuitarLab-{version}-Linux-x64.tar.gz',folder/f'GuitarLab-{version}-Windows-x64.zip',folder/'Manual-GuitarLab.html']
    for p in files:
        if not p.is_file() or p.stat().st_size==0:raise ValueError('Asset ausente: '+p.name)
    checks=folder/'SHA256SUMS.txt'
    checks.write_text(''.join(hashlib.sha256(p.read_bytes()).hexdigest()+'  '+p.name+'\n' for p in files))
    files.append(checks)
    try:existing=request(api+'/releases/tags/'+tag)
    except urllib.error.HTTPError as e:
        if e.code!=404:raise
        existing=None
    if existing:
        raise ValueError('A release já existe; não será sobrescrita. Use uma versão nova após revisar o resultado.')
    notes=(ROOT/'release/notes.md').read_text()
    release=request(api+'/releases',dict(tag_name=tag,target_commitish=commit,name='Guitar Lab '+version,
        body=notes,draft=True,prerelease=True))
    uploads=release['upload_url'].split('{')[0]
    for path in files:
        request(uploads+'?'+urllib.parse.urlencode({'name':path.name}),path.read_bytes(),'POST','application/octet-stream')
    published=request(api+'/releases/'+str(release['id']),dict(draft=False),'PATCH')
    print('Release beta publicada:',published['html_url'])

if __name__=='__main__':main()
