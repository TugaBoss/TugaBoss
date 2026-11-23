#!/usr/bin/env python3
"""Protege o PDF do material com a palavra-chave do Reels como senha.
Uso: python3 pdf_senha.py <pasta-do-reel>
Lê out/material-aberto.pdf e grava out/<PALAVRA>.pdf (AES-256; imprimir e copiar texto continuam liberados).
"""
import json, os, sys
from pypdf import PdfReader, PdfWriter

reel = os.path.abspath(sys.argv[1])
M = json.load(open(os.path.join(reel, 'material.json'), encoding='utf-8'))
senha = M['palavraChave']
w = PdfWriter(clone_from=PdfReader(os.path.join(reel, 'out', 'material-aberto.pdf')))
w.add_metadata({'/Title': M['titulo'].replace('\n', ' ').replace('*', '').replace('_', ''), '/Author': 'Tuga Boss Digital'})
w.encrypt(user_password=senha, owner_password=senha + '-tugaboss', algorithm='AES-256')
dst = os.path.join(reel, 'out', f'{senha}.pdf')
with open(dst, 'wb') as f:
    w.write(f)
assert PdfReader(dst).decrypt(senha), 'senha não abre o PDF'
print('protegido:', dst, '· senha:', senha)
