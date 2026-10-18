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

        Este cuaderno resuelve, paso a paso, los **11 ejercicios del Tema 1.1**, ejecutándose
        íntegramente en el navegador con Pyodide. No requiere instalar nada.

        **Cómo funciona**

        - La "terminal" es una **emulación en Python** (no hay bash real en el navegador), pero
          los comandos esenciales (`pwd`, `ls`, `cd`, `mkdir`, `cp`, `mv`, `cat`, `ln -s`, `rm`,
          `wc`, `md5sum`, `tail`, `test`, `echo`…) funcionan igual.
        - La terminal **recuerda dónde estás** (como una real). Tras un `cd`, los comandos siguientes
          se ejecutan en esa carpeta.
        - Ejecuta las celdas **de arriba abajo**.
        - Para volver a empezar, pulsa **↺ Reiniciar laboratorio**.
        - En la sección **📤 Subir archivos** puedes cargar tu propio `Secuencias.txt` (o un `.zip`
          con la carpeta `Tema1`) para trabajar con tus datos reales.
        """
    )
    return (mo,)


# ═════════════════════════ Imports ═════════════════════════
@app.cell(hide_code=True)
def _():
    import os
    import tempfile
    import zipfile
    from pathlib import Path

    return Path, os, tempfile, zipfile


# ═════════════════════════ Botón reset ═════════════════════════
@app.cell(hide_code=True)
def _(mo):
    reset = mo.ui.button(label="↺ Reiniciar laboratorio", kind="warn")
    reset
    return (reset,)


# ═════════════════════════ Setup del laboratorio ═════════════════════════
@app.cell(hide_code=True)
def _(Path, mo, os, reset, tempfile):
    reset.value  # al pulsar el botón, esta celda y todas las siguientes se repiten

    import shutil as _shutil

    _DEMO = (
        "@A01196:35:H2YTJDRX2:1:2101:29677:1376 1:N:0:CGGCTATG+ACGTCCTG\n"
        "CCAACAGGGTTGGTCTCCGTACGTTTCCTCACCTGCATTTCGTTCGTAGTCCCCGATGAATCG\n"
        "+\n"
        "FFFF,FFFFFFF,FFF,FFFFFFF:F:FFFF,::,FF,F:FFFF::FF,FFF:FFFFFF:FFFF\n"
    ) * 3

    def _find_tema1():
        """En local (fuera de WASM) intenta localizar la carpeta Tema1 del alumno."""
        try:
            if os.environ.get("TEMA1_DIR"):
                c = Path(os.environ["TEMA1_DIR"])
                if (c / "Secuencias.txt").exists():
                    return c
            try:
                base = Path(mo.notebook_dir() or ".")
            except Exception:
                base = Path(".")
            for cand in [base / "Tema1", base.parent / "Tema1", Path.cwd() / "Tema1"]:
                if (cand / "Secuencias.txt").exists():
                    return cand
        except Exception:
            pass
        return None

    # FS virtual del navegador:  <tmp>/home/alumno/Tema1/...
    LAB_ROOT = Path(tempfile.mkdtemp(prefix="lab1_"))
    HOME = LAB_ROOT / "home" / "alumno"
    HOME.mkdir(parents=True)
    _tema1 = HOME / "Tema1"

    _src = _find_tema1()
    _copied = False
    if _src is not None:
        try:
            _shutil.copytree(_src, _tema1)
            _copied = True
            _origen = f"copia de `{_src}`"
        except Exception:
            pass
    if not _copied:
        _tema1.mkdir(parents=True, exist_ok=True)
        (_tema1 / "Secuencias.txt").write_text(_DEMO)
        _origen = "datos de **demostración**"

    mo.md(
        f"Laboratorio listo en una carpeta temporal del **sistema de archivos virtual** "
        f"del navegador · contenido de `Tema1`: {_origen}."
    )
    return (HOME,)


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
            ## 📤 Subir tus archivos

            - **Archivos sueltos** (`Secuencias.txt`, `.fa`, `.fastq`…) → se copian a `~/Tema1/`.
              Si subes un `Secuencias.txt` nuevo, **sustituye** al de demostración.
            - **`.zip`** → se extrae en `~/`. Debe contener una carpeta `Tema1/` dentro.

            > ⚠️ Si subes archivos **después** de haber empezado los ejercicios, pulsa primero
            > **↺ Reiniciar laboratorio** para que se repitan las comprobaciones.
            """
        ),
        upload,
    ])
    return (upload,)


