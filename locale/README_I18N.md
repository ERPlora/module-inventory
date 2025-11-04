# Internacionalización (i18n) en Plugins CPOS

Este documento explica cómo implementar traducciones multiidioma en plugins CPOS.

## Estructura de Archivos

Cada plugin debe tener su propia carpeta `locale/` con la siguiente estructura:

```
plugins/
└── tu-plugin/
    └── locale/
        ├── en/
        │   └── LC_MESSAGES/
        │       ├── django.po    # Traducciones en inglés
        │       └── django.mo    # Archivo compilado
        └── es/
            └── LC_MESSAGES/
                ├── django.po    # Traducciones en español
                └── django.mo    # Archivo compilado
```

## Idiomas Soportados

El sistema CPOS soporta los siguientes idiomas:
- **Inglés (en)**: Idioma predeterminado
- **Español (es)**: Idioma secundario

## Cómo Marcar Strings para Traducción

### En Python (models.py, views.py, etc.)

```python
from django.utils.translation import gettext_lazy as _

class Product(models.Model):
    name = models.CharField(
        max_length=200,
        verbose_name=_("Name")  # ← Marcado para traducción
    )

    class Meta:
        verbose_name = _("Product")
        verbose_name_plural = _("Products")
```

**Importante**: Usa `gettext_lazy` (alias `_`) para strings en nivel de módulo/clase.

### En Templates

```html
{% load i18n %}

<h1>{% trans "Products" %}</h1>

<ion-button>
    {% trans "Create" %}
</ion-button>

<!-- Con variables -->
<span>{% blocktrans count counter=products|length %}
    {{ counter }} product
{% plural %}
    {{ counter }} products
{% endblocktrans %}</span>
```

### En JavaScript

Para JavaScript, usa un archivo separado `djangojs.po`:

```javascript
// Primero carga el catálogo de traducciones
<script src="{% url 'javascript-catalog' %}"></script>

<script>
// Usa gettext() para traducir
const message = gettext('Product created successfully');
const plural = ngettext('product', 'products', count);
</script>
```

## Flujo de Trabajo de Traducción

### 1. Crear Archivos de Traducción

Desde la raíz del proyecto workbench:

```bash
# Generar archivos .po para español
python manage.py makemessages -l es

# Generar archivos .po para inglés
python manage.py makemessages -l en

# Para JavaScript
python manage.py makemessages -d djangojs -l es
python manage.py makemessages -d djangojs -l en
```

### 2. Editar Traducciones

Abre los archivos `.po` en `locale/*/LC_MESSAGES/django.po` y traduce:

```po
# En locale/es/LC_MESSAGES/django.po
msgid "Product"
msgstr "Producto"

msgid "Products"
msgstr "Productos"
```

### 3. Compilar Traducciones

Después de editar los archivos `.po`, compílalos a formato binario `.mo`:

```bash
python manage.py compilemessages
```

### 4. Actualizar Traducciones Existentes

Si añades nuevas strings traducibles:

```bash
# Actualiza los archivos .po existentes sin perder traducciones
python manage.py makemessages -l es --no-obsolete
python manage.py makemessages -l en --no-obsolete

# Compila los archivos actualizados
python manage.py compilemessages
```

## Cambiar el Idioma

### En el Navegador

Django detecta automáticamente el idioma preferido del navegador mediante el header `Accept-Language`.

### Programáticamente

```python
from django.utils.translation import activate

# Cambiar al español
activate('es')

# Cambiar al inglés
activate('en')
```

### Mediante URL

Puedes cambiar el idioma usando el prefijo en la URL (si está configurado):

```
/en/products/  # Inglés
/es/products/  # Español
```

## Buenas Prácticas

### 1. Usa Contextos para Palabras Ambiguas

```python
from django.utils.translation import pgettext_lazy

# "Open" puede significar "abierto" o "abrir"
pgettext_lazy("state", "Open")  # → "Abierto"
pgettext_lazy("action", "Open")  # → "Abrir"
```

### 2. Mantén las Traducciones Simples

```python
# ❌ MAL - Difícil de traducir
_("You have {count} products in stock")

# ✅ BIEN - Usa variables
_("You have %(count)d products in stock") % {'count': num}
```

### 3. Usa Plurales Correctamente

```python
from django.utils.translation import ngettext

count = 5
message = ngettext(
    'One product',
    '%(count)d products',
    count
) % {'count': count}
```

### 4. Documenta el Contexto

```po
# Título de la página principal
msgid "Dashboard"
msgstr "Panel de Control"

# Botón para crear nuevo producto
msgid "Create"
msgstr "Crear"
```

## Estructura del Archivo .po

```po
# Cabecera (metadata)
msgid ""
msgstr ""
"Project-Id-Version: 1.0\n"
"Language: es\n"
"Content-Type: text/plain; charset=UTF-8\n"

# Traducción simple
msgid "Product"
msgstr "Producto"

# Traducción con plural
msgid "Product"
msgid_plural "Products"
msgstr[0] "Producto"
msgstr[1] "Productos"

# Traducción con contexto
msgctxt "action"
msgid "Open"
msgstr "Abrir"
```

## Testing de Traducciones

### 1. Verificar Traducciones Faltantes

```bash
# Busca strings sin traducir (msgstr vacío)
grep -A 1 "msgid" locale/es/LC_MESSAGES/django.po | grep -B 1 '^msgstr ""$'
```

### 2. Probar en Diferentes Idiomas

```python
# En Django shell
from django.utils import translation

# Probar en español
translation.activate('es')
from django.utils.translation import gettext
print(gettext('Product'))  # → "Producto"

# Probar en inglés
translation.activate('en')
print(gettext('Product'))  # → "Product"
```

## Herramientas Recomendadas

- **Poedit**: Editor visual para archivos .po (https://poedit.net/)
- **Lokalize**: Editor KDE para traducciones
- **VS Code**: Con extensión "gettext" para syntax highlighting

## Troubleshooting

### Las traducciones no aparecen

1. Verifica que compilaste los archivos: `python manage.py compilemessages`
2. Reinicia el servidor Django
3. Limpia la caché del navegador
4. Verifica que `USE_I18N = True` en settings.py

### Los archivos .mo no se generan

1. Instala gettext: `brew install gettext` (macOS) o `apt-get install gettext` (Linux)
2. Verifica que los archivos .po tienen formato correcto
3. Revisa errores en la salida de `compilemessages`

### Las traducciones están en inglés aunque seleccioné español

1. Verifica el idioma en el navegador
2. Verifica que el middleware de idiomas está activo
3. Usa Django Debug Toolbar para ver el idioma activo

## Recursos Adicionales

- [Django i18n Documentation](https://docs.djangoproject.com/en/5.0/topics/i18n/)
- [gettext Format Specification](https://www.gnu.org/software/gettext/manual/gettext.html)
- [Babel (Python i18n library)](http://babel.pocoo.org/)

## Ejemplo Completo

Ver los archivos en este directorio como ejemplo de implementación completa:
- `locale/es/LC_MESSAGES/django.po` - Traducciones al español
- `locale/en/LC_MESSAGES/django.po` - Traducciones al inglés (base)
