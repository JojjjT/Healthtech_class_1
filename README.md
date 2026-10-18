# HealthTech · Clase 1

Repositorio de la **Clase 1** del curso de HealthTech. Contiene la presentación
del tema y un laboratorio interactivo de la terminal de Linux, ambos publicados
en **GitHub Pages**.

🔗 **Sitio publicado:** <https://JojjjT.github.io/Healthtech_class_1/>

---

## 📂 Contenido del repositorio

| Archivo | Descripción |
|---|---|
| `tema1_clase.html` | Presentación del Tema 1 (clase magistral) |
| `tema1_terminal.py` | Cuaderno **marimo** del laboratorio de terminal de Linux |
| `.github/workflows/deploy-presentacion.yml` | Workflow de despliegue automático a GitHub Pages |

---

## 🌐 URLs publicadas

| URL | Qué abre |
|---|---|
| <https://JojjjT.github.io/Healthtech_class_1/> | Página índice con enlaces |
| <https://JojjjT.github.io/Healthtech_class_1/tema1_clase.html> | Presentación del tema |
| <https://JojjjT.github.io/Healthtech_class_1/tema1_terminal.html> | Laboratorio interactivo (marimo WASM) |

> El laboratorio se ejecuta **íntegramente en el navegador** (Pyodide/WASM):
> no requiere instalar nada. La primera carga tarda unos segundos mientras
> se descargan las dependencias.

---

## 🎯 Contenido del laboratorio

El cuaderno `tema1_terminal.py` resuelve, paso a paso, los **11 ejercicios del Tema 1.1**
sobre la terminal de Linux:

1. `pwd` — ruta actual
2. `ls` — listar archivos y carpetas
3. `cd` — entrar en `Tema1`
4. `mkdir` — crear la carpeta `Datos`
5. `cp` — copiar `Secuencias.txt` dentro de `Datos`
6. `mv` — renombrar la copia a `aminoacidos.tt`
7. `cat` / `less` — leer el archivo
8. `ln -s` — crear un enlace simbólico al original
9. Leer el enlace simbólico
10. Editar el original con `nano` (emulado) y comparar original ↔ copia ↔ enlace
11. `rm` — eliminar `aminoacidos.tt`

Cada ejercicio incluye:

- El enunciado y una **pista teórica**.
- El comando que lo resuelve (ejecutado en una **terminal emulada en Python**).
- Una **comprobación automática** ✔ que verifica el resultado.

Además, el cuaderno permite **subir tus propios archivos** (`Secuencias.txt`
o un `.zip` con la carpeta `Tema1/`) para trabajar con datos reales.

---

## 🛠 Uso local (opcional)

### Ver la presentación

Solo abre `tema1_clase.html` en el navegador.

### Ejecutar el laboratorio marimo

Requisitos: **Python ≥ 3.10**.

```bash
# Instalar marimo
pip install marimo

# Abrir el cuaderno en modo edición
marimo edit tema1_terminal.py

# O en modo "solo ejecución" (para el alumno)
marimo run tema1_terminal.py