@app.cell(hide_code=True)
def _(HOME, mo, upload, zipfile):
    import io as _io

    _tema1 = HOME / "Tema1"
    _msgs = []

    if upload.value:
        for _f in upload.value:
            _name = _f.name
            _content = _f.contents
            if callable(_content):  # compatibilidad con versiones antiguas
                _content = _content()

            if _name.lower().endswith(".zip"):
                try:
                    with zipfile.ZipFile(_io.BytesIO(_content)) as _z:
                        _z.extractall(HOME)
                    _msgs.append(f"✔ `{_name}` → extraído en `~/`")
                except Exception as _e:
                    _msgs.append(f"✘ `{_name}`: {_e}")
            else:
                _tema1.mkdir(exist_ok=True)
                (_tema1 / _name).write_bytes(_content)
                _msgs.append(f"✔ `{_name}` → `~/Tema1/`")

    if _msgs:
        mo.md("**Archivos cargados:**\n\n" + "\n".join(f"- {m}" for m in _msgs))
    else:
        mo.md("*Todavía no has subido archivos: se usarán los **datos de demostración**.*")
    return ()


# ═════════════════════════ Mini-terminal (emulada en Python) ═════════════════════════
@app.cell(hide_code=True)
def _(HOME, mo, os):
    import hashlib
    import re
    import shlex
    import shutil

    class Terminal:
        """Mini-shell en Python: emula los comandos esenciales del Tema 1.1."""

        def __init__(self, home):
            self.home = os.path.normpath(str(home))
            self.cwd = self.home

        # ─── prompt ───
        @property
        def prompt(self):
            rel = os.path.relpath(self.cwd, self.home)
            return "alumno@lab:~$" if rel == "." else f"alumno@lab:~/{rel}$"

        # ─── resolución de rutas ───
        def _resolve(self, p):
            p = p.strip().strip("\"'") or "."
            if p == "~" or p.startswith("~/"):
                p = self.home + p[1:]
            elif not p.startswith("/"):
                p = os.path.join(self.cwd, p)
            return os.path.normpath(p)

        # ─── ejecución ───
        def run(self, cmd):
            """Ejecuta una línea con `&&`; devuelve (stdout, stderr)."""
            c = cmd.strip()
            if not c:
                return "", ""
            parts = [p.strip() for p in c.split("&&")]
            outs, errs = [], []
            for part in parts:
                out, err, code = self._run_single(part)
                if out:
                    outs.append(out)
                if err:
                    errs.append(err)
                if code != 0:
                    break
            return "\n".join(outs), "\n".join(errs)

        def _run_single(self, cmd):
            """Ejecuta un comando simple con redirecciones <, >, >>. Devuelve (out, err, code)."""
            cmd = cmd.strip()
            if not cmd:
                return "", "", 0

            # Negación para `test`
            negate = False
            if cmd.startswith("!"):
                rest = cmd[1:].lstrip()
                if rest.startswith("test"):
                    negate = True
                    cmd = rest

            # Redirecciones (con espacios alrededor)
            stdin_file = None
            stdout_file = None
            stdout_mode = "w"

            m = re.search(r"^(.*?)\s+>>\s+(\S+)\s*$", cmd)
            if m:
                cmd = m.group(1).strip()
                stdout_file, stdout_mode = m.group(2), "a"
            else:
                m = re.search(r"^(.*?)\s+>\s+(\S+)\s*$", cmd)
                if m:
                    cmd = m.group(1).strip()
                    stdout_file, stdout_mode = m.group(2), "w"

            m = re.search(r"^(.*?)\s+<\s+(\S+)\s*$", cmd)
            if m:
                cmd = m.group(1).strip()
                stdin_file = m.group(2)

            try:
                tokens = shlex.split(cmd)
            except ValueError as e:
                return "", f"bash: {e}\n", 1
            if not tokens:
                return "", "", 0

            command, args = tokens[0], tokens[1:]

            # stdin desde archivo
            stdin_content = None
            if stdin_file:
                p = self._resolve(stdin_file)
                try:
                    with open(p, "rb") as fh:
                        stdin_content = fh.read()
                except FileNotFoundError:
                    return "", f"bash: {stdin_file}: No such file or directory\n", 1
                except OSError as e:
                    return "", f"bash: {stdin_file}: {e}\n", 1

            out, err, code = self._dispatch(command, args, stdin_content)
            if negate:
                code = 0 if code != 0 else 1

            if stdout_file is not None:
                p = self._resolve(stdout_file)
                try:
                    with open(p, stdout_mode, encoding="utf-8") as fh:
                        if out:
                            fh.write(out)
                            if not out.endswith("\n"):
                                fh.write("\n")
                    out = ""
                except Exception as e:
                    return "", f"bash: {stdout_file}: {e}\n", 1

            return out, err, code

        # ─── despacho ───
        def _dispatch(self, command, args, stdin_content):
            try:
                if command == "echo":
                    text = " ".join(args)
                    return (text + "\n") if text else "\n", "", 0
                if command == "pwd":
                    return self.cwd + "\n", "", 0
                if command == "cd":
                    return self._cd(args[0] if args else "~")
                if command == "ls":
                    return self._ls(args)
                if command == "mkdir":
                    return self._mkdir(args)
                if command == "cp":
                    return self._cp(args)
                if command == "mv":
                    return self._mv(args)
                if command == "cat":
                    return self._cat(args, stdin_content)
                if command == "rm":
                    return self._rm(args)
                if command == "ln":
                    return self._ln(args)
                if command == "wc":
                    return self._wc(args, stdin_content)
                if command == "md5sum":
                    return self._md5sum(args, stdin_content)
                if command == "head":
                    return self._head_tail(args, stdin_content, "head")
                if command == "tail":
                    return self._head_tail(args, stdin_content, "tail")
                if command == "readlink":
                    return self._readlink(args)
                if command == "test":
                    return self._test(args)
                return "", f"bash: {command}: command not found\n", 127
            except Exception as e:
                return "", f"bash: {command}: {e}\n", 1

        # ─── implementación de cada comando ───
        def _cd(self, target):
            p = self._resolve(target)
            if os.path.isdir(p):
                self.cwd = p
                return "", "", 0
            return "", f"bash: cd: {target}: No such file or directory\n", 1

        def _ls(self, args):
            long = False
            show_hidden = False
            targets = []
            for a in args:
                if a in ("-l", "-lh", "-la", "-al", "-ll"):
                    long = True
                    if "a" in a:
                        show_hidden = True
                elif a in ("-a", "-A"):
                    show_hidden = True
                elif a.startswith("-"):
                    continue
                else:
                    targets.append(a)
            if not targets:
                targets = ["."]

            lines = []
            for t in targets:
                p = self._resolve(t)
                if not (os.path.exists(p) or os.path.islink(p)):
                    return "", f"ls: cannot access '{t}': No such file or directory\n", 2
                if os.path.isdir(p):
                    try:
                        names = sorted(os.listdir(p))
                    except OSError as e:
                        return "", f"ls: {e}\n", 1
                    if not show_hidden:
                        names = [n for n in names if not n.startswith(".")]
                    if not names:
                        continue
                    for n in names:
                        full = os.path.join(p, n)
                        if long:
                            if os.path.islink(full):
                                try:
                                    tgt = os.readlink(full)
                                except OSError:
                                    tgt = "?"
                                lines.append(f"lrwxrwxrwx 1 alumno alumno    ? {n} -> {tgt}")
                            elif os.path.isdir(full):
                                lines.append(f"drwxr-xr-x 2 alumno alumno 4096 {n}")
                            else:
                                sz = os.path.getsize(full)
                                lines.append(f"-rw-r--r-- 1 alumno alumno {sz:>4} {n}")
                        else:
                            lines.append(n)
                else:
                    lines.append(t)
            return "\n".join(lines) + ("\n" if lines else ""), "", 0

        def _mkdir(self, args):
            made = False
            for a in args:
                if a.startswith("-"):
                    continue
                p = self._resolve(a)
                try:
                    os.makedirs(p, exist_ok=False)
                    made = True
                except FileExistsError:
                    return "", f"mkdir: cannot create directory '{a}': File exists\n", 1
                except OSError as e:
                    return "", f"mkdir: {e}\n", 1
            return "", "", 0 if made or args else 1

        def _cp(self, args):
            if len(args) < 2:
                return "", "cp: missing operand\n", 1
            srcs, dst = args[:-1], args[-1]
            dst_p = self._resolve(dst)
            dst_is_dir = os.path.isdir(dst_p)
            if len(srcs) > 1 and not dst_is_dir:
                return "", f"cp: target '{dst}' is not a directory\n", 1
            for s in srcs:
                src_p = self._resolve(s)
                if not os.path.exists(src_p):
                    return "", f"cp: cannot stat '{s}': No such file or directory\n", 1
                target = os.path.join(dst_p, os.path.basename(src_p)) if dst_is_dir else dst_p
                try:
                    with open(src_p, "rb") as fi, open(target, "wb") as fo:
                        fo.write(fi.read())
                except Exception as e:
                    return "", f"cp: {e}\n", 1
            return "", "", 0

        def _mv(self, args):
            if len(args) < 2:
                return "", "mv: missing operand\n", 1
            src = self._resolve(args[0])
            dst = self._resolve(args[1])
            if not (os.path.exists(src) or os.path.islink(src)):
                return "", f"mv: cannot stat '{args[0]}': No such file or directory\n", 1
            target = os.path.join(dst, os.path.basename(src)) if os.path.isdir(dst) else dst
            try:
                os.rename(src, target)
            except Exception as e:
                return "", f"mv: {e}\n", 1
            return "", "", 0

        def _cat(self, args, stdin_content):
            if not args and stdin_content is not None:
                return stdin_content.decode("utf-8", errors="replace"), "", 0
            outs = []
            for a in args:
                p = self._resolve(a)
                try:
                    with open(p, "rb") as fh:
                        outs.append(fh.read().decode("utf-8", errors="replace"))
                except FileNotFoundError:
                    return "", f"cat: {a}: No such file or directory\n", 1
                except OSError as e:
                    return "", f"cat: {a}: {e}\n", 1
            return "".join(outs), "", 0

        def _rm(self, args):
            recursive = False
            targets = []
            for a in args:
                if a in ("-r", "-R", "-rf", "-fr", "-fR", "-Rf"):
                    recursive = True
                elif a.startswith("-"):
                    continue
                else:
                    targets.append(a)
            for t in targets:
                p = self._resolve(t)
                try:
                    if os.path.islink(p):
                        os.unlink(p)
                    elif os.path.isdir(p):
                        if not recursive:
                            return "", f"rm: cannot remove '{t}': Is a directory\n", 1
                        shutil.rmtree(p)
                    elif os.path.exists(p):
                        os.remove(p)
                    else:
                        return "", f"rm: cannot remove '{t}': No such file or directory\n", 1
                except OSError as e:
                    return "", f"rm: {e}\n", 1
            return "", "", 0

        def _ln(self, args):
            symbolic = False
            rest = []
            for a in args:
                if a == "-s":
                    symbolic = True
                elif a.startswith("-"):
                    continue
                else:
                    rest.append(a)
            if len(rest) < 2:
                return "", "ln: missing operand\n", 1
            target, link_name = rest[0], rest[1]
            link_p = self._resolve(link_name)
            try:
                if symbolic:
                    os.symlink(target, link_p)
                else:
                    os.link(self._resolve(target), link_p)
            except FileExistsError:
                return "", f"ln: failed to create {'symbolic ' if symbolic else ''}link '{link_name}': File exists\n", 1
            except OSError as e:
                return "", f"ln: {e}\n", 1
            return "", "", 0

        def _wc(self, args, stdin_content):
            count_l = False
            targets = []
            for a in args:
                if a == "-l":
                    count_l = True
                elif a.startswith("-"):
                    continue
                else:
                    targets.append(a)

            def fmt(content, name=None):
                n = content.count(b"\n")
                if count_l:
                    return f"{n}" + (f" {name}" if name else "")
                return f"{n} {len(content.split())} {len(content)}" + (f" {name}" if name else "")

            if not targets and stdin_content is not None:
                return fmt(stdin_content) + "\n", "", 0

            outs = []
            for t in targets:
                p = self._resolve(t)
                try:
                    with open(p, "rb") as fh:
                        content = fh.read()
                except FileNotFoundError:
                    return "", f"wc: {t}: No such file or directory\n", 1
                outs.append(fmt(content, t))
            return "\n".join(outs) + "\n", "", 0

        def _md5sum(self, args, stdin_content):
            if not args and stdin_content is not None:
                return f"{hashlib.md5(stdin_content).hexdigest()}  -\n", "", 0
            outs = []
            for t in args:
                p = self._resolve(t)
                try:
                    with open(p, "rb") as fh:
                        content = fh.read()
                except FileNotFoundError:
                    return "", f"md5sum: {t}: No such file or directory\n", 1
                outs.append(f"{hashlib.md5(content).hexdigest()}  {t}")
            return "\n".join(outs) + ("\n" if outs else ""), "", 0

        def _head_tail(self, args, stdin_content, mode):
            n = 10
            targets = []
            i = 0
            while i < len(args):
                a = args[i]
                if a == "-n" and i + 1 < len(args):
                    try:
                        n = int(args[i + 1])
                    except ValueError:
                        pass
                    i += 2
                    continue
                if a.startswith("-n") and len(a) > 2:
                    try:
                        n = int(a[2:])
                    except ValueError:
                        pass
                elif a.startswith("-") and a[1:].isdigit():
                    n = int(a[1:])
                elif a.startswith("-"):
                    pass
                else:
                    targets.append(a)
                i += 1

            def process(text):
                lines = text.splitlines(keepends=True)
                return "".join(lines[:n] if mode == "head" else (lines[-n:] if n > 0 else []))

            if not targets and stdin_content is not None:
                return process(stdin_content.decode("utf-8", errors="replace")), "", 0

            outs = []
            for idx, t in enumerate(targets):
                p = self._resolve(t)
                try:
                    with open(p, "rb") as fh:
                        text = fh.read().decode("utf-8", errors="replace")
                except FileNotFoundError:
                    return "", f"{mode}: cannot open '{t}' for reading: No such file or directory\n", 1
                if len(targets) > 1:
                    if idx > 0:
                        outs.append("")
                    outs.append(f"==> {t} <==")
                outs.append(process(text))
            return "\n".join(outs) + ("" if not outs else ""), "", 0

        def _readlink(self, args):
            outs = []
            for a in args:
                if a.startswith("-"):
                    continue
                p = self._resolve(a)
                if not os.path.islink(p):
                    return "", f"readlink: {a}: Invalid argument\n", 1
                outs.append(os.readlink(p))
            return ("\n".join(outs) + "\n") if outs else "", "", 0

        def _test(self, args):
            if not args:
                return "", "", 1
            op, rest = args[0], args[1:]
            if op in ("-e", "-f", "-d", "-L", "-h") and rest:
                p = self._resolve(rest[0])
                checks = {
                    "-e": os.path.exists,
                    "-f": os.path.isfile,
                    "-d": os.path.isdir,
                    "-L": os.path.islink,
                    "-h": os.path.islink,
                }
                return "", "", 0 if checks[op](p) else 1
            return "", "", 1

        # ─── helpers de presentación ───
        def out(self, cmd):
            """Solo stdout, sin espacios sobrantes (para las comprobaciones)."""
            return self.run(cmd)[0].strip()

        def sh(self, script, max_lines=12):
            """Ejecuta una orden por línea y devuelve la 'sesión' formateada."""
            blocks = []
            for line in [l for l in script.strip().splitlines() if l.strip()]:
                prompt = self.prompt  # prompt ANTES de ejecutar
                out, err = self.run(line)
                lines = out.splitlines()
                if len(lines) > max_lines:
                    lines = lines[:max_lines] + [f"… ({len(lines) - max_lines} líneas más)"]
                lines += [f"[stderr] {l}" for l in err.splitlines()]
                body = "\n".join(lines)
                blocks.append(f"{prompt} {line}" + (f"\n{body}" if body else ""))
            return mo.md("```console\n" + "\n".join(blocks) + "\n```")

    term = Terminal(HOME)

    def check(label, cond):
        return mo.callout(
            mo.md(("✔ " if cond else "✘ ") + label),
            kind="success" if cond else "danger",
        )

    return check, term


