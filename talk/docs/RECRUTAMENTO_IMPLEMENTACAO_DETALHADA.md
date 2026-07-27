# Talk Recrutamento: Plano de Implementação Detalhado

**Data:** 2026-07-27  
**Status:** Planejamento de Desenvolvimento  
**Escopo:** Landing pages por segmento + geração QR + fluxo completo candidato → hire  
**Público-alvo:** 2 nichos (Hospital + Varejo/Shopping)

---

## 📋 Índice

1. Arquitetura de Landing Pages por Segmento
2. Consolidação de Públicos (Public vs Internal)
3. Limpeza de Dados (Apagar segmentos extras)
4. Fluxo Detalhado: QR Code → Contratação
5. Roadmap de Implementação (8 semanas)
6. Testes E2E

---

## 🏗️ Parte 1: Arquitetura de Landing Pages por Segmento

### Modelo de Segmentos

```
Segmento = Nicho de Mercado + Modelo de Recrutamento Específico

HOSPITAL (Saúde)
├─ Empresas: Hospital Central, Centro Médico, Laboratório, Clínica
├─ Cargos: Médico, Enfermeiro, Técnico, Administrativo
├─ Competências: Resolução de problemas, confiabilidade, comunicação, liderança
├─ Turnover: 25-30%/ano (estável)
├─ Recrutamento: Interno (funcionários) + Externo (público)
└─ Landing Page: /recrutamento/hospital/

VAREJO / SHOPPING (Comércio)
├─ Empresas: Retail 800 (800 lojas), Rede de Shoppings, Franquias
├─ Cargos: Vendedor, Gerente, Promotor, Operacional
├─ Competências: Orientação a cliente, sales, comunicação, teamwork
├─ Turnover: 80-100%/ano (alto)
├─ Recrutamento: QR Code em loja + Interno
└─ Landing Page: /recrutamento/varejo/
```

---

### Landing Page por Segmento (Arquitetura)

```django
# accounts/views.py

class SegmentedLandingView(TemplateView):
    """
    Redireciona para landing page correta baseado no segmento
    """
    def get(self, request, *args, **kwargs):
        segment = self.kwargs.get('segment', 'default')
        
        # Valida segmento
        valid_segments = ['hospital', 'varejo', 'default']
        if segment not in valid_segments:
            segment = 'default'
        
        context = {
            'segment': segment,
            'segment_name': self.get_segment_name(segment),
            'segment_data': self.get_segment_data(segment),
        }
        
        template = f'registration/recruitment_{segment}.html'
        return render(request, template, context)
    
    def get_segment_name(self, segment):
        mapping = {
            'hospital': 'Saúde',
            'varejo': 'Varejo & Shopping',
            'default': 'Recrutamento Talk',
        }
        return mapping.get(segment, 'Recrutamento Talk')
    
    def get_segment_data(self, segment):
        """
        Retorna dados específicos do segmento:
        - Competências prioritárias
        - Descrição de cargos
        - Benefícios
        - Exemplos de empresas
        """
        data = {
            'hospital': {
                'hero_title': 'Profissionais de Saúde Encontram Oportunidades',
                'hero_subtitle': 'Hospitais, clínicas e laboratórios descobrem os melhores profissionais',
                'hero_image': 'hospital_hero.svg',
                'competencies': ['resolução de problemas', 'confiabilidade', 'comunicação', 'liderança'],
                'example_roles': ['Médico', 'Enfermeiro', 'Técnico', 'Administrativo'],
                'turnover_stat': '25-30%/ano',
                'example_companies': ['Hospital Central', 'Clínica Nova', 'Laboratório Vida'],
                'main_pain': 'Rotatividade de profissionais afeta continuidade de cuidado',
            },
            'varejo': {
                'hero_title': 'O Emprego Encontra Você',
                'hero_subtitle': 'Escaneia QR code da loja. Fica disponível. Empresas contatam.',
                'hero_image': 'varejo_hero.svg',
                'competencies': ['orientação a cliente', 'sales', 'comunicação', 'teamwork'],
                'example_roles': ['Vendedor', 'Gerente', 'Promotor', 'Operacional'],
                'turnover_stat': '80-100%/ano',
                'example_companies': ['Retail 800', 'Shopping Center', 'Loja de Moda'],
                'main_pain': 'Alto turnover faz recrutamento ser contínuo e caro',
            }
        }
        return data.get(segment, {})

# URLs
urlpatterns = [
    path('recrutamento/', SegmentedLandingView.as_view(), name='recruitment_landing'),
    path('recrutamento/<str:segment>/', SegmentedLandingView.as_view(), name='recruitment_segment'),
]
```

