"""Offline PDF report writer with page-safe multiline rows and column selection."""
from pathlib import Path
import textwrap

PAGE_WIDTH,PAGE_HEIGHT=842,595
MARGIN=38

def _literal(value):
    value=str(value if value is not None else '').encode('latin-1','replace').decode('latin-1')
    return value.replace('\\','\\\\').replace('(','\\(').replace(')','\\)').replace('\r',' ').replace('\n',' ')

def _wrap(value,limit):
    # Preserve explicit line breaks, including blank lines, and avoid accidental
    # rendering of a newline as a control character in the PDF content stream.
    result=[]
    for line in str(value if value is not None else '').replace('\r\n','\n').replace('\r','\n').split('\n'):
        result.extend(textwrap.wrap(line,width=limit,break_long_words=True,break_on_hyphens=False,replace_whitespace=False) or [''])
    return result or ['']

def write_pdf(path,title,fields,rows):
    if not fields:raise ValueError('Select at least one column')
    width,height=PAGE_WIDTH,PAGE_HEIGHT
    col_count=len(fields)+1
    usable=width-2*MARGIN
    # Reserve a narrow number column so text columns remain readable.
    num_width=42
    data_width=(usable-num_width)/len(fields)
    font_size=max(6,min(10,80/(len(fields)+1)))
    leading=font_size+3
    char_limit=max(3,int((data_width-12)/(font_size*.54)))
    widths=[num_width]+[data_width]*len(fields)
    xs=[MARGIN]
    for col_width in widths:xs.append(xs[-1]+col_width)
    pages=[];commands=[];y=0
    def emit(text,x,baseline,size=9,bold=False):
        commands.append(f'0.13 0.18 0.24 rg BT /F{2 if bold else 1} {size:.1f} Tf 1 0 0 1 {x:.1f} {baseline:.1f} Tm ({_literal(text)}) Tj ET')
    def rule(at):commands.append(f'0.82 0.85 0.88 RG 0.6 w {MARGIN} {at:.1f} m {width-MARGIN} {at:.1f} l S')
    def newpage():
        nonlocal commands,y
        if commands:pages.append('\n'.join(commands).encode('latin-1'))
        commands=[];y=height-40
        emit(title,MARGIN,y,15,True);y-=23
        emit('Ledgerbook report | # follows the current filtered and sorted table',MARGIN,y,8);y-=24
        for j,label in enumerate(['#']+[f['label'] for f in fields]):
            lim=6 if j==0 else char_limit
            emit(str(label)[:lim],xs[j]+4,y,font_size,True)
        y-=10;rule(y);y-=17
    newpage()
    for number,values in rows:
        cells=[str(number)]+[values.get(f['key'],'') for f in fields]
        wrapped=[_wrap(c,6 if i==0 else char_limit) for i,c in enumerate(cells)]
        offset=0;total=max(map(len,wrapped))
        while offset<total:
            available=y-(MARGIN+14)
            fit=int((available-12)//leading)
            if fit<1:
                newpage();continue
            chunk=min(fit,total-offset)
            for j,parts in enumerate(wrapped):
                for k,part in enumerate(parts[offset:offset+chunk]):
                    emit(part,xs[j]+4,y-k*leading,font_size)
            # Place the separator strictly below the lowest rendered baseline.
            y-=chunk*leading+9
            rule(y+2)
            y-=7
            offset+=chunk
            if offset<total:newpage()
    if commands:pages.append('\n'.join(commands).encode('latin-1'))
    objects=[b'<< /Type /Catalog /Pages 2 0 R >>',b'',
             b'<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>',
             b'<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica-Bold >>']
    page_ids=[]
    for data in pages:
        page_id=len(objects)+1;content_id=page_id+1;page_ids.append(page_id)
        objects.append(f'<< /Type /Page /Parent 2 0 R /MediaBox [0 0 {width} {height}] /Resources << /Font << /F1 3 0 R /F2 4 0 R >> >> /Contents {content_id} 0 R >>'.encode())
        objects.append(f'<< /Length {len(data)} >>\nstream\n'.encode()+data+b'\nendstream')
    objects[1]=f'<< /Type /Pages /Kids [{" ".join(str(i)+" 0 R" for i in page_ids)}] /Count {len(page_ids)} >>'.encode()
    output=bytearray(b'%PDF-1.4\n%\xe2\xe3\xcf\xd3\n');offsets=[0]
    for i,obj in enumerate(objects,1):
        offsets.append(len(output));output.extend(f'{i} 0 obj\n'.encode()+obj+b'\nendobj\n')
    xref=len(output);output.extend(f'xref\n0 {len(objects)+1}\n0000000000 65535 f \n'.encode())
    for off in offsets[1:]:output.extend(f'{off:010d} 00000 n \n'.encode())
    output.extend(f'trailer\n<< /Size {len(objects)+1} /Root 1 0 R >>\nstartxref\n{xref}\n%%EOF\n'.encode())
    Path(path).write_bytes(output)
    return len(pages)