# ═════════════════════════ 1 · pwd ═════════════════════════
@app.cell(hide_code=True)
def _(mo):
    mo.md(
        r"""
        ---
        ## 1 · ¿En qué ruta estoy?
        > *Identifica la ruta completa en la que te encuentras una vez que has iniciado la terminal.*

        **Pista:** `pwd` = *print working directory*. Imprime la **ruta absoluta** del directorio
        actual (en Linux empieza siempre por `/`). En tu ordenador la ruta será distinta.
        """
    )
    return


@app.cell
def _(check, mo, term):
    _s = term.sh("pwd")
    e1 = mo.vstack([
        _s,
        check("la ruta es absoluta (empieza por `/`)", term.out("pwd").startswith("/")),
    ])
    e1
    return (e1,)


# ═════════════════════════ 2 · ls ═════════════════════════
@app.cell(hide_code=True)
def _(e1, mo):
    e1
    mo.md(
        r"""
        ---
        ## 2 · Listar archivos y carpetas
        > *Genera el listado de archivos y carpetas que se encuentran en la posición en la que te encuentras.*

        **Pista:** `ls` = *list*. Variantes: `ls -l` (formato largo: permisos, dueño, tamaño, fecha),
        `ls -a` (incluye ocultos), `ls -lh` (tamaños legibles).
        Verás **una sola carpeta: `Tema1`** (todavía no hemos entrado en ella).
        """
    )
    return


