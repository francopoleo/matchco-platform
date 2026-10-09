# 🎥 Plano de Segurança e Armazenamento de Vídeos

## ⚠️ Problemas de Segurança com Vídeos

### Cenários de Risco:
```
1. Vídeo sensível (saúde) vazado publicamente
2. Usuário compartilha link do vídeo
3. Vídeo copiado/baixado ilegalmente
4. Acesso não autorizado (IP externo)
5. Alguém entra e "assiste" o vídeo sem aprender nada
6. DRM quebrado, vídeo circula por torrent
7. LGPD: dados pessoais na thumbnail/metadados
```

### Por que é crítico em saúde:
- 🏥 Conteúdo sensível (técnicas, protocolos)
- 👮 Compliance: LGPD, HIPAA, regulações médicas
- 🔐 Vazamento = responsabilidade legal
- 📹 Vídeo = evidência (auditoria importante)

---

## 1️⃣ OPÇÕES DE ARMAZENAMENTO

### OPÇÃO A: Upload Local + Servidor Próprio
```
❌ Vantagens: Controle total
✅ Desvantagens: 
   - Caro (servidor potente + banda larga)
   - Risco: perder dados
   - Lento para muitos usuários
   - Requer backup redundante
   - Conformidade complexa

Custo: ~$200-500/mês + infraestrutura
Melhor para: Poucos vídeos, baixo tráfego
```

### OPÇÃO B: AWS S3 (Recomendado para escala)
```
✅ Vantagens:
   - Escalável (cresce com demanda)
   - Seguro (criptografia AES-256)
   - CDN integrado (CloudFront)
   - Acesso controlado (IAM, presigned URLs)
   - Compliance: HIPAA, SOC 2 certificado
   - Backup automático
   - Regional (pode estar no Brasil = LGPD)

❌ Desvantagens:
   - Custo variável (paga por GB transferido)
   - Curva de aprendizado

Custo: ~$0,10-0,25 por GB (storage) + ~$0,08 por GB (saída)
Exemplo: 100GB vídeos, 10K views/mês = ~$50-100/mês
Melhor para: Produção profissional
```

### OPÇÃO C: Google Cloud Storage
```
✅ Similar ao AWS S3
✅ HIPAA certified
✅ Multi-regional (reduz latência)
❌ Preço similar

Custo: Comparável ao AWS
Melhor para: Se já usa Google Workspace
```

### OPÇÃO D: YouTube Private/Unlisted
```
❌ Vantagens: 
   - Hosting gratuito
   - Streaming confiável
   - Rastreamento básico

✅ Desvantagens:
   - Falta controle de acesso fino
   - Vídeo pode ser encontrado (SEO)
   - Termos de serviço restritivos
   - Sem proteção contra download
   - Sem DRM
   - YouTube Analytics genéricos
   - Dados sensivos na Google

Custo: Gratuito
Melhor para: Conteúdo público ou menos sensível
```

### OPÇÃO E: Vimeo Pro/Business
```
✅ Vantagens:
   - Seguro (foco em privacidade)
   - Controle de acesso fino
   - DRM opcional
   - Analytics detalhado
   - GDPR compliant
   - HIPAA opcional

❌ Desvantagens:
   - Caro para volume alto
   - Limite de armazenamento

Custo: $75-1200/mês (depende do plano)
Melhor para: Pequeno volume, máxima segurança
```

### OPÇÃO F: Hybrid (Recomendado para Talk)
```
✅ Vantagens:
   - Melhor custo-benefício
   - YouTube para conteúdo público
   - AWS S3 para conteúdo sensível
   - Máxima segurança + flexibilidade

Custo: $50-150/mês (conforme volume)
Melhor para: Produção profissional em saúde
```

---

## 2️⃣ ESTRATÉGIA HYBRID RECOMENDADA PARA TALK

### ARQUITETURA:

```
┌─────────────────────────────────────────┐
│         TALK LEARNING PLATFORM          │
└─────────────────────────────────────────┘
                    │
        ┌───────────┼───────────┐
        │           │           │
    ┌─────────┐ ┌──────────┐ ┌──────────┐
    │YOUTUBE  │ │ AWS S3   │ │ VIMEO    │
    │(Public) │ │(Private) │ │(Medical) │
    └─────────┘ └──────────┘ └──────────┘
```

### REGRAS DE ROTEAMENTO:

```python
class Video(models.Model):
    title = CharField
    storage_type = Choice([
        'youtube_public',      # Vídeos públicos
        'aws_s3_encrypted',    # Vídeos sensíveis
        'vimeo_hipaa'          # Conteúdo médico crítico
    ])
    
    # YouTube: Link do YouTube
    youtube_id = CharField(null=True)
    
    # AWS S3: Caminho do arquivo
    s3_key = CharField(null=True)  # ex: 'videos/higiene-maos.mp4'
    s3_bucket = CharField(default='talk-videos')
    
    # Vimeo: ID do vídeo
    vimeo_id = CharField(null=True)
    
    # Metadados
    module = FK(Module)
    duration_seconds = Integer
    file_size_mb = Integer
    thumbnail = ImageField
    
    # Segurança
    require_login = Boolean  # true = não público
    allowed_organizations = ManyToMany(Organization)  # Multi-tenant
    access_token_expiry_hours = Integer  # token vence após X horas

REGRAS:
├── Vídeo público (ex: demo) → YouTube
├── Vídeo de treinamento (ex: procedimento) → AWS S3 + DRM
├── Vídeo médico sensível (ex: cirurgia) → Vimeo HIPAA
└── Vídeo interno/confidencial → AWS S3 + 256-bit encryption
```

---

## 3️⃣ SEGURANÇA NÍVEL POR NÍVEL

### NÍVEL 1: CONTROLE DE ACESSO BÁSICO

```python
# 1. Autenticação: Só usuário logado pode ver
# 2. Autorização: Verificar se está inscrito no curso
# 3. Token com expiração

def get_video_access_token(request, video_id):
    """Gera token com validade de 1 hora"""
    user = request.user
    video = Video.objects.get(id=video_id)
    
    # Verificar se tem acesso
    enrollment = CourseEnrollment.objects.get(
        user=user,
        course=video.module.course
    )
    
    # Gerar token
    token = jwt.encode({
        'user_id': user.id,
        'video_id': video.id,
        'exp': timezone.now() + timedelta(hours=1)
    }, settings.SECRET_KEY)
    
    return token
```

**Implementação:**
- ✅ Login obrigatório
- ✅ Token JWT com expiry (1-2 horas)
- ✅ Verificar acesso por course enrollment
- ✅ Log: quem viu, quando, quanto tempo

**Risco residual:** Token pode ser compartilhado

---

### NÍVEL 2: PROTEÇÃO CONTRA COMPARTILHAMENTO

```python
# 1. Verificar IP (difícil de contornar que VPN)
# 2. Device ID
# 3. User-Agent
# 4. Rate limiting
# 5. Watermark (marca d'água no vídeo)

class VideoAccessLog(models.Model):
    user = FK(User)
    video = FK(Video)
    access_token = CharField
    ip_address = GenericIPAddress
    device_id = CharField  # fingerprint do navegador
    user_agent = CharField
    accessed_at = DateTime
    watched_percent = Integer
    duration_minutes = Integer

def validate_video_access(token, request):
    """Valida token + IP + device"""
    
    payload = jwt.decode(token, settings.SECRET_KEY)
    user_id = payload['user_id']
    
    # 1. Token válido?
    if payload['exp'] < timezone.now():
        raise PermissionDenied("Token expirado")
    
    # 2. IP é diferente muito de antes?
    last_access = VideoAccessLog.objects.filter(
        user_id=user_id
    ).latest('accessed_at')
    
    if last_access.ip_address != request.META['REMOTE_ADDR']:
        # IP muda frequentemente (OK)
        # Mas se mudar cada minuto = suspeito
        pass
    
    # 3. Device ID constante?
    current_device_id = hash(request.META['HTTP_USER_AGENT'])
    if last_access.device_id != current_device_id:
        # Log suspeita
        log_suspicious_access(user_id, "device_change")
    
    # 4. Rate limit: 5 requisições por minuto
    recent_accesses = VideoAccessLog.objects.filter(
        user=user_id,
        accessed_at__gte=timezone.now() - timedelta(minutes=1)
    ).count()
    
    if recent_accesses > 5:
        raise PermissionDenied("Muitas requisições")
    
    return True
```

**Implementação:**
- ✅ Tudo do Nível 1 +
- ✅ IP whitelist/check
- ✅ Device fingerprint
- ✅ Rate limiting
- ✅ Marca d'água (watermark) no vídeo
- ✅ Bloqueio de downloads