---

### Páginas Iniciais por Segmento

```
GET / → Detecta segmento do usuário → Redireciona
    
Se não-autenticado:
  ├─ Vindo de /recrutamento/hospital/ → landing_hospital.html
  ├─ Vindo de /recrutamento/varejo/ → landing_varejo.html
  └─ Vindo de link direto → landing_default.html (Talk geral)

Se autenticado (user.organization.segment = 'hospital'):
  └─ → /console/ (manager dashboard)
     → Cursos/educação hospitalar
     → Métricas recrutamento hospitalar

Se autenticado (user.organization.segment = 'varejo'):
  └─ → /console/ (manager dashboard)
     → Cursos/educação varejo
     → Métricas recrutamento varejo
```

---

## 🔐 Parte 2: Consolidação de Públicos (Public vs Internal)

### Modelo de Públicos

```python
class PublicType(models.TextChoices):
    PUBLIC = 'public', 'Candidato Externo (QR Code)'
    INTERNAL = 'internal', 'Funcionário Interno'

class User(models.Model):
    # ... campos existentes
    
    # NOVO: Tipo de público
    public_type = CharField(
        max_length=20,
        choices=PublicType.choices,
        default='internal'
    )
    # PUBLIC: Usuário externo, se cadastrou via QR code
    # INTERNAL: Funcionário da empresa, se cadastrou via convite/app interno

class Organization(models.Model):
    # ... campos existentes
    
    # NOVO: Segmento de mercado
    segment = CharField(
        max_length=20,
        choices=[('hospital', 'Saúde'), ('varejo', 'Varejo'), ('other', 'Outro')],
        default='other'
    )
```

---

### Fluxo de Cadastro: Public vs Internal

#### Flow 1: PÚBLICO (QR Code → Varejo)

```
1. Candidato escaneia QR code na loja
   └─ QR leva a: /recrutamento/varejo/cadastro/public/
   
2. Landing page específica para público:
   └─ Título: "Oportunidades em Shoppings próximos"
   └─ Formulário simples: nome, CEP, disponibilidade
   
3. Sistema cria User com:
   └─ public_type = 'public'
   └─ organization = Retail800 (ou rede específica)
   └─ Membro de: public-candidates (org virtual pública)
   
4. Redirecionamento:
   └─ "Entrevista disponível em 24h. Volte para fazer!"
   └─ Email: "Seu candidatura foi registrada. Faça a entrevista quando quiser."

5. Próxima visita:
   └─ User faz login → Entra no quiz de entrevista
   └─ Score criado
   └─ MatchingProfile criado
   └─ Empresas passam a ver o candidato
```

#### Flow 2: INTERNO (Funcionário da Empresa)

```
1. HR da empresa (gerente) envia link para funcionários:
   └─ /recrutamento/varejo/cadastro/internal/?company_id=123
   
2. Landing page específica para interno:
   └─ Título: "Avance sua carreira conosco"
   └─ Formulário: experiência, aspirações, disponibilidade para mudança
   
3. Sistema cria/liga User com:
   └─ public_type = 'internal'
   └─ organization = Empresa específica (Hospital A, Retail 800, etc)
   └─ membership já existe (funcionário existente)
   
4. Objetivo: Preparar funcionário para mobilidade interna
   └─ Quiz avalia: pode crescer? Qual cargo? Qual loja?
   └─ Resultado: "Você é candidato para gerente na Loja Sul"
   └─ Empresa oferece promoção/mudança interna
```