@app.cell
def _(check, e1, mo, term):
    e1
    e2 = mo.vstack([
        term.sh("ls"),
        check("aparece la carpeta `Tema1`", "Tema1" in term.out("ls").split()),
    ])
    e2
    return (e2,)


# ═════════════════════════ 3 · cd ═════════════════════════
@app.cell(hide_code=True)
def _(e2, mo):
    e2
    mo.md(
        r"""
        ---
        ## 3 · Entrar en la carpeta `Tema1`
        > *Navega hasta dentro de la carpeta descargada como Tema1.*

        **Pista:** `cd` = *change directory*. Fíjate en que **el prompt cambia** (`~` → `~/Tema1`).
        Atajos: `.` = aquí · `..` = carpeta superior · `~` = tu carpeta personal.
        """
    )
    return


@app.cell
def _(check, e2, mo, term):
    e2
    _s = term.sh("cd Tema1\npwd\nls")
    e3 = mo.vstack([
        _s,
        check("ahora estamos dentro de `Tema1`", term.out("pwd").endswith("/Tema1")),
    ])
    e3
    return (e3,)


# ═════════════════════════ 4 · mkdir ═════════════════════════
@app.cell(hide_code=True)
def _(e3, mo):
    e3
    mo.md(
        r"""
        ---
        ## 4 · Crear la carpeta `Datos`
        > *Crea una nueva carpeta denominada "Datos".*

        **Pista:** `mkdir` = *make directory*. Si dudas: `mkdir --help`. Linux distingue
        mayúsculas: `Datos` ≠ `datos`.
        """
    )
    return