**Risco residual:** Pode ser quebrado por usuário técnico

---

### NÍVEL 3: DRM (Digital Rights Management)

```python
# 1. Criptografia do vídeo (HLS/DASH com criptografia)
# 2. Chave de criptografia por usuário
# 3. Verificação contínua de acesso
# 4. Expiração automática de stream

OPÇÕES DE DRM:
├── AWS Elemental MediaConvert + CloudFront
├── HLS com chave de encriptação
├── DASH com Widevine DRM
└── Vimeo + DRM integrado

class VideoDRM(models.Model):
    video = FK(Video)
    
    # HLS stream encriptado
    m3u8_manifest = URLField  # ex: https://cdn.talk.com/v/xyz.m3u8
    encryption_key = BinaryField  # 128-bit AES key
    key_expiry = DateTime
    
    # Acesso restrito por usuário
    allowed_users = ManyToMany(User)
    expires_at = DateTime
    
    # Estatísticas
    max_concurrent_streams = Integer  # ex: 1 (só 1 browser)
    geo_blocked = Boolean  # Só Brasil?
```

**Implementação:**
- ✅ Tudo do Nível 2 +
- ✅ Vídeo criptografado (não pode baixar)
- ✅ Chave por usuário
- ✅ Expiração automática
- ✅ Max 1 stream por usuário (impossível compartilhar)
- ✅ Geo-blocking (só Brasil)

**Custo:** +50-100/mês (processamento)
**Risco residual:** Quase zero (Hollywood usa este)

---

## 4️⃣ YOUTUBE: COMO FAZER SEGURO

### Problema com YouTube padrão:
```
❌ Link pode ser achado por SEO
❌ Sem controle de acesso fino
❌ Sem DRM
❌ Impossível rastrear quem viu
❌ Dados sensivos na Google
❌ Termos de serviço podem mudar
```

### Solução: YouTube + Access Control

```python
class YouTubeVideo(models.Model):
    youtube_id = CharField  # ex: "dQw4w9WgXcQ"
    url = URLField  # https://youtu.be/dQw4w9WgXcQ
    title = CharField
    module = FK(Module)
    
    # Segurança
    embed_disabled = Boolean  # Desabilita embed público
    requires_login = Boolean  # Login obrigatório
    allowed_organizations = ManyToMany(Organization)
    
    # Rastreamento
    track_views = Boolean  # Integração com Google Analytics
    
def render_youtube_video(request, video_id):
    """Renderiza YouTube com segurança"""
    
    video = YouTubeVideo.objects.get(id=video_id)
    
    # 1. Verificar acesso
    if video.requires_login and not request.user.is_authenticated:
        return redirect('login')
    
    # 2. Verificar organização
    if video.allowed_organizations.exists():
        user_org = request.user.active_organization
        if user_org not in video.allowed_organizations.all():
            return PermissionDenied()
    
    # 3. Log da visualização
    YouTubeViewLog.objects.create(
        user=request.user,
        video=video,
        watched_at=timezone.now()
    )
    
    # 4. Render embed seguro (no-share, no-download)
    return render(request, 'video.html', {
        'youtube_id': video.youtube_id,
        'params': {
            'controls': 1,
            'modestbranding': 1,  # Sem logo YouTube
            'fs': 0,  # Sem fullscreen
            'rel': 0,  # Sem vídeos recomendados
        }
    })

# Template seguro
<iframe 
    width="100%" height="600"
    src="https://www.youtube.com/embed/{{ youtube_id }}?{{ params }}"
    frameborder="0"
    allow="autoplay; encrypted-media"
    allowfullscreen>
</iframe>
```

**Segurança YouTube:**
- ✅ Nível 1: Autenticação obrigatória
- ✅ Nível 1: Organizações permitidas
- ✅ Nível 1: Rastreamento de views
- ❌ Nível 2-3: Sem DRM (YouTube não oferece)

**Melhor para:**
- Conteúdo público/semi-público
- Tutoriais, demos
- NÃO para conteúdo sensível

---

## 5️⃣ AWS S3: IMPLEMENTAÇÃO SEGURA

### Arquitetura:

```
[Usuário] 
    ↓ (login)
[Django App] 
    ↓ (verifica acesso)
[JWT Token] 
    ↓ (com expiry 1h)
[Presigned URL]
    ↓ (autorização temporária)
[AWS CloudFront]
    ↓ (CDN global)
[AWS S3] 
    ↓ (arquivo criptografado)
[Video Stream]
```

### Código:

```python
import boto3
from botocore.exceptions import ClientError
from datetime import timedelta

class S3VideoManager:
    def __init__(self):
        self.s3_client = boto3.client(
            's3',
            region_name='sa-east-1'  # São Paulo = LGPD compliant
        )
        self.bucket = 'talk-videos-encrypted'
    
    def upload_video(self, video_file, module_id, user_id):
        """Upload seguro com encriptação AES-256"""
        
        key = f"videos/{module_id}/{video_file.name}"
        
        # 1. Criptografar antes de enviar
        try:
            response = self.s3_client.put_object(
                Bucket=self.bucket,
                Key=key,
                Body=video_file,
                ServerSideEncryption='AES256',  # Criptografia S3-managed
                # Ou usar KMS para máxima segurança:
                # ServerSideEncryption='aws:kms',
                # SSEKMSKeyId='arn:aws:kms:...'
                
                # Metadata
                Metadata={
                    'upload_by': str(user_id),
                    'upload_date': timezone.now().isoformat()
                },
                
                # ACL privado (só Talk pode acessar)
                ACL='private'
            )
            return key
        except ClientError as e:
            logger.error(f"S3 upload error: {e}")
            raise
    
    def generate_presigned_url(self, key, user_id, expiry_hours=1):
        """Gera URL temporária para o usuário"""
        
        try:
            # URL válida por 1 hora
            url = self.s3_client.generate_presigned_url(
                'get_object',
                Params={
                    'Bucket': self.bucket,
                    'Key': key
                },
                ExpiresIn=int(expiry_hours * 3600)  # em segundos
            )
            
            # Log para auditoria
            S3AccessLog.objects.create(
                user_id=user_id,
                s3_key=key,
                url_generated_at=timezone.now(),
                expires_at=timezone.now() + timedelta(hours=expiry_hours)
            )
            
            return url
        except ClientError as e:
            logger.error(f"Presigned URL error: {e}")
            raise

def get_video_stream_url(request, video_id):
    """Endpoint para obter URL do vídeo"""
    
    video = Video.objects.get(id=video_id)
    user = request.user
    
    # 1. Verificar autenticação
    if not user.is_authenticated:
        return JsonResponse({'error': 'Not authenticated'}, status=401)
    
    # 2. Verificar acesso ao curso
    try:
        enrollment = CourseEnrollment.objects.get(
            user=user,
            course=video.module.course
        )
    except CourseEnrollment.DoesNotExist:
        return JsonResponse({'error': 'Not enrolled'}, status=403)
    
    # 3. Verificar organização
    if video.allowed_organizations.exists():
        if user.active_organization not in video.allowed_organizations.all():
            return JsonResponse({'error': 'Wrong organization'}, status=403)
    
    # 4. Gerar URL presignada
    s3_manager = S3VideoManager()
    try:
        presigned_url = s3_manager.generate_presigned_url(
            video.s3_key,
            user.id,
            expiry_hours=1
        )
        
        # Log para rastreamento
        VideoAccessLog.objects.create(
            user=user,
            video=video,
            ip_address=request.META.get('REMOTE_ADDR'),
            accessed_at=timezone.now()
        )
        
        return JsonResponse({
            'url': presigned_url,
            'expires_in_seconds': 3600,
            'title': video.title
        })
    except Exception as e:
        logger.error(f"Error generating presigned URL: {e}")
        return JsonResponse({'error': 'Server error'}, status=500)
```

**Segurança S3:**
- ✅ Criptografia AES-256 (S3-managed) ou KMS
- ✅ URLs presignadas com expiry (1 hora)
- ✅ ACL privado (só Talk acessa)
- ✅ Log de acesso
- ✅ IP logging
- ✅ Bucket em São Paulo (LGPD)

---

## 6️⃣ RASTREAMENTO DE VÍDEOS