---

### Identificação de Public vs Internal

```python
# recruitment/views.py

class RecruitmentSignupView(TemplateView):
    template_name = 'recruitment/signup.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Detecta tipo de público
        public_type = self.kwargs.get('public_type', 'public')
        # public_type em URL: /cadastro/public/ ou /cadastro/internal/
        
        context['public_type'] = public_type
        context['form'] = self.get_form_for_public_type(public_type)
        context['template_name'] = f'recruitment/signup_{public_type}.html'
        
        return context
    
    def get_form_for_public_type(self, public_type):
        """Retorna formulário específico para tipo de público"""
        if public_type == 'public':
            return PublicCandidateSignupForm()
            # Campos: nome, CEP, disponibilidade, contato
        else:  # internal
            return InternalCandidateSignupForm()
            # Campos: experiência, aspirações, carreira, mudança interna

class PublicCandidateSignupForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ['first_name', 'last_name', 'email']
    
    cep = forms.CharField(max_length=8, label='CEP')
    availability = forms.ChoiceField(
        choices=[('available', 'Disponível agora'),
                 ('2weeks', 'Em 2 semanas'),
                 ('1month', 'Em 1 mês')]
    )
    
    def save(self, commit=True):
        user = super().save(commit=False)
        user.public_type = 'public'
        # Cria em org pública: public-candidates
        if commit:
            user.save()
        return user

class InternalCandidateSignupForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ['first_name', 'last_name']
    
    current_role = forms.CharField(label='Seu cargo atual')
    years_experience = forms.IntegerField(label='Anos de experiência')
    desired_role = forms.ChoiceField(
        choices=[('supervisor', 'Supervisor'),
                 ('manager', 'Gerente'),
                 ('other', 'Outro cargo')]
    )
    open_to_relocate = forms.BooleanField(label='Aberto a transferência para outra loja?')
```

---

## 🗑️ Parte 3: Limpeza de Dados (Apagar Segmentos Extras)

### Segmentos a Manter vs Apagar

```
✅ MANTER (Definir como "production"):
  ├─ Hospital Generative (segmento: hospital)
  ├─ Retail 800 (segmento: varejo)
  └─ Escola Generative (segmento: education - OPCIONAL para fase 2)

❌ APAGAR (Limpar dados confusos):
  ├─ Seguradora Generative
  ├─ Manufatura XYZ
  ├─ FinTech Rápido
  └─ Farmalab Biotech

Razão: Foco em 2 nichos bem definidos (Hospital + Varejo)
       Evita confusão de dados, UI complexa, múltiplos fluxos
```

### Script de Limpeza

```python
# configuration/management/commands/cleanup_segments.py

from django.core.management.base import BaseCommand
from configuration.models import Organization

class Command(BaseCommand):
    help = 'Limpa organizações extras, mantém apenas Hospital e Varejo'
    
    def handle(self, *args, **options):
        # Organizações a manter
        keep_slugs = [
            'hospital-generative',
            'retail-800',
            'escola-generative',  # opcional
        ]
        
        # Deleta outras
        to_delete = Organization.objects.exclude(slug__in=keep_slugs)
        count = to_delete.count()
        
        self.stdout.write(f'Deletando {count} organizações...')
        to_delete.delete()
        
        self.stdout.write(self.style.SUCCESS('Limpeza concluída!'))
        self.stdout.write(f'Mantidas: {", ".join(keep_slugs)}')
```

---

## 🎯 Parte 4: Fluxo Detalhado - QR Code → Contratação

### Estágios do Fluxo