@app.cell
def _(check, e3, mo, term):
    e3
    e4 = mo.vstack([
        term.sh("mkdir Datos\nls"),
        check("existe la carpeta `Datos`", term.out("test -d Datos && echo si") == "si"),
    ])
    e4
    return (e4,)


# ═════════════════════════ 5 · cp ═════════════════════════
@app.cell(hide_code=True)
def _(e4, mo):
    e4
    mo.md(
        r"""
        ---
        ## 5 · Copiar `Secuencias.txt` dentro de `Datos`
        > *Haz una copia del archivo Secuencias.txt dentro de la nueva carpeta "Datos".*

        **Pista:** `cp ORIGEN DESTINO`. Si el destino es una carpeta, el archivo conserva su
        nombre. Una **copia es un archivo nuevo e independiente**. Lo comprobamos con
        `md5sum`: mismo contenido ⇒ mismo código.
        """
    )
    return


@app.cell
def _(check, e4, mo, term):
    e4
    _s = term.sh("cp Secuencias.txt Datos/\nls Datos\nmd5sum Secuencias.txt Datos/Secuencias.txt")
    _a = term.out("md5sum < Secuencias.txt")
    _b = term.out("md5sum < Datos/Secuencias.txt")
    e5 = mo.vstack([
        _s,
        check("la copia existe y es idéntica (mismo md5)", bool(_a) and _a == _b),
    ])
    e5
    return (e5,)