```python
class VideoAnalytics(models.Model):
    """Rastreamento completo de vídeo"""
    
    user = FK(User)
    video = FK(Video)
    module = FK(Module)
    
    # Timeline
    started_at = DateTime
    ended_at = DateTime (null)
    last_activity = DateTime
    
    # Progresso
    total_duration_seconds = Integer  # ex: 600 (10 min)
    watched_seconds = Integer  # ex: 570 (95%)
    watch_percent = Integer  # 95
    
    # Interações
    paused_count = Integer
    rewind_count = Integer
    skipped_seconds = Integer
    
    # Validação
    is_valid = Boolean  # Atingiu 95%?
    marked_complete = Boolean
    
    # Compliance
    ip_accessed = GenericIPAddress
    device_fingerprint = CharField
    browser_info = CharField

# JavaScript para rastreamento

<script>
const video = document.getElementById('video-player');
let analyticsData = {
    startedAt: new Date(),
    watchedSeconds: 0,
    pausedCount: 0,
    rewindCount: 0
};

// Rastrear reprodução
video.addEventListener('play', () => {
    console.log('Vídeo iniciado');
});

// Rastrear progresso
video.addEventListener('timeupdate', () => {
    analyticsData.watchedSeconds = video.currentTime;
    const watchPercent = (video.currentTime / video.duration) * 100;
    
    // Enviar para servidor a cada 30 segundos
    if (Math.floor(video.currentTime) % 30 === 0) {
        fetch('/api/video/track/', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': getCookie('csrftoken')
            },
            body: JSON.stringify({
                video_id: videoId,
                watched_seconds: analyticsData.watchedSeconds,
                watch_percent: Math.floor(watchPercent),
                duration: video.duration
            })
        });
    }
    
    // Ao atingir 95%, marcar como completo
    if (watchPercent >= 95) {
        markVideoComplete();
    }
});

// Rastrear pausa
video.addEventListener('pause', () => {
    analyticsData.pausedCount++;
});

// Rastrear rewind
let lastTime = 0;
video.addEventListener('timeupdate', () => {
    if (video.currentTime < lastTime - 2) {  // Rewind > 2 seg
        analyticsData.rewindCount++;
    }
    lastTime = video.currentTime;
});

// Ao sair
window.addEventListener('beforeunload', () => {
    sendAnalytics(analyticsData);
});
</script>
```

---

## 7️⃣ CONFORMIDADE & COMPLIANCE

### LGPD (Lei Geral de Proteção de Dados - Brasil)

```python
class VideoLGPDCompliance(models.Model):
    """Rastreamento para LGPD"""
    
    video = FK(Video)
    
    # Armazenamento
    stored_in_region = CharField  # 'sa-east-1' (São Paulo)
    encryption_method = CharField  # 'AES-256'
    
    # Consentimento
    requires_consent = Boolean
    consent_version = Integer
    
    # Direitos do usuário
    allow_deletion = Boolean  # Usuário pode pedir deleção
    allow_export = Boolean  # Usuário pode exportar dados
    retention_days = Integer  # Quanto tempo guardar
    
    # Auditoria
    creation_date = DateTime
    last_audit_date = DateTime
    next_audit_date = DateTime

# Implementação
COMPLIANCE_RULES = {
    'storage_region': 'sa-east-1',  # Brasil
    'encryption': 'AES-256',  # Mínimo obrigatório
    'consent_required': True,  # LGPD obriga consentimento
    'retention_period_days': 365,  # Guardar por 1 ano
    'right_to_deletion': True,  # Usuário pode pedir deleção
    'right_to_access': True,  # Usuário pode ver seus dados
    'data_export_format': 'json'  # Exportar em JSON
}

def delete_user_data_on_request(user_id):
    """Direito de deleção (LGPD Art. 17)"""
    
    # 1. Deletar todos os vídeos do usuário
    Video.objects.filter(owner_id=user_id).delete()
    
    # 2. Deletar logs de acesso
    VideoAccessLog.objects.filter(user_id=user_id).delete()
    
    # 3. Deletar analytics
    VideoAnalytics.objects.filter(user_id=user_id).delete()
    
    # 4. Deletar S3
    s3_manager = S3VideoManager()
    user_videos = Video.objects.filter(owner_id=user_id)
    for video in user_videos:
        try:
            s3_manager.delete_video(video.s3_key)
        except:
            logger.error(f"Failed to delete S3: {video.s3_key}")
    
    # 5. Log para auditoria
    DataDeletionLog.objects.create(
        user_id=user_id,
        action='full_deletion',
        requested_at=timezone.now()
    )
```