```
ESTÁGIO 1: DESCOBERTA (Semana 1)
├─ Candidato vê QR code em loja
├─ Escaneia QR → landing /recrutamento/varejo/cadastro/public/
└─ Cadastra em 2 minutos (nome, CEP, contato)
   └─ User criado com public_type='public'
   └─ Mensagem: "Entrevista disponível em 24h"

ESTÁGIO 2: AVALIAÇÃO (Semana 1-2)
├─ Candidato volta ao app
├─ Faz entrevista (20 min, 30-40 perguntas)
├─ Sistema calcula score em 8 dimensões
└─ MatchingProfile criado
   └─ Score armazenado (0-100)
   └─ Perfil visível para empresas

ESTÁGIO 3: MATCHING (Semana 2-4)
├─ Empresas (HR) buscam: "Vendedores nos próximos 5km, score 70+"
├─ Candidato aparece na lista de matches
├─ HR entra em contato via chat
└─ Negociação:
   ├─ HR: "Vaga de vendedor em nossa loja Sul"
   ├─ Salário: R$1.500
   ├─ Horário: Ter-Sab, 14h-22h
   ├─ Transporte: Linha 407 (5km, R$3,45, 20 min)
   └─ Candidato: Aceita/Recusa

ESTÁGIO 4: CONTRATAÇÃO (Semana 4+)
├─ Candidato aceita oferta
├─ HR faz pré-boarding (check documentos, dados banco)
├─ Candidato tira dúvidas (chat)
├─ Começa na data combinada
└─ HR reporta contratação no Talk
   └─ Sistema registra: OfferHistory, HiringDecision
   └─ Analytics atualizam

ESTÁGIO 5: FEEDBACK & APRENDIZADO (Contínuo)
├─ HR da empresa (after 3 meses):
│  └─ "Como foi com nosso novo vendedor?"
│  └─ Feedback: comportamento, performance, fit
├─ Sistema atualiza MatchingProfile do candidato
└─ Empresas veem histórico: "75% dos contratados Talk vão bem"
```

---

### Fluxo Técnico: QR Code Geração

```python
# recruitment/models.py

class QRCodeCampaign(models.Model):
    """Campanha de QR codes para recrutamento"""
    organization = ForeignKey(Organization)
    
    # Tipo de público
    public_type = CharField(
        max_length=20,
        choices=[('public', 'Público Externo'),
                 ('internal', 'Funcionários Internos')],
        default='public'
    )
    
    # Local (para varejo)
    store_name = CharField(max_length=255, null=True)  # "Loja Sul Shopping"
    store_location = PointField(null=True)  # Geoloc
    
    # URL gerada
    signup_url = URLField(unique=True)  # /recrutamento/varejo/cadastro/public/?campaign=xyz
    qr_code_image = ImageField()
    
    # Metadados
    created_at = DateTimeField(auto_now_add=True)
    active = BooleanField(default=True)
    
    # Analytics
    scans_count = PositiveIntegerField(default=0)
    signups_count = PositiveIntegerField(default=0)
    
    def generate_qr_code(self):
        """Gera imagem QR code para esta campanha"""
        import qrcode
        
        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_L,
            box_size=10,
            border=4,
        )
        qr.add_data(self.signup_url)
        qr.make(fit=True)
        
        img = qr.make_image(fill_color="black", back_color="white")
        
        # Salva arquivo
        filename = f'qr_{self.id}_{timezone.now().timestamp()}.png'
        self.qr_code_image.save(filename, img)
        self.save()
        
        return self.qr_code_image

# recruitment/views.py

class QRCodeGeneratorView(LoginRequiredMixin, View):
    """Gerente de loja gera QR code para recrutamento"""
    
    def post(self, request, *args, **kwargs):
        # Dados da loja
        store_name = request.POST.get('store_name')
        store_location = request.POST.get('store_location')  # latitude, longitude
        
        # Criar campanha
        campaign = QRCodeCampaign.objects.create(
            organization=request.user.organization,
            public_type='public',
            store_name=store_name,
            store_location=f'POINT({store_location})',
            signup_url=f'/recrutamento/{request.user.organization.segment}/cadastro/public/?campaign={uuid.uuid4()}'
        )
        
        # Gera QR
        campaign.generate_qr_code()
        
        # Retorna
        return JsonResponse({
            'campaign_id': campaign.id,
            'qr_url': campaign.qr_code_image.url,
            'signup_url': campaign.signup_url,
            'scans': campaign.scans_count,
        })

# recruitment/views.py

class QRCodeRedirectView(View):
    """Tracked QR code scan"""
    
    def get(self, request, campaign_id):
        try:
            campaign = QRCodeCampaign.objects.get(id=campaign_id)
            campaign.scans_count += 1
            campaign.save()
            
            # Redireciona para signup
            return redirect(campaign.signup_url)
        except QRCodeCampaign.DoesNotExist:
            return redirect('/recrutamento/varejo/')
```