# ═════════════════════════ 6 · mv ═════════════════════════
@app.cell(hide_code=True)
def _(e5, mo):
    e5
    mo.md(
        r"""
        ---
        ## 6 · Renombrar la copia a `aminoacidos.tt`
        > *Cambia el nombre del archivo Secuencias.txt y denomínalo "aminoacidos.tt".*

        **Pista:** `mv ORIGEN DESTINO` sirve para **mover y para renombrar**. Entramos en `Datos`
        para renombrar **la copia** (no el original). Cambiar el nombre **no cambia el
        contenido** — el md5 es el mismo.
        """
    )
    return


@app.cell
def _(check, e5, mo, term):
    e5
    _s = term.sh("cd Datos\nmv Secuencias.txt aminoacidos.tt\nls\nmd5sum aminoacidos.tt ../Secuencias.txt")
    _a = term.out("md5sum < aminoacidos.tt")
    _b = term.out("md5sum < ../Secuencias.txt")
    e6 = mo.vstack([
        _s,
        check("`aminoacidos.tt` existe, `Secuencias.txt` ya no está en `Datos`",
              term.out("ls") == "aminoacidos.tt"),
        check("el contenido no ha cambiado (md5 idéntico al original)", _a == _b),
    ])
    e6
    return (e6,)


# ═════════════════════════ 7 · cat / less ═════════════════════════
@app.cell(hide_code=True)
def _(e6, mo):
    e6
    mo.md(
        r"""
        ---
        ## 7 · Leer `aminoacidos.tt`
        > *Lee el contenido del archivo "aminoacidos.tt".*

        **Pista:** tres lectores de texto:

        | Comando | Comportamiento |
        |---|---|
        | `cat` | vuelca **todo** de golpe (no interactivo) |
        | `more` | por pantallas, solo hacia abajo |
        | `less` | por pantallas, **arriba y abajo** (`q` para salir) |

        Aquí usamos `cat`, pero el cuaderno **recorta** la salida a 12 líneas. Con `wc -l`
        contamos líneas: 4 líneas = 1 lectura FASTQ.
        """
    )
    return


@app.cell
def _(check, e6, mo, term):
    e6
    e7 = mo.vstack([
        term.sh("cat aminoacidos.tt", max_lines=12),
        term.sh("wc -l aminoacidos.tt"),
        check("el archivo tiene contenido",
              int(term.out("wc -l < aminoacidos.tt") or 0) > 0),
    ])
    e7
    return (e7,)


# ═════════════════════════ 8 · ln -s ═════════════════════════
@app.cell(hide_code=True)
def _(e7, mo):
    e7
    mo.md(
        r"""
        ---
        ## 8 · Enlace simbólico a `Secuencias.txt`
        > *Crea un enlace simbólico al archivo Secuencias.txt dentro de la nueva carpeta creada.*

        **Pista:** `ln -s DESTINO NOMBRE_DEL_ENLACE`. Sin `-s` crea un *enlace duro*.

        ⚠️ **Error clásico:** la ruta del destino se interpreta **desde la carpeta donde vive el
        enlace**. Estamos en `Datos`, y `Secuencias.txt` está **un nivel por encima** → hay que
        usar `../Secuencias.txt`. Primero lo hacemos mal a propósito (como en la clase) y luego
        lo corregimos.
        """
    )
    return


