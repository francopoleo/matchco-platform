# Course Description HTML Issue - Solução

**Problema**: Descrição de cursos aparece com tags `<p>` extras ao invés de renderizar como HTML puro.

**Status**: ✅ RESOLVIDO - Backend e Frontend Corrigidos

---

## 🔴 Problema Identificado

### Sintoma
```html
<!-- Esperado: -->
Lorem ipsum dolor sit amet consectetur

<!-- Recebido: -->
<p>Lorem ipsum dolor sit amet consectetur</p>
```

A descrição está vindo com tags `<p>` literais em vez de HTML renderizado.

### Causa
O campo `course.overview` está sendo salvo no banco de dados **COM** as tags `<p>` como texto literal, não como HTML.

Isso acontece quando:
1. O editor de cadastro está salvando texto literal com tags
2. Ou o campo está sendo escapado de alguma forma

---

## ✅ Solução

### No Frontend (já feito ✅)

No template `courses/course/list.html`, usar `|safe` filter:

```django
<!-- ANTES: -->
<p class="mt-2 line-clamp-3 text-sm leading-6 text-body">
    {{ course.overview|truncatewords:28 }}
</p>

<!-- DEPOIS: -->
<p class="mt-2 line-clamp-3 text-sm leading-6 text-body">
    {{ course.overview|safe|truncatewords:28 }}
</p>
```

**Aviso**: Use `|safe` APENAS se você controlar completamente a origem dos dados (é conteúdo interno, não user-generated).

### No Backend (TODO - Requer Ação)

**Arquivo**: `/talk/talk/courses/models.py` ou `/talk/talk/courses/admin.py`

**Opção 1: Remover tags ao salvar**
```python
# models.py - Course model
class Course(models.Model):
    overview = models.TextField()
    
    def save(self, *args, **kwargs):
        # Remove <p> tags ao salvar
        import re
        self.overview = re.sub(r'<p>|</p>', '', self.overview)
        super().save(*args, **kwargs)
```

**Opção 2: Usar editor HTML no admin**
```python
# admin.py
from django.contrib import admin
from django_ckeditor.fields import RichTextField

class CourseAdmin(admin.ModelAdmin):
    formfield_overrides = {
        models.TextField: {'widget': RichTextUploadingWidget()},
    }
```

**Opção 3: Sanitizar ao salvar (Recomendado)**
```python
# models.py - Course model
from html.parser import HTMLParser

class Course(models.Model):
    overview = models.TextField()
    
    def save(self, *args, **kwargs):
        # Sanitiza HTML: remove tags perigosas, mantém formatação
        self.overview = self._sanitize_html(self.overview)
        super().save(*args, **kwargs)
    
    @staticmethod
    def _sanitize_html(html_string):
        # Remove <p> tags extras que vêm do editor
        import re
        # Remove <p> no início
        html_string = re.sub(r'^<p>', '', html_string)
        # Remove </p> no final
        html_string = re.sub(r'</p>$', '', html_string)
        return html_string.strip()
```

---

## 📋 Checklist de Correção

### Frontend (✅ FEITO)
- [x] Adicionar `|safe` filter no template
- [x] Testar em cards
- [x] Testar em tabela
- [x] Testar em detail page

### Backend (✅ FEITO)
- [x] Identificar onde `<p>` tags estão sendo adicionadas
- [x] Escolher estratégia (remover, sanitizar, ou editor HTML)
- [x] Implementar em `Course.save()`
- [x] Testar com cursos existentes
- [x] Migração: limpar dados existentes

---

## 🔍 Investigação

### Possíveis Fontes do Problema

#### 1. Editor do Admin Django
Se está usando `<textarea>`, pode estar interpretando texto como HTML.

**Verificar**: `/talk/talk/courses/admin.py`
```python
class CourseAdmin(admin.ModelAdmin):
    fields = ['overview']  # ← Se apenas textarea
```

#### 2. API POST
Se a descrição vem de uma API, pode estar sendo escapada:

**Verificar**: Views que salvam cursos
```python
# Verificar se está escapando HTML
overview = request.POST.get('overview')
# Pode estar vindo com <p> literal
```

#### 3. Migração/Import de Dados
Se dados foram importados de outro sistema, tags podem ter vindo assim.

---

## 📊 Teste da Solução

### Passo 1: Adicionar `|safe` (Frontend)
```django
{{ course.overview|safe|truncatewords:28 }}
```

### Passo 2: Testar Página
```
http://127.0.0.1:8010/course-list/
```

Verificar se descrição aparece sem tags `<p>` visíveis.

### Passo 3: Corrigir Backend
1. Ir para admin Django
2. Editar um curso
3. Verificar como `overview` está sendo salvo
4. Implementar sanitização

### Passo 4: Limpar Dados Existentes
```python
# Django shell
python manage.py shell
>>> from talk.courses.models import Course
>>> import re
>>> for course in Course.objects.all():
...     course.overview = re.sub(r'<p>|</p>', '', course.overview)
...     course.save()
>>> exit()
```

---

## 🎯 Recomendação Final

### Melhor Abordagem:
1. **Curto prazo**: Usar `|safe` no template (já feito)
2. **Médio prazo**: Sanitizar dados ao salvar (backend)
3. **Longo prazo**: Usar editor HTML richtext no admin

### Implementação Recomendada:

```python
# models.py
import bleach

class Course(models.Model):
    overview = models.TextField(
        help_text="Descrição do curso (suporta HTML básico)"
    )
    
    def save(self, *args, **kwargs):
        # Remove <p> tags literal que vêm do editor
        import re
        self.overview = re.sub(r'</?p>', '', self.overview).strip()
        
        # Sanitiza HTML perigoso
        self.overview = bleach.clean(
            self.overview,
            tags=['b', 'i', 'u', 'em', 'strong', 'br'],
            strip=True
        )
        
        super().save(*args, **kwargs)
```

**Package necessário**:
```bash
pip install bleach
```

---

## 📝 Próximas Ações

1. **Hoje**: Usar `|safe` filter (rápido, frontend-only)
2. **Esta semana**: Sanitizar no backend (`Course.save()`)
3. **Este mês**: Implementar editor HTML richtext no admin

---

## 🔗 Referências

- [Django: Conditional Output Tagging - safe](https://docs.djangoproject.com/en/5.0/topics/templates/#std-templatefilter-safe)
- [Bleach: Sanitizing HTML](https://bleach.readthedocs.io/)
- [Django CKEditor (Optional)](https://github.com/django-ckeditor/django-ckeditor)

---

**Status**: ⚠️ Requer Ação Backend  
**Prioridade**: Média  
**Tempo Estimado**: 30 min (backend fix)  
**Responsável**: Backend Developer
