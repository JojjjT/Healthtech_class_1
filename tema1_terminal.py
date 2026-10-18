import marimo

__generated_with = "0.10.0"
app = marimo.App(width="medium", app_title="Tema 1.1 · Terminal Linux (WASM)")


# ═════════════════════════ Portada ═════════════════════════
@app.cell(hide_code=True)
def _():
    import marimo as mo

    mo.md(
        r"""
        # Laboratorio 1 · Tema 1.1 — La terminal de Linux
        **Bioinformática y análisis de datos ómicos** · versión **WASM** (todo en tu navegador)

        Cada uno de los **11 ejercicios** tiene su **propia caja de comandos**:

        1. Escribe uno o varios comandos (**uno por línea**) en la caja del ejercicio.
        2. Pulsa **▶ Ejecutar**. Verás la sesión de la terminal y una **comprobación automática** (✔ / ✘).
        3. Si algo falla, corrige y vuelve a ejecutar. Hay una **💡 Pista** y una **✅ Solución de referencia** desplegables.

        **Cómo funciona**

        - La "terminal" es una **emulación en Python** (no hay bash real en el navegador), pero
          `pwd`, `ls`, `cd`, `mkdir`, `cp`, `mv`, `cat`, `ln -s`, `rm`, `wc`, `md5sum`, `head`, `tail`,
          `echo`… funcionan igual, y también `&&`, `;`, `|`, `<`, `>`, `>>`.
        - **Cada ejecución parte del estado correcto** tras los ejercicios anteriores. Por eso puedes hacer
          los ejercicios en cualquier orden, repetirlos y equivocarte sin romper nada.
        - Dentro de una misma caja los comandos **sí** se encadenan (un `cd` afecta a las líneas siguientes).
        - `nano` no existe en el navegador: en el ejercicio 10 se emula con `echo "…" >> archivo`.
        - Al final hay una **🧪 Terminal libre** para experimentar.
        """
    )
    return (mo,)


# ═════════════════════════ Imports ═════════════════════════
@app.cell(hide_code=True)
def _():
    import hashlib
    import io
    import os
    import shlex
    import shutil
    import tempfile
    import zipfile

    return hashlib, io, os, shlex, shutil, tempfile, zipfile


# ═════════════════════════ Subida de archivos ═════════════════════════
@app.cell(hide_code=True)
def _(mo):
    upload = mo.ui.file(
        label="📁 Subir archivos a  ~/Tema1/  (o un .zip con la carpeta Tema1)",
        multiple=True,
    )
    mo.vstack([
        mo.md(
            r"""
            ---
            ## 📤 Subir tus archivos (opcional)

            - **Archivos sueltos** (`Secuencias.txt`, `.fa`, `.fastq`…) → se copian a `~/Tema1/`.
              Si subes un `Secuencias.txt`, **sustituye** al de demostración.
            - **`.zip`** → se usan los archivos de su carpeta `Tema1/`.

            Si no subes nada, se usan **datos de demostración**. Al subir archivos, los resultados
            de los ejercicios se recalculan solos con tus datos.
            """
        ),
        upload,
    ])
    return (upload,)


@app.cell(hide_code=True)
def _(io, mo, upload, zipfile):
    SEED = {}
    _msgs = []

    for _f in (upload.value or []):
        _name = _f.name
        _content = _f.contents
        if callable(_content):  # compatibilidad con versiones antiguas
            _content = _content()
        if _name.lower().endswith(".zip"):
            try:
                with zipfile.ZipFile(io.BytesIO(_content)) as _z:
                    _found = 0
                    for _n in _z.namelist():
                        _parts = [p for p in _n.split("/") if p]
                        if "Tema1" in _parts and not _n.endswith("/"):
                            _rest = _parts[_parts.index("Tema1") + 1:]
                            if len(_rest) == 1:
                                SEED[_rest[0]] = _z.read(_n)
                                _found += 1
                    if _found:
                        _msgs.append(f"✔ `{_name}` → {_found} archivo(s) de `Tema1/`")
                    else:
                        _msgs.append(f"✘ `{_name}`: no contiene archivos dentro de una carpeta `Tema1/`")
            except Exception as _e:
                _msgs.append(f"✘ `{_name}`: {_e}")
        else:
            SEED[_name] = _content
            _msgs.append(f"✔ `{_name}` → `~/Tema1/`")

    if _msgs:
        mo.md("**Archivos cargados:**\n\n" + "\n".join(f"- {m}" for m in _msgs))
    else:
        mo.md("*Todavía no has subido archivos: se usarán los **datos de demostración**.*")
    return (SEED,)