---

## 📅 Parte 5: Roadmap de Implementação (8 semanas)

### Semana 1-2: Fundação + Landing Pages

```
GOALS:
✅ Landing pages por segmento (hospital + varejo)
✅ Identificação public vs internal
✅ Limpeza de dados (deletar segmentos extras)

TASKS:
├─ [2d] Criar views SegmentedLandingView
├─ [1d] Criar templates:
│  ├─ registration/recruitment_hospital.html
│  ├─ registration/recruitment_varejo.html
│  └─ registration/recruitment_default.html
├─ [1d] Atualizar models (User.public_type, Organization.segment)
├─ [1d] Migration database
├─ [1d] Criar forms públicos vs internos
├─ [2d] Script de limpeza de dados
└─ [1d] Teste: Landing page por segmento funciona

DELIVERABLES:
- Landing pages carregam baseado em /recrutamento/{segment}/
- Public type claramente definido na DB
- Segmentos extras deletados
```

### Semana 3-4: QR Code + Cadastro

```
GOALS:
✅ Geração de QR codes (HR gera código para loja)
✅ Fluxo de cadastro via QR
✅ Tracked scans & analytics

TASKS:
├─ [2d] Models QRCodeCampaign + migrations
├─ [1d] View QRCodeGeneratorView (HR cria QR)
├─ [1d] View QRCodeRedirectView (rastreado)
├─ [2d] Console: Dashboard de QR codes
│  ├─ Lista de códigos
│  ├─ Scans/signups por QR
│  └─ Botão "gerar novo QR"
├─ [1d] Template de cadastro público via QR
└─ [1d] Teste: QR → cadastro → user criado

DELIVERABLES:
- HR clica "gerar QR" → código PNG gerado
- QR apontada para /recrutamento/varejo/cadastro/public/?campaign=xyz
- Cada scan rastreado
- Novo candidato criado com public_type='public'
```

### Semana 5-6: Entrevista + Matching

```
GOALS:
✅ Quiz de entrevista integrado
✅ Score em 8 dimensões
✅ MatchingProfile criado
✅ Candidato visível para empresas

TASKS:
├─ [2d] Integrar quiz existente do Talk
├─ [2d] Criar MatchingProfile + migrations
├─ [2d] Algoritmo scoring (8 dimensões)
├─ [1d] MatchingProfile visible após score
├─ [2d] Console manager: ver candidatos por raio+score
│  ├─ Filtro: CEP (raio 5km), score mínimo
│  ├─ Custo de transporte visível
│  └─ Botão "contatar" (chat)
└─ [1d] Teste: Quiz → score → visible

DELIVERABLES:
- Candidato faz quiz em 20 min
- Score calculado (0-100)
- Manager vê lista de candidatos
- Chat pronto para contato
```

### Semana 7-8: Contratação + Analytics