### HIPAA (Saúde - se aplicável)

```python
# HIPAA Requirements
HIPAA_REQUIREMENTS = {
    'encryption_at_rest': 'AES-256',  # Obrigatório
    'encryption_in_transit': 'TLS 1.2+',  # Obrigatório
    'access_logging': True,  # Log todo acesso
    'audit_trail': True,  # Auditoria completa
    'data_integrity': True,  # Verificar integridade
    'business_associate_agreement': True,  # BAA com AWS
    'penetration_testing': 'annual',  # Teste de segurança 1x/ano
    'incident_response_plan': True,  # Plano de resposta
}
```

---

## 8️⃣ MATRIX DE DECISÃO

```
┌──────────────────┬─────────────┬──────────────┬──────────────┐
│ Tipo de Vídeo    │ Armazenamento│ Segurança    │ Custo        │
├──────────────────┼─────────────┼──────────────┼──────────────┤
│ Público (Demo)   │ YouTube     │ Nível 1      │ $0           │
│ Treinamento      │ AWS S3      │ Nível 2      │ $50-100/mês  │
│ Médico (Sensível)│ AWS S3      │ Nível 3 (DRM)│ $100-200/mês │
│ Confidencial      │ AWS S3 + KMS│ Nível 3 (DRM)│ $150-250/mês │
│ Muito crítico    │ Vimeo HIPAA │ Nível 3      │ $200-500/mês │
└──────────────────┴─────────────┴──────────────┴──────────────┘
```

---

## 9️⃣ IMPLEMENTAÇÃO RECOMENDADA PARA TALK

### FASE 1 (Semana 1-2): Basics
```
✅ YouTube para vídeos públicos (demo, overview)
✅ AWS S3 com presigned URLs para conteúdo sensível
✅ Autenticação obrigatória
✅ Rastreamento básico (quem, quando, quanto tempo)
✅ LGPD compliance: dados em São Paulo, criptografia
```

### FASE 2 (Semana 3-4): Rastreamento
```
✅ Analytics de vídeo (% assistido)
✅ Marca como completo em 95%
✅ Auditoria (log de acesso)
✅ Integração com completion tracking
```

### FASE 3 (Semana 5-6): Segurança Avançada
```
✅ DRM para vídeos médicos
✅ Watermarking (marca d'água)
✅ Rate limiting
✅ Geo-blocking (só Brasil)
✅ IP whitelist
```

### FASE 4 (Opcional): HIPAA
```
✅ Business Associate Agreement (BAA) com AWS
✅ Teste de penetração
✅ Conformidade completa
```

---

## 🔟 CHECKLIST SEGURANÇA

### Antes de ir para Produção:

- [ ] Todos vídeos criptografados AES-256
- [ ] URLs presignadas com expiry (max 1 hora)
- [ ] Autenticação obrigatória
- [ ] Rastreamento de acesso (IP + device)
- [ ] Log de auditoria
- [ ] LGPD compliance (dados em SP)
- [ ] Backup automático (3+ cópias)
- [ ] Teste de penetração
- [ ] Plano de resposta a incidentes
- [ ] Termos de serviço claros
- [ ] Consentimento do usuário

### Produção:
- [ ] SSL/TLS em todas as conexões
- [ ] WAF (Web Application Firewall)
- [ ] Rate limiting
- [ ] DDoS protection
- [ ] Monitoramento 24/7
- [ ] Alertas de acesso anormal

---

## 🎯 RESUMO EXECUTIVO

| Requisito | Solução | Custo | Tempo |
|-----------|---------|-------|-------|
| Públicos | YouTube | $0 | 1 dia |
| Sensíveis | AWS S3 + presigned URL | $50-100/mês | 3 dias |
| Médicos | AWS S3 + DRM | $100-200/mês | 1 semana |
| Rastreamento | Analytics + logging | Incluído | 1 semana |
| LGPD | Criptografia + São Paulo | Incluído | 2 dias |
| HIPAA | BAA + auditoria | Incluído | Contínuo |

**Recomendação:** Hybrid (YouTube + AWS S3) = Melhor custo-benefício para Talk

---

## 📋 PRÓXIMOS PASSOS

1. **Você quer começar com AWS S3?**
2. **Usar YouTube para tudo?**
3. **Implementar Hybrid desde o início?**

Qual estratégia preferir?