# ═════════════════════════ Motor: terminal emulada + comprobaciones ═════════════════════════
@app.cell(hide_code=True)
def _(hashlib, os, shlex, shutil, tempfile):
    DEMO_SEQ = (
        "@A01196:35:H2YTJDRX2:1:2101:29677:1376 1:N:0:CGGCTATG+ACGTCCTG\n"
        "CCAACAGGGTTGGTCTCCGTACGTTTCCTCACCTGCATTTCGTTCGTAGTCCCCGATGAATCG\n"
        "+\n"
        "FFFF,FFFFFFF,FFF,FFFFFFF:F:FFFF,::,FF,F:FFFF::FF,FFF:FFFFFF:FFFF\n"
    ) * 3

    READERS = ("cat", "less", "more", "head", "tail")

    # Comandos de referencia: SOLUTIONS[n-1] resuelve el ejercicio n.
    SOLUTIONS = [
        ["pwd"],
        ["ls"],
        ["cd Tema1"],
        ["mkdir Datos"],
        ["cp Secuencias.txt Datos/"],
        ["cd Datos", "mv Secuencias.txt aminoacidos.tt"],
        ["cat aminoacidos.tt"],
        ["ln -s ../Secuencias.txt Secuencias.txt"],
        ["cat Secuencias.txt"],
        ["cd ..", 'echo "Estoy añadiendo una nueva línea" >> Secuencias.txt', "cat Secuencias.txt"],
        ["rm Datos/aminoacidos.tt"],
    ]


    def oserr_text(e):
        if getattr(e, "errno", None) == 40:
            return "Too many levels of symbolic links"
        return getattr(e, "strerror", None) or str(e)


    class Terminal:
        """Mini-shell en Python (sin bash real): todo ocurre dentro de una carpeta temporal."""

        def __init__(self, root):
            self.root = os.path.normpath(str(root))
            self.home = os.path.join(self.root, "home", "alumno")
            self.cwd = self.home
            self.records = []

        # ───────── rutas ─────────
        def virt(self, real):
            v = real[len(self.root):]
            return v if v else "/"

        def resolve(self, p, cwd=None):
            base = cwd or self.cwd
            p = p if p else "."
            if p == "~" or p.startswith("~/"):
                full = self.home + p[1:]
            elif p.startswith("/"):
                full = self.root + p
            else:
                full = os.path.join(base, p)
            full = os.path.normpath(full)
            if not (full == self.root or full.startswith(self.root + os.sep)):
                full = self.root
            return full

        @property
        def prompt(self):
            rel = os.path.relpath(self.cwd, self.home)
            if rel == ".":
                return "alumno@lab:~$"
            if rel.startswith(".."):
                return "alumno@lab:" + self.virt(self.cwd) + "$"
            return "alumno@lab:~/" + rel + "$"

        # ───────── análisis de la línea ─────────
        def tokenize(self, line):
            lex = shlex.shlex(line, posix=True, punctuation_chars=True)
            lex.whitespace_split = True
            lex.commenters = ""
            return list(lex)

        def run_line(self, line):
            """Ejecuta una línea (admite &&, ||, ;, |, <, >, >>). Devuelve (out, err, code)."""
            line = line.strip()
            if not line or line.startswith("#"):
                return "", "", 0
            try:
                tokens = self.tokenize(line)
            except ValueError as e:
                return "", "bash: error de sintaxis: " + str(e) + "\n", 2
            seqs = []
            cur = []
            op = None
            for tok in tokens:
                if tok in ("&&", "||", ";"):
                    seqs.append((op, cur))
                    cur = []
                    op = tok
                else:
                    cur.append(tok)
            seqs.append((op, cur))
            outs, errs, code = [], [], 0
            for op, toks in seqs:
                if op == "&&" and code != 0:
                    continue
                if op == "||" and code == 0:
                    continue
                if not toks:
                    continue
                try:
                    o, e, code = self._pipeline(toks)
                except Exception as ex:  # nunca debe romper el cuaderno
                    o, e, code = "", "bash: error interno: " + str(ex) + "\n", 1
                outs.append(o)
                errs.append(e)
            return "".join(outs), "".join(errs), code

        def _pipeline(self, toks):
            stages = [[]]
            for t in toks:
                if t == "|":
                    stages.append([])
                else:
                    stages[-1].append(t)
            stdin = None
            out, err_all, code = "", "", 0
            for st in stages:
                if not st:
                    return "", "bash: error de sintaxis cerca de `|'\n", 2
                out, err, code = self._stage(st, stdin)
                err_all += err
                stdin = out.encode("utf-8")
            return out, err_all, code

        def _stage(self, toks, stdin):
            args = []
            fin = None
            fout = None
            mode = "w"
            i = 0
            while i < len(toks):
                t = toks[i]
                if t in ("<", ">", ">>"):
                    if i + 1 >= len(toks):
                        return "", "bash: error de sintaxis cerca de `newline'\n", 2
                    if t == "<":
                        fin = toks[i + 1]
                    else:
                        fout = toks[i + 1]
                        mode = "a" if t == ">>" else "w"
                    i += 2
                    continue
                args.append(t)
                i += 1

            cwd_before = self.cwd
            if fin is not None:
                try:
                    with open(self.resolve(fin), "rb") as fh:
                        stdin = fh.read()
                except FileNotFoundError:
                    return "", "bash: " + fin + ": No such file or directory\n", 1
                except OSError as e:
                    return "", "bash: " + fin + ": " + str(e) + "\n", 1

            if args:
                out, err, code = self._dispatch(args[0], args[1:], stdin)
                out = out.replace(self.root, "")
                err = err.replace(self.root, "")
            else:
                out, err, code = "", "", 0

            if fout is not None:
                p = self.resolve(fout)
                if os.path.isdir(p):
                    err += "bash: " + fout + ": Is a directory\n"
                    code = 1
                else:
                    try:
                        with open(p, mode, encoding="utf-8") as fh:
                            fh.write(out)
                        out = ""
                    except OSError as e:
                        err += "bash: " + fout + ": " + str(e) + "\n"
                        code = 1

            self.records.append({
                "name": args[0] if args else "",
                "args": args[1:],
                "cwd": cwd_before,
                "out": out,
                "err": err,
                "code": code,
                "fin": fin,
                "fout": fout,
            })
            return out, err, code

        # ───────── despacho ─────────
        def _dispatch(self, cmd, a, stdin):
            table = {
                "echo": self._echo, "pwd": self._pwd, "cd": self._cd, "ls": self._ls,
                "mkdir": self._mkdir, "rmdir": self._rmdir, "touch": self._touch,
                "cp": self._cp, "mv": self._mv, "rm": self._rm, "ln": self._ln,
                "cat": self._cat, "less": self._cat, "more": self._cat,
                "wc": self._wc, "md5sum": self._md5sum,
                "head": self._head, "tail": self._tail,
                "readlink": self._readlink, "test": self._test,
            }
            if cmd in table:
                return table[cmd](a, stdin)
            if cmd == "clear":
                return "", "", 0
            if cmd in ("nano", "vi", "vim", "pico"):
                return ("", cmd + ": editor interactivo, no disponible en el navegador.\n"
                        "Para añadir una línea al final usa:  echo \"texto\" >> archivo\n", 1)
            if cmd == "help":
                return ("Comandos: pwd · ls · cd · mkdir · rmdir · touch · cp · mv · rm · ln -s · "
                        "cat/less/more · head · tail · wc · md5sum · readlink · test · echo\n"
                        "Operadores: &&  ||  ;  |  <  >  >>\n"), "", 0
            return "", "bash: " + cmd + ": command not found\n", 127

        # ───────── comandos ─────────
        def _echo(self, a, stdin):
            if a and a[0] == "-n":
                return " ".join(a[1:]), "", 0
            return " ".join(a) + "\n", "", 0

        def _pwd(self, a, stdin):
            return self.virt(self.cwd) + "\n", "", 0

        def _cd(self, a, stdin):
            target = a[0] if a else "~"
            p = self.resolve(target)
            if os.path.isdir(p):
                self.cwd = p
                return "", "", 0
            if os.path.exists(p):
                return "", "bash: cd: " + target + ": Not a directory\n", 1
            return "", "bash: cd: " + target + ": No such file or directory\n", 1

        def _ls_entry(self, full, name, long):
            if not long:
                return name
            size = os.lstat(full).st_size
            if os.path.islink(full):
                return "lrwxrwxrwx 1 alumno alumno %5d Oct 18 10:00 %s -> %s" % (size, name, os.readlink(full))
            if os.path.isdir(full):
                return "drwxr-xr-x 2 alumno alumno %5d Oct 18 10:00 %s" % (4096, name)
            return "-rw-r--r-- 1 alumno alumno %5d Oct 18 10:00 %s" % (size, name)

        def _ls(self, a, stdin):
            long = False
            hidden = False
            dots = False
            targets = []
            for x in a:
                if x.startswith("-") and len(x) > 1:
                    if "l" in x:
                        long = True
                    if "a" in x:
                        hidden = True
                        dots = True
                    if "A" in x:
                        hidden = True
                else:
                    targets.append(x)
            if not targets:
                targets = ["."]
            files, dirs, errs, code = [], [], "", 0
            for t in targets:
                p = self.resolve(t)
                if not os.path.lexists(p):
                    errs += "ls: cannot access '" + t + "': No such file or directory\n"
                    code = 2
                    continue
                if os.path.isdir(p):
                    names = sorted(os.listdir(p))
                    if not hidden:
                        names = [n for n in names if not n.startswith(".")]
                    if dots:
                        names = [".", ".."] + names
                    lines = [self._ls_entry(os.path.join(p, n), n, long) for n in names]
                    dirs.append((t, lines))
                else:
                    files.append(self._ls_entry(p, t, long))
            blocks = []
            if files:
                blocks.append("\n".join(files))
            for t, lines in dirs:
                body = "\n".join(lines)
                if len(targets) > 1:
                    body = t + ":\n" + body
                if body:
                    blocks.append(body)
            out = "\n\n".join(blocks)
            return (out + "\n" if out else ""), errs, code

        def _mkdir(self, a, stdin):
            parents = any(x.startswith("-") and "p" in x for x in a)
            err, code = "", 0
            for x in [y for y in a if not y.startswith("-")]:
                p = self.resolve(x)
                try:
                    if parents:
                        os.makedirs(p, exist_ok=True)
                    else:
                        os.mkdir(p)
                except FileExistsError:
                    err += "mkdir: cannot create directory '" + x + "': File exists\n"
                    code = 1
                except FileNotFoundError:
                    err += "mkdir: cannot create directory '" + x + "': No such file or directory\n"
                    code = 1
                except OSError as e:
                    err += "mkdir: " + str(e) + "\n"
                    code = 1
            if not [y for y in a if not y.startswith("-")]:
                return "", "mkdir: missing operand\n", 1
            return "", err, code

        def _rmdir(self, a, stdin):
            err, code = "", 0
            for x in [y for y in a if not y.startswith("-")]:
                try:
                    os.rmdir(self.resolve(x))
                except OSError:
                    err += "rmdir: failed to remove '" + x + "': Directory not empty or not found\n"
                    code = 1
            return "", err, code

        def _touch(self, a, stdin):
            for x in [y for y in a if not y.startswith("-")]:
                with open(self.resolve(x), "a"):
                    pass
            return "", "", 0

        def _cp(self, a, stdin):
            rec = any(x.startswith("-") and ("r" in x or "R" in x or "a" in x) for x in a)
            args = [x for x in a if not x.startswith("-")]
            if len(args) < 2:
                return "", "cp: missing file operand\n", 1
            srcs, dst = args[:-1], args[-1]
            dst_p = self.resolve(dst)
            dst_dir = os.path.isdir(dst_p)
            if len(srcs) > 1 and not dst_dir:
                return "", "cp: target '" + dst + "' is not a directory\n", 1
            err, code = "", 0
            for s in srcs:
                sp = self.resolve(s)
                if not os.path.exists(sp):
                    err += "cp: cannot stat '" + s + "': No such file or directory\n"
                    code = 1
                    continue
                target = os.path.join(dst_p, os.path.basename(sp)) if dst_dir else dst_p
                if os.path.abspath(sp) == os.path.abspath(target):
                    err += "cp: '" + s + "' and '" + dst + "' are the same file\n"
                    code = 1
                    continue
                try:
                    if os.path.isdir(sp):
                        if not rec:
                            err += "cp: -r not specified; omitting directory '" + s + "'\n"
                            code = 1
                            continue
                        shutil.copytree(sp, target)
                    else:
                        shutil.copyfile(sp, target)
                except OSError as e:
                    err += "cp: " + str(e) + "\n"
                    code = 1
            return "", err, code

        def _mv(self, a, stdin):
            args = [x for x in a if not x.startswith("-")]
            if len(args) < 2:
                return "", "mv: missing file operand\n", 1
            srcs, dst = args[:-1], args[-1]
            dst_p = self.resolve(dst)
            dst_dir = os.path.isdir(dst_p)
            if len(srcs) > 1 and not dst_dir:
                return "", "mv: target '" + dst + "' is not a directory\n", 1
            err, code = "", 0
            for s in srcs:
                sp = self.resolve(s)
                if not os.path.lexists(sp):
                    err += "mv: cannot stat '" + s + "': No such file or directory\n"
                    code = 1
                    continue
                target = os.path.join(dst_p, os.path.basename(sp)) if dst_dir else dst_p
                if os.path.abspath(sp) == os.path.abspath(target):
                    err += "mv: '" + s + "' and '" + dst + "' are the same file\n"
                    code = 1
                    continue
                try:
                    shutil.move(sp, target)
                except OSError as e:
                    err += "mv: " + str(e) + "\n"
                    code = 1
            return "", err, code

        def _read(self, name):
            p = self.resolve(name)
            if os.path.isdir(p):
                raise IsADirectoryError(name)
            with open(p, "rb") as fh:
                return fh.read().decode("utf-8", errors="replace")

        def _cat(self, a, stdin):
            names = [x for x in a if not x.startswith("-")]
            if not names and stdin is not None:
                return stdin.decode("utf-8", errors="replace"), "", 0
            out, err, code = "", "", 0
            for n in names:
                try:
                    out += self._read(n)
                except IsADirectoryError:
                    err += "cat: " + n + ": Is a directory\n"
                    code = 1
                except FileNotFoundError:
                    err += "cat: " + n + ": No such file or directory\n"
                    code = 1
                except OSError as e:
                    err += "cat: " + n + ": " + oserr_text(e) + "\n"
                    code = 1
            return out, err, code

        def _rm(self, a, stdin):
            rec = any(x.startswith("-") and ("r" in x or "R" in x) for x in a)
            force = any(x.startswith("-") and "f" in x for x in a)
            targets = [x for x in a if not x.startswith("-")]
            if not targets:
                return "", "rm: missing operand\n", 1
            err, code = "", 0
            for t in targets:
                p = self.resolve(t)
                try:
                    if os.path.islink(p) or os.path.isfile(p):
                        os.remove(p)
                    elif os.path.isdir(p):
                        if rec:
                            shutil.rmtree(p)
                        else:
                            err += "rm: cannot remove '" + t + "': Is a directory\n"
                            code = 1
                    elif not force:
                        err += "rm: cannot remove '" + t + "': No such file or directory\n"
                        code = 1
                except OSError as e:
                    err += "rm: " + str(e) + "\n"
                    code = 1
            return "", err, code

        def _ln(self, a, stdin):
            symbolic = any(x.startswith("-") and "s" in x for x in a)
            force = any(x.startswith("-") and "f" in x for x in a)
            rest = [x for x in a if not x.startswith("-")]
            if len(rest) < 2:
                return "", "ln: missing file operand\n", 1
            target, name = rest[0], rest[1]
            link_p = self.resolve(name)
            if os.path.isdir(link_p) and not os.path.islink(link_p):
                link_p = os.path.join(link_p, os.path.basename(target.rstrip("/")))
            kind = "symbolic link" if symbolic else "hard link"
            try:
                if force and os.path.lexists(link_p):
                    os.remove(link_p)
                if symbolic:
                    real_target = (self.root + target) if target.startswith("/") else target
                    os.symlink(real_target, link_p)
                else:
                    src = self.resolve(target)
                    try:
                        os.link(src, link_p)
                    except (OSError, NotImplementedError, AttributeError):
                        shutil.copyfile(src, link_p)  # respaldo si el sistema no admite enlaces duros
            except FileExistsError:
                return "", "ln: failed to create " + kind + " '" + name + "': File exists\n", 1
            except OSError as e:
                return "", "ln: " + str(e) + "\n", 1
            return "", "", 0

        def _wc(self, a, stdin):
            flags = "".join(x[1:] for x in a if x.startswith("-"))
            names = [x for x in a if not x.startswith("-")]

            def fmt(data, name):
                nl = data.count(b"\n")
                nw = len(data.split())
                nc = len(data)
                parts = []
                if not flags:
                    parts = [nl, nw, nc]
                else:
                    if "l" in flags:
                        parts.append(nl)
                    if "w" in flags:
                        parts.append(nw)
                    if "c" in flags:
                        parts.append(nc)
                s = " ".join(str(x) for x in parts)
                return s + (" " + name if name else "")

            if not names and stdin is not None:
                return fmt(stdin, "") + "\n", "", 0
            lines = []
            for n in names:
                try:
                    with open(self.resolve(n), "rb") as fh:
                        lines.append(fmt(fh.read(), n))
                except OSError:
                    return "", "wc: " + n + ": No such file or directory\n", 1
            return "\n".join(lines) + "\n", "", 0

        def _md5sum(self, a, stdin):
            names = [x for x in a if not x.startswith("-")]
            if not names and stdin is not None:
                return hashlib.md5(stdin).hexdigest() + "  -\n", "", 0
            out = ""
            for n in names:
                try:
                    with open(self.resolve(n), "rb") as fh:
                        out += hashlib.md5(fh.read()).hexdigest() + "  " + n + "\n"
                except OSError:
                    return out, "md5sum: " + n + ": No such file or directory\n", 1
            return out, "", 0

        def _head_tail(self, a, stdin, mode):
            n = 10
            names = []
            i = 0
            while i < len(a):
                x = a[i]
                if x == "-n" and i + 1 < len(a):
                    try:
                        n = int(a[i + 1])
                    except ValueError:
                        pass
                    i += 2
                    continue
                if x.startswith("-n") and len(x) > 2:
                    try:
                        n = int(x[2:])
                    except ValueError:
                        pass
                elif x.startswith("-") and x[1:].isdigit():
                    n = int(x[1:])
                elif x.startswith("-"):
                    pass
                else:
                    names.append(x)
                i += 1

            def cut(text):
                ls = text.splitlines(keepends=True)
                if mode == "head":
                    return "".join(ls[:n])
                return "".join(ls[-n:]) if n > 0 else ""

            if not names and stdin is not None:
                return cut(stdin.decode("utf-8", errors="replace")), "", 0
            out, err, code = "", "", 0
            for idx, nm in enumerate(names):
                try:
                    text = self._read(nm)
                except IsADirectoryError:
                    err += mode + ": error reading '" + nm + "': Is a directory\n"
                    code = 1
                    continue
                except OSError as e:
                    err += mode + ": cannot open '" + nm + "' for reading: " + oserr_text(e) + "\n"
                    code = 1
                    continue
                if len(names) > 1:
                    out += ("\n" if idx > 0 else "") + "==> " + nm + " <==\n"
                body = cut(text)
                out += body if body.endswith("\n") or not body else body + "\n"
            return out, err, code

        def _head(self, a, stdin):
            return self._head_tail(a, stdin, "head")

        def _tail(self, a, stdin):
            return self._head_tail(a, stdin, "tail")

        def _readlink(self, a, stdin):
            full = any(x.startswith("-") and "f" in x for x in a)
            out = ""
            for n in [x for x in a if not x.startswith("-")]:
                p = self.resolve(n)
                if full:
                    out += os.path.realpath(p) + "\n"
                elif os.path.islink(p):
                    out += os.readlink(p) + "\n"
                else:
                    return out, "", 1
            return out, "", 0

        def _test(self, a, stdin):
            neg = False
            if a and a[0] == "!":
                neg = True
                a = a[1:]
            fns = {"-e": os.path.exists, "-f": os.path.isfile, "-d": os.path.isdir,
                   "-L": os.path.islink, "-h": os.path.islink}
            ok = False
            if len(a) == 2 and a[0] in fns:
                ok = fns[a[0]](self.resolve(a[1]))
            return "", "", (0 if ok != neg else 1)


    # ═════════════════════ Laboratorio y sesiones ═════════════════════
    def norm_seed(seed):
        s = dict(seed or {})
        if "Secuencias.txt" not in s:
            s["Secuencias.txt"] = DEMO_SEQ.encode("utf-8")
        return s


    def build_lab(seed, upto=0):
        """Crea un laboratorio nuevo y aplica las soluciones de los primeros `upto` ejercicios."""
        root = tempfile.mkdtemp(prefix="lab1_")
        t = Terminal(root)
        tema1 = os.path.join(t.home, "Tema1")
        os.makedirs(tema1)
        for name, data in norm_seed(seed).items():
            with open(os.path.join(tema1, os.path.basename(name)), "wb") as fh:
                fh.write(data)
        for k in range(upto):
            for line in SOLUTIONS[k]:
                t.run_line(line)
        t.records = []
        return t


    def start_prompt(n, seed=None):
        t = build_lab(seed, n - 1)
        try:
            return t.prompt
        finally:
            shutil.rmtree(t.root, ignore_errors=True)


    def run_session(t, text, max_lines=30):
        blocks = []
        for raw in text.splitlines():
            line = raw.strip()
            if not line:
                continue
            prompt = t.prompt
            if line.startswith("#"):
                blocks.append(prompt + " " + line)
                continue
            out, err, code = t.run_line(line)
            body = (out + err).rstrip("\n")
            lines = body.splitlines() if body else []
            if len(lines) > max_lines:
                lines = lines[:max_lines] + ["… (" + str(len(lines) - max_lines) + " líneas más)"]
            blocks.append(prompt + " " + line + ("\n" + "\n".join(lines) if lines else ""))
        return "\n".join(blocks).replace("```", "'''")


    # ═════════════════════ Comprobaciones ═════════════════════
    def lab_paths(t):
        t1 = os.path.join(t.home, "Tema1")
        d = os.path.join(t1, "Datos")
        return {
            "T1": t1,
            "D": d,
            "O": os.path.join(t1, "Secuencias.txt"),
            "A": os.path.join(d, "aminoacidos.tt"),
            "L": os.path.join(d, "Secuencias.txt"),
        }


    def rd(path):
        with open(path, "rb") as fh:
            return fh.read()


    def md5(path):
        return hashlib.md5(rd(path)).hexdigest()


    def reads(t, target, names=READERS):
        for r in t.records:
            if r["name"] in names and r["out"]:
                for x in r["args"]:
                    if not x.startswith("-") and t.resolve(x, r["cwd"]) == target:
                        return True
                if r["fin"] and t.resolve(r["fin"], r["cwd"]) == target:
                    return True
        return False


    def ck_1(t, P, orig):
        pw = [r for r in t.records if r["name"] == "pwd"]
        return [
            ("Ejecutaste `pwd`", bool(pw), "El comando que imprime el directorio de trabajo es `pwd`."),
            ("La salida es una ruta absoluta (empieza por `/`)",
             any(r["out"].startswith("/") for r in pw), None),
        ]


    def ck_2(t, P, orig):
        ls = [r for r in t.records if r["name"] == "ls"]
        return [
            ("Ejecutaste `ls`", bool(ls), "`ls` = list."),
            ("Aparece la carpeta `Tema1`", any("Tema1" in r["out"].split() for r in ls), None),
        ]


    def ck_3(t, P, orig):
        return [("Ahora estás dentro de `Tema1`", t.cwd == P["T1"],
                 "Terminaste en `" + t.virt(t.cwd) + "`. Usa `cd Tema1`.")]


    def ck_4(t, P, orig):
        names = os.listdir(P["T1"])
        tip = None
        if any(n.lower() == "datos" and n != "Datos" for n in names):
            tip = "Linux distingue mayúsculas: la carpeta debe llamarse exactamente `Datos`."
        return [("Existe la carpeta `Tema1/Datos`", os.path.isdir(P["D"]), tip or "Usa `mkdir Datos`.")]


    def ck_5(t, P, orig):
        ok = os.path.isfile(P["L"]) and not os.path.islink(P["L"])
        return [
            ("Existe la copia `Datos/Secuencias.txt`", ok, "Sintaxis: `cp ORIGEN DESTINO`. Estás en `~/Tema1`."),
            ("La copia es idéntica al original (mismo md5)",
             ok and os.path.isfile(P["O"]) and md5(P["L"]) == md5(P["O"]), None),
            ("El original sigue en `Tema1`", os.path.isfile(P["O"]),
             "Con `cp` el original no desaparece. ¿Usaste `mv`?"),
        ]


    def ck_6(t, P, orig):
        names = sorted(os.listdir(P["D"])) if os.path.isdir(P["D"]) else []
        same = os.path.isfile(P["A"]) and os.path.isfile(P["O"]) and md5(P["A"]) == md5(P["O"])
        return [
            ("En `Datos` solo queda `aminoacidos.tt`", names == ["aminoacidos.tt"],
             "Contenido actual de `Datos`: " + (", ".join(names) or "(vacío)")),
            ("Mismo contenido que el original (md5): renombrar no cambia los datos", same,
             "`mv ORIGEN DESTINO` renombra. Hazlo sobre la copia de `Datos`, no sobre el original."),
        ]


    def ck_7(t, P, orig):
        return [("Leíste `aminoacidos.tt` con `cat`, `less`, `more`, `head` o `tail`",
                 reads(t, P["A"]), "Estás en `Datos`: prueba `cat aminoacidos.tt`.")]


    def ck_8(t, P, orig):
        islk = os.path.islink(P["L"])
        works = (islk and os.path.exists(P["L"])
                 and os.path.realpath(P["L"]) == os.path.realpath(P["O"]))
        tip = "Crea el enlace con `ln -s DESTINO NOMBRE`."
        if islk and not works:
            tip = ("El enlace existe pero está **roto**: la ruta del destino se interpreta desde la "
                   "carpeta donde vive el enlace. El original está un nivel por encima → `../Secuencias.txt`. "
                   "Vuelve a escribir todos los comandos (se parte de cero).")
        return [
            ("Existe el enlace simbólico `Datos/Secuencias.txt`", islk, "Crea el enlace con `ln -s DESTINO NOMBRE`."),
            ("El enlace funciona (apunta al original, no está roto)", works, tip),
        ]


    def ck_9(t, P, orig):
        ok = reads(t, P["L"])
        text = orig.decode("utf-8", errors="replace")
        same = any(
            r["name"] in READERS and r["out"].rstrip("\n") in text
            for r in t.records if r["out"] and ok
        )
        return [
            ("Leíste el enlace `Secuencias.txt` (no `../Secuencias.txt`)", ok,
             "Estás en `Datos`: `cat Secuencias.txt` lee el enlace."),
            ("Ves el contenido del original a través del enlace", same, None),
        ]


    def ck_10(t, P, orig):
        new = rd(P["O"]) if os.path.isfile(P["O"]) else b""
        added = new.startswith(orig) and len(new) > len(orig)
        text_added = new[len(orig):].decode("utf-8", errors="replace").strip() if added else ""
        tip = "Usa `echo \"texto\" >> archivo` (con `>>`, que añade; un solo `>` sobrescribe)."
        if any(r["name"] in ("nano", "vi", "vim") for r in t.records):
            tip = "nano no se puede usar dentro del navegador: emúlalo con `echo \"...\" >> Secuencias.txt`."
        elif new and not new.startswith(orig):
            tip = "El original ha cambiado de forma distinta a añadir una línea. ¿Usaste `>` en lugar de `>>`?"
        copy_ok = os.path.isfile(P["A"]) and md5(P["A"]) == hashlib.md5(orig).hexdigest()
        link_ok = os.path.islink(P["L"]) and os.path.exists(P["L"]) and rd(P["L"]) == new
        reread = bool(text_added) and any(
            r["name"] in READERS and text_added in r["out"] for r in t.records)
        return [
            ("El original (`Tema1/Secuencias.txt`) tiene una línea nueva al final", added, tip),
            ("Volviste a leer el original y se ve la línea nueva", reread,
             "Léelo después de editarlo: `cat Secuencias.txt` o `tail Secuencias.txt` (desde `Tema1`)."),
            ("La copia `aminoacidos.tt` NO cambió (es independiente)", copy_ok, None),
            ("El enlace `Datos/Secuencias.txt` SÍ muestra la línea nueva (apunta al original)", link_ok, None),
        ]


    def ck_11(t, P, orig):
        return [
            ("`aminoacidos.tt` ya no existe", not os.path.lexists(P["A"]),
             "Desde `Tema1`: `rm Datos/aminoacidos.tt`."),
            ("El original sigue intacto", os.path.isfile(P["O"]), "¡Has borrado el original!"),
            ("El enlace simbólico sigue funcionando", os.path.islink(P["L"]) and os.path.exists(P["L"]),
             "Solo debías borrar la copia."),
        ]


    CHECKS = {1: ck_1, 2: ck_2, 3: ck_3, 4: ck_4, 5: ck_5, 6: ck_6,
              7: ck_7, 8: ck_8, 9: ck_9, 10: ck_10, 11: ck_11}


    def run_exercise(n, text, seed=None):
        """Ejecuta los comandos del alumno desde el estado correcto del ejercicio n y los valida."""
        t = build_lab(seed, n - 1)
        try:
            P = lab_paths(t)
            orig = rd(P["O"])
            transcript = run_session(t, text)
            checks = CHECKS[n](t, P, orig)
        finally:
            shutil.rmtree(t.root, ignore_errors=True)
        return {"transcript": transcript, "checks": checks}


    def run_free(text, seed=None, upto=0):
        """Terminal libre: ejecuta el guion desde un laboratorio nuevo (con `upto` ejercicios ya hechos)."""
        t = build_lab(seed, upto)
        try:
            return run_session(t, text, max_lines=60)
        finally:
            shutil.rmtree(t.root, ignore_errors=True)

    return SOLUTIONS, run_exercise, run_free, start_prompt