```
GOALS:
✅ Fluxo de oferta (HR → Candidato)
✅ Aceitação/rejeição registrada
✅ HiringDecision + analytics

TASKS:
├─ [1d] Model Offer (job, salary, schedule, location)
├─ [1d] Chat integrado (HR + Candidato)
├─ [1d] View OfferCreate (HR monta oferta)
├─ [1d] Candidato recebe & responde oferta
├─ [1d] Model HiringDecision (accept/reject + feedback)
├─ [2d] Dashboard analytics:
│  ├─ Ofertas enviadas
│  ├─ Aceitação %
│  ├─ Tempo médio até hire
│  ├─ Custo por contratação
│  └─ Comparativo com mês anterior
└─ [1d] Teste end-to-end: QR → hire

DELIVERABLES:
- HR envia oferta (salário, horário, localização)
- Chat mostra detalhes
- Candidato aceita/recusa
- Analytics mostram: "800 lojas, 150 contratações este mês"
```

---

## 🧪 Parte 6: Testes E2E (End-to-End)

### Teste 1: QR Code → Candidato Público → Contratação

```
CENÁRIO: Varejo 800 - Gerente cria QR code, candidato cadastra, HR contrata

STEPS:
1. Login como HR de Retail 800
   └─ URL: /console/recruitment/qr-generator/

2. Criar QR code para "Loja Sul Shopping"
   └─ Clica: "Gerar novo QR"
   └─ Resultado: PNG baixado

3. Imprimir QR e colar na loja
   └─ Candidato vê QR na entrada

4. Candidato escaneia QR (via celular)
   └─ Redireciona: /recrutamento/varejo/cadastro/public/?campaign=abc123

5. Cadastro rápido
   └─ Nome: João da Silva
   └─ CEP: 01310-100
   └─ Disponibilidade: Disponível agora
   └─ Clica: Cadastrar

6. Confirmação email
   └─ "Sua candidatura foi registrada!"
   └─ "Faça sua entrevista em 24h"

7. João volta ao app (próximo dia)
   └─ Faz quiz de entrevista (20 min)
   └─ Responde 35 perguntas
   └─ Score: 78/100 em vendas

8. HR de Retail 800 busca candidatos
   └─ Filtro: "CEP 01310 (raio 5km), score 70+"
   └─ Resultado: João da Silva (78 pts, R$3.45 transporte diário)
   └─ Clica: "Contatar João"

9. Chat: HR → João
   └─ HR: "Tenemos vaga de vendedor na Loja Sul"
   └─ Salário: R$1.500
   └─ Horário: Ter-Sab 14h-22h
   └─ Transporte: Ônibus linha 407
   
   └─ João: "Quanto de bônus?"
   └─ HR: "5% sobre venda acima de R$5k"
   
   └─ João: "Beleza, aceito! Quando começo?"
   └─ HR: "Próxima segunda. Traz os documentos."

10. HR registra: Oferta aceita
    └─ HiringDecision criada
    └─ Analytics: +1 contratação
    └─ João aparece como "hire" no dashboard

11. Analytics dashboard mostra:
    └─ "Campanha Loja Sul Shopping: 47 scans, 12 signups, 3 contratados"
    └─ Custo por contratação: R$99/3 = R$33
    └─ Tempo médio: 8 dias
```

### Teste 2: Funcionário Interno → Promoção

```
CENÁRIO: Hospital - Enfermeiro faz "entrevista de promoção" para supervisor

STEPS:
1. HR de Hospital Central envia link:
   └─ /recrutamento/hospital/cadastro/internal/?company_id=123

2. Enfermeiro clica em link
   └─ Landing page: "Avance sua Carreira"
   └─ Formulário: Experiência, aspirações, disponibilidade para mudança

3. Preenche:
   └─ Cargo atual: Enfermeiro
   └─ Anos de experiência: 5
   └─ Interesse: Supervisor de Enfermagem
   └─ Aberto a transferência: Sim

4. Sistema registra como internal candidate
   └─ public_type = 'internal'
   └─ organization = Hospital Central

5. Faz entrevista específica para supervisores
   └─ 30 perguntas sobre liderança, decisão, conflito

6. Score: 85/100 em liderança
   └─ Recomendação: "Apto para supervisor"

7. HR vê no console:
   └─ Candidatos internos com potencial
   └─ "Enfermeira Maria: 85pts em liderança, pode virar supervisor na Ala Norte"

8. HR oferece promoção
   └─ Novo cargo: Supervisora
   └─ Novo salário: R$3.200
   └─ Novo setor: Ala Norte
   
   └─ Maria aceita

9. Analytics:
   └─ "1 promoção interna este mês"
   └─ "Retém 1 profissional sênior (economia: R$5k recrutamento)"
```

