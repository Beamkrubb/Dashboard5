head=open('head3.html',encoding='utf-8').read(); body=open('body3.html',encoding='utf-8').read()
js=open('script3.js',encoding='utf-8').read(); data=open('data3.json',encoding='utf-8').read().replace('</','<\\/')
cdn='<script src="https://cdnjs.cloudflare.com/ajax/libs/plotly.js/2.35.2/plotly.min.js"></script>'
page=head+body+'\n<script id="data" type="application/json">'+data+'</script>\n'+cdn+'\n<script>\n'+js+'</script>\n'
open('/mnt/user-data/outputs/thai_agri_dashboard.html','w',encoding='utf-8').write(page)
stub='<script>window.__calls=[];window.Plotly={react:(el,t,l)=>{window.__calls.push(el.id);return Promise.resolve()},relayout:()=>{}};window.claude={use:n=>Promise.resolve(n==="downloads"?{save:async a=>{window.__saved=a;return{status:"saved"}}}:null)};</script>'
open('test3.html','w',encoding='utf-8').write('<!doctype html><html><head><meta charset="utf-8"></head><body>'+page.replace(cdn,stub)+'</body></html>')
print(round(len(page)/1e6,2),'MB')