# ═════════════════════════ Helpers de interfaz ═════════════════════════
@app.cell(hide_code=True)
def _(SOLUTIONS, mo, start_prompt):
    def console_block(text):
        return mo.md("```console\n" + text + "\n```")

    def exercise_card(n, titulo, enunciado, concepto, pista, form):
        sol = "\n".join(SOLUTIONS[n - 1])
        return mo.vstack([
            mo.md("---\n## " + str(n) + " · " + titulo + "\n> *" + enunciado + "*\n\n" + concepto),
            mo.md("📍 Partes de: `" + start_prompt(n) + "`"),
            form,
            mo.accordion({
                "💡 Pista": mo.md(pista),
                "✅ Solución de referencia": mo.md("```bash\n" + sol + "\n```"),
            }),
        ])

    def render_result(res):
        parts = [console_block(res["transcript"])]
        for label, good, tip in res["checks"]:
            msg = ("✔ " if good else "✘ ") + label
            if (not good) and tip:
                msg += "\n\n💡 " + tip
            parts.append(mo.callout(mo.md(msg), kind="success" if good else "danger"))
        done = all(c[1] for c in res["checks"])
        parts.append(mo.callout(
            mo.md("🎉 **¡Ejercicio completado!**" if done
                  else "Revisa los puntos marcados con ✘, corrige y vuelve a pulsar **▶ Ejecutar**."),
            kind="success" if done else "warn",
        ))
        return mo.vstack(parts)

    return console_block, exercise_card, render_result