### Teste 3: Múltiplas Empresas, Mesmo Segmento

```
CENÁRIO: Varejo - 3 franquias (Loja A, B, C) usam Talk Recruitment

COMPANY 1: Loja A Shopping
├─ Gerente: Carlos
├─ Gera QR: "Loja A Shopping"
├─ 5 scans, 2 signups, 1 contratação

COMPANY 2: Loja B Shopping
├─ Gerente: Ana
├─ Gera QR: "Loja B Shopping"
├─ 8 scans, 4 signups, 2 contratações

COMPANY 3: Loja C Shopping
├─ Gerente: Pedro
├─ Gera QR: "Loja C Shopping"
├─ 3 scans, 1 signup, 0 contratações

POOL DE CANDIDATOS (Público)
├─ João (78pts, CEP 01310, vendas)
├─ Maria (65pts, CEP 01310, operacional)
├─ Pedro (82pts, CEP 01312, vendas)

MATCHING:
├─ Carlos busca: "vendedores, score 70+, raio 5km"
│  └─ Vê: João, Pedro
│  └─ Contrata: João
│  
├─ Ana busca: "vendedores, score 70+, raio 5km"
│  └─ Vê: Pedro (João já foi contratado, não aparece)
│  └─ Contrata: Pedro
│  
└─ Pedro busca: "operacional, score 60+, raio 5km"
   └─ Vê: Maria
   └─ Contrata: Maria

POOL: 3 candidatos públicos → 3 contratações → 0 desemprego
```

---

## ✅ Checklist Pré-Implementação

```
DECISÕES A CONFIRMAR:

[ ] Deletar mesmo estes segmentos?
    - Seguradora Generative
    - Manufatura XYZ
    - FinTech Rápido
    - Farmalab Biotech

[ ] Foco inicial: Varejo + Hospital?
    - Sim: Começar por varejo (QR code claro)
    - Depois: Hospital (interno + externo)

[ ] QR Code: Imprimir ou Digital?
    - Imprimir: Placa na loja (física)
    - Digital: WhatsApp, SMS, email
    - Ambos: Recomendado

[ ] Candidato Público: Precisa email verificado?
    - Sim: Enviamos link verificação
    - Não: Acesso imediato
    - Recomendação: Sim (melhor qualidade)

[ ] Múltiplas Lojas: Candidato vê todas?
    - Sim: Candidato vê 800 lojas (pode escolher)
    - Não: Candidato vê apenas loja do QR
    - Recomendação: Sim (máxima oportunidade)

[ ] Período de Teste E2E?
    - Quando começar: Semana 9 (após MVP 8 semanas)
    - Duração: 2 semanas
    - Com dados reais? Sim (empresa piloto)
```

---

## 📌 Sumário Executivo

| Fase | Semanas | Foco | Deliverable |
|------|---------|------|-------------|
| 1-2 | 2 | Landing pages + public/internal | Segmentação funcional |
| 3-4 | 2 | QR Code + cadastro | Geração QR tracked |
| 5-6 | 2 | Quiz + matching | Candidatos visíveis |
| 7-8 | 2 | Oferta + contratação | Hire registrada |
| 9+ | - | Testes E2E | QR → contratação |

**Próximo passo:** Confirmar decisões acima e iniciar Semana 1 com landing pages.
