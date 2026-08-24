#!/usr/bin/env python3
"""
decompile_aps.py - Décompile les fichiers .aps (Sudden Strike 2 / Hidden Stroke II)

Ces fichiers utilisent un conteneur maison "FZFF" : un en-tête de 8 octets
(magic "FZFF" + taille décompressée sur 4 octets little-endian) suivi d'une
série de flux zlib/deflate concaténés bout à bout. Ce script les détecte et
les décompresse en un seul flux, puis sauvegarde le résultat en texte
(encodage cp1252, courant dans ces vieux jeux) et en binaire brut.

Usage :
    python3 decompile_aps.py fichier1.aps fichier2.aps ...
    python3 decompile_aps.py --dir "/chemin/vers/dossier"   (traite tous les .aps du dossier, récursif)

Sortie :
    Pour chaque fichier.aps, crée fichier.aps.txt (texte) et fichier.aps.bin (binaire brut)
    dans le même dossier que le fichier source (ou --outdir si précisé).

Limites connues :
    - Fonctionne pour le format FZFF observé sur les .aps de ce jeu.
    - Le format .sue (UNSUE) n'a pas pu être testé faute d'exemplaire : le script
      tente quand même une détection FZFF dessus, et affiche un avertissement
      clair s'il ne reconnaît pas l'en-tête. Envoie-moi un .sue si tu veux que
      j'adapte le script à son format exact.
    - Certains fichiers (notamment les très gros comme main.aps) contiennent
      surtout des données de terrain/graphismes : le résultat texte sera
      alors majoritairement illisible, c'est normal.
"""

import sys
import os
import glob
import zlib
import argparse

MAGIC = b'FZFF'
READ_CHUNK = 1 << 20  # 1 Mo par lecture


def decompile_fzff(path, outdir=None):
    with open(path, 'rb') as f:
        header = f.read(8)
        if header[:4] != MAGIC:
            print(f"[!] {path} : pas de signature FZFF (en-tête = {header[:4]!r}), ignoré.")
            return False

        declared_len = int.from_bytes(header[4:8], 'little')

        base = os.path.basename(path)
        out_dir = outdir or os.path.dirname(path) or '.'
        bin_path = os.path.join(out_dir, base + '.bin')
        txt_path = os.path.join(out_dir, base + '.txt')

        total_out = 0
        n_streams = 0
        with open(bin_path, 'wb') as out:
            buf = b''
            d = zlib.decompressobj()
            while True:
                piece = f.read(READ_CHUNK)
                if not piece and not buf:
                    break
                buf += piece
                if not buf:
                    break
                try:
                    chunk = d.decompress(buf)
                except zlib.error:
                    # flux corrompu ou fin de fichier avec padding : on arrête proprement
                    break
                out.write(chunk)
                total_out += len(chunk)
                buf = d.unused_data
                # plusieurs flux zlib peuvent se terminer dans le même bloc lu
                while buf:
                    n_streams += 1
                    d = zlib.decompressobj()
                    try:
                        chunk = d.decompress(buf)
                    except zlib.error:
                        buf = b''
                        break
                    out.write(chunk)
                    total_out += len(chunk)
                    newbuf = d.unused_data
                    if newbuf == buf:
                        break
                    buf = newbuf
                if not piece and not buf:
                    break

        # écrit aussi une version texte (best effort, encodage cp1252)
        with open(bin_path, 'rb') as f2:
            raw = f2.read()
        text = raw.decode('cp1252', errors='replace')
        with open(txt_path, 'w', encoding='utf-8') as tf:
            tf.write(text)

        print(f"[OK] {path}")
        print(f"     taille déclarée : {declared_len:,} octets | décompressé : {total_out:,} octets | flux zlib : {n_streams+1}")
        print(f"     -> {bin_path}")
        print(f"     -> {txt_path}")
        return True


def main():
    ap = argparse.ArgumentParser(description="Décompile des fichiers .aps (format FZFF)")
    ap.add_argument('files', nargs='*', help="fichiers .aps à traiter")
    ap.add_argument('--dir', help="dossier à parcourir récursivement pour trouver des .aps/.sue")
    ap.add_argument('--outdir', help="dossier de sortie (par défaut : même dossier que le fichier source)")
    args = ap.parse_args()

    targets = list(args.files)
    if args.dir:
        targets += glob.glob(os.path.join(args.dir, '**', '*.aps'), recursive=True)
        targets += glob.glob(os.path.join(args.dir, '**', '*.sue'), recursive=True)

    if not targets:
        ap.print_help()
        sys.exit(1)

    if args.outdir:
        os.makedirs(args.outdir, exist_ok=True)

    ok, fail = 0, 0
    for t in targets:
        if decompile_fzff(t, args.outdir):
            ok += 1
        else:
            fail += 1

    print(f"\nTerminé : {ok} fichier(s) décompilé(s), {fail} ignoré(s)/échoué(s).")


if __name__ == '__main__':
    main()