# ═════════════════════════ 1 · ¿En qué ruta estoy? ═════════════════════════
@app.cell(hide_code=True)
def _(exercise_card, mo):
    f1 = mo.ui.form(
        mo.ui.text_area(placeholder="Escribe aquí tus comandos (uno por línea)…", full_width=True),
        submit_button_label="▶ Ejecutar",
        bordered=False,
    )
    exercise_card(
        1,
        r"""¿En qué ruta estoy?""",
        r"""Identifica la ruta completa en la que te encuentras una vez que has iniciado la terminal.""",
        r"""Todo en Linux parte de un **directorio de trabajo**: la carpeta en la que estás ahora mismo. La ruta absoluta empieza siempre por `/`. Aquí verás la ruta del laboratorio virtual (en tu ordenador será otra).""",
        r"""El comando se llama `pwd` (*print working directory*).""",
        f1,
    )
    return (f1,)


@app.cell(hide_code=True)
def _(SEED, f1, mo, render_result, run_exercise):
    mo.stop(
        not f1.value,
        mo.callout(mo.md("✍️ Escribe tus comandos y pulsa **▶ Ejecutar**."), kind="neutral"),
    )
    render_result(run_exercise(1, f1.value, SEED))
    return


# ═════════════════════════ 2 · Listar archivos y carpetas ═════════════════════════
@app.cell(hide_code=True)
def _(exercise_card, mo):
    f2 = mo.ui.form(
        mo.ui.text_area(placeholder="Escribe aquí tus comandos (uno por línea)…", full_width=True),
        submit_button_label="▶ Ejecutar",
        bordered=False,
    )
    exercise_card(
        2,
        r"""Listar archivos y carpetas""",
        r"""Genera el listado de archivos y carpetas que se encuentran en la posición en la que te encuentras.""",
        r"""Variantes útiles: `ls -l` (formato largo: permisos, dueño, tamaño), `ls -a` (incluye ocultos). Verás **una sola carpeta: `Tema1`** (todavía no hemos entrado en ella).""",
        r"""`ls` = *list*.""",
        f2,
    )
    return (f2,)