@app.cell
def _(check, e7, mo, term):
    e7
    _mal = term.sh("ln -s Secuencias.txt Secuencias.txt\nls -l\ncat Secuencias.txt")
    _roto = term.out("test -L Secuencias.txt && ! test -e Secuencias.txt && echo roto") == "roto"
    _bien = term.sh("rm Secuencias.txt\nln -s ../Secuencias.txt Secuencias.txt\nls -l")
    e8 = mo.vstack([
        mo.md("**① Intento incorrecto** — el enlace apunta a `Datos/Secuencias.txt`, que no existe:"),
        _mal,
        check("el primer enlace estaba roto (apuntaba a sí mismo)", _roto),
        mo.md("**② Correcto** — `../` sube un nivel:"),
        _bien,
        check("el enlace apunta a `../Secuencias.txt` y funciona",
              term.out("readlink Secuencias.txt") == "../Secuencias.txt"
              and term.out("test -e Secuencias.txt && echo ok") == "ok"),
    ])
    e8
    return (e8,)


# ═════════════════════════ 9 · leer el enlace ═════════════════════════
@app.cell(hide_code=True)
def _(e8, mo):
    e8
    mo.md(
        r"""
        ---
        ## 9 · Leer el enlace simbólico
        > *Lee el contenido del nuevo enlace simbólico de Secuencias.txt.*

        **Pista:** un enlace simbólico se lee **igual que un archivo normal**; el sistema sigue
        el "atajo" hasta el archivo real.
        """
    )
    return


@app.cell
def _(check, e8, mo, term):
    e8
    _a = term.out("md5sum < Secuencias.txt")
    _b = term.out("md5sum < ../Secuencias.txt")
    e9 = mo.vstack([
        term.sh("cat Secuencias.txt", max_lines=8),
        check("leer el enlace equivale a leer el original", _a == _b),
    ])
    e9
    return (e9,)


# ═════════════════════════ 10 · nano (emulado) ═════════════════════════
@app.cell(hide_code=True)
def _(e9, mo):
    e9
    mo.md(
        r"""
        ---
        ## 10 · Añadir una línea al original y volver a leerlo
        > *Añade una nueva línea al archivo de texto utilizando el editor nano y vuelve a leer el
        > contenido del archivo original Secuencias.txt que se encuentra fuera de la carpeta.*

        **En una terminal real:**

        ```bash
        cd ..                    # salimos de Datos
        nano Secuencias.txt      # escribe la línea al final
        #   Ctrl+O  → guardar (Enter para confirmar el nombre)
        #   Ctrl+X  → salir de nano
        tail -n 3 Secuencias.txt
nano es interactivo y no puede ejecutarse dentro de una celda, así que aquí lo
emulamos con echo "…" >> archivo, que añade (append) una línea al final.
⚠️ >> añade; un solo > sobrescribe el archivo entero.

Lo importante de este ejercicio — compara los tres archivos tras editar el original:

Archivo	¿Qué es?	¿Ve la línea nueva?
Tema1/Secuencias.txt	el original	✔ (lo hemos editado)
Datos/aminoacidos.tt	una copia (vida propia)	✘
Datos/Secuencias.txt	un enlace simbólico (atajo)	✔
"""		
)		
return		
@app.cell
def _(check, e9, mo, term):
e9
_s1 = term.sh("cd ..\npwd")
_s2 = term.sh('echo "Estoy añadiendo una nueva línea" >> Secuencias.txt')
_s3 = term.sh(
"tail -n 2 Secuencias.txt\n"
"tail -n 2 Datos/aminoacidos.tt\n"
"tail -n 2 Datos/Secuencias.txt"
)
_nueva = "Estoy añadiendo una nueva línea"
e10 = mo.vstack([
_s1, _s2, _s3,
check("el original contiene la línea nueva",
_nueva in term.out("tail -n 1 Secuencias.txt")),
check("la copia aminoacidos.tt NO la contiene (es independiente)",
_nueva not in term.out("tail -n 1 Datos/aminoacidos.tt")),
check("el enlace Datos/Secuencias.txt SÍ la contiene (apunta al original)",
_nueva in term.out("tail -n 1 Datos/Secuencias.txt")),
])
e10
return (e10,)

═════════════════════════ 11 · rm ═════════════════════════
@app.cell(hide_code=True)
def _(e10, mo):
e10
mo.md(
r"""

11 · Eliminar aminoacidos.tt
Elimina el archivo aminoacidos.tt.

Pista: rm = remove. ⚠️ En Linux no hay papelera. Para borrar carpetas haría
falta rm -r; con -i te pide confirmación.
"""
)
return

