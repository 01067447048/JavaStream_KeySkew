import re
def top_items(body):
    i=0; items=[]
    tagre=re.compile(r'<(w:[A-Za-z]+)\b[^>]*?(/?)>')
    while i<len(body):
        m=tagre.search(body,i)
        if not m: break
        tag=m.group(1); start=m.start()
        if m.group(2)=='/': items.append((tag,body[start:m.end()])); i=m.end(); continue
        depth=1; j=m.end(); pat=re.compile(r'<(/?)%s\b[^>]*?(/?)>'%tag)
        while depth:
            mm=pat.search(body,j)
            if mm.group(1)=='/': depth-=1
            elif mm.group(2)!='/': depth+=1
            j=mm.end()
        items.append((tag,body[start:j])); i=j
    return items