@app.cell(hide_code=True)
def _(SEED, f2, mo, render_result, run_exercise):
    mo.stop(
        not f2.value,
        mo.callout(mo.md("✍️ Escribe tus comandos y pulsa **▶ Ejecutar**."), kind="neutral"),
    )
    render_result(run_exercise(2, f2.value, SEED))
    return


# ═════════════════════════ 3 · Entrar en la carpeta Tema1 ═════════════════════════
@app.cell(hide_code=True)
def _(exercise_card, mo):
    f3 = mo.ui.form(
        mo.ui.text_area(placeholder="Escribe aquí tus comandos (uno por línea)…", full_width=True),
        submit_button_label="▶ Ejecutar",
        bordered=False,
    )
    exercise_card(
        3,
        r"""Entrar en la carpeta `Tema1`""",
        r"""Navega hasta dentro de la carpeta descargada como Tema1.""",
        r"""`cd` = *change directory*. Fíjate en que **el prompt cambia** (`~` → `~/Tema1`). Atajos: `.` = aquí · `..` = carpeta superior · `~` = tu carpeta personal.""",
        r"""`cd Tema1`. Con `cd tema1` (minúscula) falla: Linux distingue mayúsculas.""",
        f3,
    )
    return (f3,)


@app.cell(hide_code=True)
def _(SEED, f3, mo, render_result, run_exercise):
    mo.stop(
        not f3.value,
        mo.callout(mo.md("✍️ Escribe tus comandos y pulsa **▶ Ejecutar**."), kind="neutral"),
    )
    render_result(run_exercise(3, f3.value, SEED))
    return