@app.cell
def _(check, e10, mo, term):
e10
e11 = mo.vstack([
term.sh("rm Datos/aminoacidos.tt\nls -l Datos"),
check("aminoacidos.tt ya no existe",
term.out("test -e Datos/aminoacidos.tt && echo si") != "si"),
check("el original y el enlace siguen intactos",
term.out("test -e Secuencias.txt && test -L Datos/Secuencias.txt && echo ok") == "ok"),
])
e11
return (e11,)

═════════════════════════ Hoja de respuestas ═════════════════════════
@app.cell(hide_code=True)
def _(e11, mo):
e11
mo.md(
r"""

📋 Hoja de respuestas (para pegar en el documento y entregar en PDF)
bash
# 1. Ruta actual
pwd

# 2. Listar archivos y carpetas
ls

# 3. Entrar en Tema1
cd Tema1

# 4. Crear la carpeta Datos
mkdir Datos

# 5. Copiar Secuencias.txt dentro de Datos
cp Secuencias.txt Datos/

# 6. Renombrar la copia
cd Datos
mv Secuencias.txt aminoacidos.tt

# 7. Leer aminoacidos.tt
cat aminoacidos.tt            # (o: less aminoacidos.tt)

# 8. Enlace simbólico al original (que está un nivel por encima)
ln -s ../Secuencias.txt Secuencias.txt

# 9. Leer el enlace simbólico
cat Secuencias.txt

# 10. Editar el original con nano y releerlo
cd ..
nano Secuencias.txt           # Ctrl+O, Enter, Ctrl+X
cat Secuencias.txt            # (o: tail Secuencias.txt)

# 11. Eliminar aminoacidos.tt
rm Datos/aminoacidos.tt
Preguntas de repaso
¿Por qué el enlace de la 8 falla si escribimos ln -s Secuencias.txt Secuencias.txt
desde Datos?

¿Por qué la copia no recibe la línea nueva y el enlace sí?

¿Qué pasaría con el enlace si borráramos el original? (pruébalo en la terminal libre)
"""
)
return

# ═════════════════════════ Terminal interactivo (REPL real) ═════════════════════════
@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
        ---
        ## 🧪 Terminal interactivo (REPL)

        Escribe un comando y pulsa **Enter** (o ▶). El prompt refleja tu `cd` actual.
        Comandos disponibles: `pwd`, `ls`, `cd`, `mkdir`, `cp`, `mv`, `cat`, `rm`,
        `ln -s`, `wc`, `md5sum`, `head`, `tail`, `readlink`, `test`, `echo`, `clear`.

        También puedes usar `&&`, `<`, `>` y `>>`.
        """)
    return


# ─── Estado (se recrea al reiniciar, porque depende de HOME) ───
@app.cell(hide_code=True)
def _(HOME, mo):
    get_cwd, set_cwd = mo.state(str(HOME))
    get_hist, set_hist = mo.state([])
    return get_cwd, get_hist, set_cwd, set_hist


# ─── Entrada: el comando se ejecuta en un callback ───
@app.cell(hide_code=True)
def _(HOME, Terminal, get_cwd, get_hist, mo, set_cwd, set_hist):
    def _run(value):
        cmd = (value or "").strip()
        if not cmd:
            return
        if cmd == "clear":
            set_hist([])
            return
        t = Terminal(HOME)
        t.cwd = get_cwd()
        prompt = t.prompt          # prompt ANTES de ejecutar
        out, err = t.run(cmd)
        set_hist(get_hist() + [(prompt, cmd, out, err)])
        set_cwd(t.cwd)

    cmd_form = mo.ui.form(
        mo.ui.text(placeholder="escribe un comando y pulsa Enter…", full_width=True),
        clear_on_submit=True,
        submit_button_label="▶ Ejecutar",
        on_change=_run,
    )
    cmd_form
    return (cmd_form,)


# ─── Historial + prompt actual ───
@app.cell(hide_code=True)
def _(HOME, Terminal, cmd_form, get_cwd, get_hist, mo):
    _t = Terminal(HOME)
    _t.cwd = get_cwd()

    _lines = []
    for _prompt, _cmd, _out, _err in get_hist():
        _lines.append(f"{_prompt} {_cmd}")
        if _out:
            _lines.extend(_out.rstrip("\n").split("\n"))
        if _err:
            _lines.extend(f"[stderr] {_l}" for _l in _err.rstrip("\n").split("\n"))

    _lines.append(f"{_t.prompt} █")
    if not get_hist():
        _lines += ["", "Comandos: pwd · ls · cd · mkdir · cp · mv · cat · rm · ln -s · wc · md5sum · tail · echo · clear"]

    mo.md("```console\n" + "\n".join(_lines) + "\n```")
    return
if name == "main":
app.run()