# ═════════════════════════ 4 · Crear la carpeta Datos ═════════════════════════
@app.cell(hide_code=True)
def _(exercise_card, mo):
    f4 = mo.ui.form(
        mo.ui.text_area(placeholder="Escribe aquí tus comandos (uno por línea)…", full_width=True),
        submit_button_label="▶ Ejecutar",
        bordered=False,
    )
    exercise_card(
        4,
        r"""Crear la carpeta `Datos`""",
        r"""Crea una nueva carpeta denominada "Datos".""",
        r"""`mkdir` = *make directory*. Linux distingue mayúsculas: `Datos` ≠ `datos`.""",
        r"""`mkdir Datos`. Comprueba con `ls`.""",
        f4,
    )
    return (f4,)


@app.cell(hide_code=True)
def _(SEED, f4, mo, render_result, run_exercise):
    mo.stop(
        not f4.value,
        mo.callout(mo.md("✍️ Escribe tus comandos y pulsa **▶ Ejecutar**."), kind="neutral"),
    )
    render_result(run_exercise(4, f4.value, SEED))
    return


# ═════════════════════════ 5 · Copiar Secuencias.txt dentro de Datos ═════════════════════════
@app.cell(hide_code=True)
def _(exercise_card, mo):
    f5 = mo.ui.form(
        mo.ui.text_area(placeholder="Escribe aquí tus comandos (uno por línea)…", full_width=True),
        submit_button_label="▶ Ejecutar",
        bordered=False,
    )
    exercise_card(
        5,
        r"""Copiar `Secuencias.txt` dentro de `Datos`""",
        r"""Haz una copia del archivo Secuencias.txt dentro de la nueva carpeta "Datos".""",
        r"""`cp ORIGEN DESTINO`. Si el destino es una carpeta, el archivo conserva su nombre. Una **copia es un archivo nuevo e independiente**: lo puedes comprobar con `md5sum` (mismo contenido ⇒ mismo código).""",
        r"""`cp Secuencias.txt Datos/`. Para comprobar: `ls Datos` y `md5sum Secuencias.txt Datos/Secuencias.txt`.""",
        f5,
    )
    return (f5,)


@app.cell(hide_code=True)
def _(SEED, f5, mo, render_result, run_exercise):
    mo.stop(
        not f5.value,
        mo.callout(mo.md("✍️ Escribe tus comandos y pulsa **▶ Ejecutar**."), kind="neutral"),
    )
    render_result(run_exercise(5, f5.value, SEED))
    return


# ═════════════════════════ 6 · Renombrar la copia a aminoacidos.tt ═════════════════════════
@app.cell(hide_code=True)
def _(exercise_card, mo):
    f6 = mo.ui.form(
        mo.ui.text_area(placeholder="Escribe aquí tus comandos (uno por línea)…", full_width=True),
        submit_button_label="▶ Ejecutar",
        bordered=False,
    )
    exercise_card(
        6,
        r"""Renombrar la copia a `aminoacidos.tt`""",
        r"""Cambia el nombre del archivo Secuencias.txt y denomínalo "aminoacidos.tt".""",
        r"""`mv ORIGEN DESTINO` sirve para **mover y para renombrar**. Entra en `Datos` para renombrar **la copia** (no el original). Cambiar el nombre **no cambia el contenido** (el md5 es el mismo).""",
        r"""Dos comandos: `cd Datos` y `mv Secuencias.txt aminoacidos.tt` (en líneas separadas o unidos con `&&`).""",
        f6,
    )
    return (f6,)


@app.cell(hide_code=True)
def _(SEED, f6, mo, render_result, run_exercise):
    mo.stop(
        not f6.value,
        mo.callout(mo.md("✍️ Escribe tus comandos y pulsa **▶ Ejecutar**."), kind="neutral"),
    )
    render_result(run_exercise(6, f6.value, SEED))
    return


# ═════════════════════════ 7 · Leer aminoacidos.tt ═════════════════════════
@app.cell(hide_code=True)
def _(exercise_card, mo):
    f7 = mo.ui.form(
        mo.ui.text_area(placeholder="Escribe aquí tus comandos (uno por línea)…", full_width=True),
        submit_button_label="▶ Ejecutar",
        bordered=False,
    )
    exercise_card(
        7,
        r"""Leer `aminoacidos.tt`""",
        r"""Lee el contenido del archivo "aminoacidos.tt".""",
        r"""Tres lectores de texto:

| Comando | Comportamiento |
|---|---|
| `cat` | vuelca **todo** de golpe (no interactivo) |
| `more` | por pantallas, solo hacia abajo |
| `less` | por pantallas, **arriba y abajo** (`q` para salir) |

Aquí `more` y `less` se comportan como `cat` (no hay modo interactivo en el navegador). Con `wc -l` cuentas líneas: 4 líneas = 1 lectura FASTQ.""",
        r"""`cat aminoacidos.tt` (estás dentro de `Datos`).""",
        f7,
    )
    return (f7,)


@app.cell(hide_code=True)
def _(SEED, f7, mo, render_result, run_exercise):
    mo.stop(
        not f7.value,
        mo.callout(mo.md("✍️ Escribe tus comandos y pulsa **▶ Ejecutar**."), kind="neutral"),
    )
    render_result(run_exercise(7, f7.value, SEED))
    return


# ═════════════════════════ 8 · Enlace simbólico a Secuencias.txt ═════════════════════════
@app.cell(hide_code=True)
def _(exercise_card, mo):
    f8 = mo.ui.form(
        mo.ui.text_area(placeholder="Escribe aquí tus comandos (uno por línea)…", full_width=True),
        submit_button_label="▶ Ejecutar",
        bordered=False,
    )
    exercise_card(
        8,
        r"""Enlace simbólico a `Secuencias.txt`""",
        r"""Crea un enlace simbólico al archivo Secuencias.txt dentro de la nueva carpeta creada.""",
        r"""`ln -s DESTINO NOMBRE_DEL_ENLACE`. Sin `-s` crea un *enlace duro*.

⚠️ **Error clásico:** la ruta del destino se interpreta **desde la carpeta donde vive el enlace**. Estás en `Datos` y `Secuencias.txt` está **un nivel por encima**. Prueba primero el intento incorrecto (`ln -s Secuencias.txt Secuencias.txt`, luego `ls -l` y `cat Secuencias.txt`) y después corrígelo (`rm` del enlace roto y crearlo bien). Puedes hacerlo todo en el mismo envío.""",
        r"""El destino correcto es `../Secuencias.txt`: `ln -s ../Secuencias.txt Secuencias.txt`.""",
        f8,
    )
    return (f8,)


@app.cell(hide_code=True)
def _(SEED, f8, mo, render_result, run_exercise):
    mo.stop(
        not f8.value,
        mo.callout(mo.md("✍️ Escribe tus comandos y pulsa **▶ Ejecutar**."), kind="neutral"),
    )
    render_result(run_exercise(8, f8.value, SEED))
    return


# ═════════════════════════ 9 · Leer el enlace simbólico ═════════════════════════
@app.cell(hide_code=True)
def _(exercise_card, mo):
    f9 = mo.ui.form(
        mo.ui.text_area(placeholder="Escribe aquí tus comandos (uno por línea)…", full_width=True),
        submit_button_label="▶ Ejecutar",
        bordered=False,
    )
    exercise_card(
        9,
        r"""Leer el enlace simbólico""",
        r"""Lee el contenido del nuevo enlace simbólico de Secuencias.txt.""",
        r"""Un enlace simbólico se lee **igual que un archivo normal**: el sistema sigue el "atajo" hasta el archivo real.""",
        r"""Estando en `Datos`: `cat Secuencias.txt`.""",
        f9,
    )
    return (f9,)


@app.cell(hide_code=True)
def _(SEED, f9, mo, render_result, run_exercise):
    mo.stop(
        not f9.value,
        mo.callout(mo.md("✍️ Escribe tus comandos y pulsa **▶ Ejecutar**."), kind="neutral"),
    )
    render_result(run_exercise(9, f9.value, SEED))
    return


# ═════════════════════════ 10 · Añadir una línea al original y volver a leerlo ═════════════════════════
@app.cell(hide_code=True)
def _(exercise_card, mo):
    f10 = mo.ui.form(
        mo.ui.text_area(placeholder="Escribe aquí tus comandos (uno por línea)…", full_width=True),
        submit_button_label="▶ Ejecutar",
        bordered=False,
    )
    exercise_card(
        10,
        r"""Añadir una línea al original y volver a leerlo""",
        r"""Añade una nueva línea al archivo de texto utilizando el editor nano y vuelve a leer el contenido del archivo original Secuencias.txt que se encuentra fuera de la carpeta.""",
        r"""**En una terminal real** usarías `cd ..`, luego `nano Secuencias.txt` (escribes la línea, `Ctrl+O` guarda, `Ctrl+X` sale) y por último `cat` o `tail`.

`nano` es interactivo y no se puede usar en el navegador, así que aquí lo emulamos con `echo "…" >> archivo`, que **añade** una línea al final. ⚠️ `>>` añade; un solo `>` **sobrescribe** el archivo entero.

Compara los tres archivos tras editar el original:

| Archivo | ¿Qué es? | ¿Ve la línea nueva? |
|---|---|---|
| `Tema1/Secuencias.txt` | el original | ✔ (lo hemos editado) |
| `Datos/aminoacidos.tt` | una copia (vida propia) | ✘ |
| `Datos/Secuencias.txt` | un enlace simbólico (atajo) | ✔ |""",
        r"""`cd ..`, luego `echo "Estoy añadiendo una nueva línea" >> Secuencias.txt` y `cat Secuencias.txt`. Para comparar: `tail -n 2 Datos/aminoacidos.tt Datos/Secuencias.txt`.""",
        f10,
    )
    return (f10,)


@app.cell(hide_code=True)
def _(SEED, f10, mo, render_result, run_exercise):
    mo.stop(
        not f10.value,
        mo.callout(mo.md("✍️ Escribe tus comandos y pulsa **▶ Ejecutar**."), kind="neutral"),
    )
    render_result(run_exercise(10, f10.value, SEED))
    return


# ═════════════════════════ 11 · Eliminar aminoacidos.tt ═════════════════════════
@app.cell(hide_code=True)
def _(exercise_card, mo):
    f11 = mo.ui.form(
        mo.ui.text_area(placeholder="Escribe aquí tus comandos (uno por línea)…", full_width=True),
        submit_button_label="▶ Ejecutar",
        bordered=False,
    )
    exercise_card(
        11,
        r"""Eliminar `aminoacidos.tt`""",
        r"""Elimina el archivo aminoacidos.tt.""",
        r"""`rm` = *remove*. ⚠️ En Linux **no hay papelera**. Para borrar carpetas haría falta `rm -r`.""",
        r"""Estás en `Tema1`: `rm Datos/aminoacidos.tt`.""",
        f11,
    )
    return (f11,)


@app.cell(hide_code=True)
def _(SEED, f11, mo, render_result, run_exercise):
    mo.stop(
        not f11.value,
        mo.callout(mo.md("✍️ Escribe tus comandos y pulsa **▶ Ejecutar**."), kind="neutral"),
    )
    render_result(run_exercise(11, f11.value, SEED))
    return


# ═════════════════════════ Hoja de respuestas ═════════════════════════
@app.cell(hide_code=True)
def _(SOLUTIONS, mo):
    _titulos = [
        "Ruta actual", "Listar archivos y carpetas", "Entrar en Tema1", "Crear la carpeta Datos",
        "Copiar Secuencias.txt dentro de Datos", "Renombrar la copia", "Leer aminoacidos.tt",
        "Enlace simbólico al original (un nivel por encima)", "Leer el enlace simbólico",
        "Editar el original (nano en una terminal real) y releerlo", "Eliminar aminoacidos.tt",
    ]
    _lineas = []
    for _i, _cmds in enumerate(SOLUTIONS):
        _lineas.append(f"# {_i + 1}. {_titulos[_i]}")
        _lineas.extend(_cmds)
        _lineas.append("")
    _hoja = "\n".join(_lineas).replace(
        'echo "Estoy añadiendo una nueva línea" >> Secuencias.txt',
        'nano Secuencias.txt           # Ctrl+O, Enter, Ctrl+X  (aquí: echo "..." >> Secuencias.txt)',
    )

    mo.vstack([
        mo.md(
            r"""
            ---
            ## 📋 Hoja de respuestas (para pegar en el documento y entregar en PDF)
            """
        ),
        mo.md("```bash\n" + _hoja + "\n```"),
        mo.md("### Preguntas de repaso"),
        mo.accordion({
            "1. ¿Por qué falla el enlace del ejercicio 8 con `ln -s Secuencias.txt Secuencias.txt` desde `Datos`?":
                mo.md("Porque la ruta del destino se interpreta **desde la carpeta donde vive el enlace**. "
                      "En `Datos` no existe ningún `Secuencias.txt` (el original está un nivel por encima), "
                      "así que el enlace apunta a sí mismo y queda **roto**. La ruta correcta es `../Secuencias.txt`."),
            "2. ¿Por qué la copia no recibe la línea nueva y el enlace sí?":
                mo.md("La **copia** es un archivo independiente (sus propios datos). El **enlace simbólico** "
                      "solo guarda una ruta hacia el original, así que al leerlo siempre ves el contenido actual del original."),
            "3. ¿Qué pasaría con el enlace si borráramos el original?":
                mo.md("Quedaría **roto** (*dangling*): `ls -l` mostraría el destino, pero `cat` daría "
                      "*No such file or directory*. Pruébalo en la terminal libre con el estado "
                      "«10 ejercicios hechos»: `rm Secuencias.txt` y luego `cat Datos/Secuencias.txt`."),
        }),
    ])
    return


# ═════════════════════════ Terminal libre ═════════════════════════
@app.cell(hide_code=True)
def _(mo):
    start_sel = mo.ui.dropdown(
        options={
            "Laboratorio limpio (solo Secuencias.txt)": 0,
            "Con los 10 primeros ejercicios hechos (copia + enlace)": 10,
            "Con los 11 ejercicios hechos": 11,
        },
        value="Laboratorio limpio (solo Secuencias.txt)",
        label="Estado inicial: ",
    )
    ffree = mo.ui.form(
        mo.ui.text_area(placeholder="Escribe aquí tus comandos (uno por línea)…", full_width=True),
        submit_button_label="▶ Ejecutar",
        bordered=False,
    )
    mo.vstack([
        mo.md(
            r"""
            ---
            ## 🧪 Terminal libre

            Experimenta sin comprobaciones. Escribe los comandos que quieras (uno por línea) y pulsa
            **▶ Ejecutar**: se ejecutan **desde el estado inicial elegido**, así que cada envío empieza de cero
            (incluye todos los comandos que quieras probar en el mismo envío).

            Disponibles: `pwd` `ls` `cd` `mkdir` `rmdir` `touch` `cp` `mv` `rm` `ln -s` `cat` `less` `more`
            `head` `tail` `wc` `md5sum` `readlink` `test` `echo` · operadores `&&` `||` `;` `|` `<` `>` `>>`
            """
        ),
        start_sel,
        ffree,
    ])
    return ffree, start_sel


@app.cell(hide_code=True)
def _(SEED, ffree, mo, run_free, start_sel):
    mo.stop(
        not ffree.value,
        mo.callout(mo.md("✍️ Escribe tus comandos y pulsa **▶ Ejecutar**."), kind="neutral"),
    )
    mo.md("```console\n" + run_free(ffree.value, SEED, start_sel.value) + "\n```")
    return


if __name__ == "__main__":
    app.run()
