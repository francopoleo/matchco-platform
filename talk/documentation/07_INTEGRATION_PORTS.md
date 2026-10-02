# Contratos de Integração (Ports) - APIs Internas

**Público**: Desenvolvedores, arquitetos, integradores  
**Última atualização**: 2026-10-02

---

## Visão Geral

O módulo de Recruitment é arquitetonicamente desacoplado do resto do Talk através de **ports** (interfaces) bem definidas. Cada integração é:

- **Versionada**: Contratos imutáveis, mudanças são novas versões
- **Testável**: Pode ser mockada, não é obrigatória para o core
- **Lazy-loaded**: Carregada sob demanda conforme `RECRUITMENT_INTEGRATIONS`
- **Resiliente**: Falhas em integrações não quebram recrutamento

---

## 1. Identity Port

**Responsabilidade**: Gerenciar identidade global de pessoas, e-mails verificados, conversão para usuários internos.

**Arquivo**: `recruitment/integrations/identity.py`

### Interface

```python
class IdentityPort:
    def get_or_create_global_identity(
        self, 
        email: str, 
        phone: str = None, 
        name: str = None
    ) -> dict:
        """
        Retorna ou cria identidade global de uma pessoa.
        
        Returns:
            {
                'person_id': UUID,
                'email': str (normalizado),
                'phone': str (normalizado),
                'name': str,
            }
        """
        
    def get_identity_by_email(self, email: str) -> dict:
        """Busca identidade por e-mail normalizado."""
        
    def link_email_to_identity(
        self, 
        person_id: UUID, 
        email: str
    ) -> dict:
        """Adiciona e-mail verificado à identidade."""
        
    def create_employee_account(
        self, 
        person_id: UUID,
        organization_id: UUID,
        role: str = 'employee'
    ) -> dict:
        """
        Converte pessoa em usuário interno da organização.
        
        Returns:
            {
                'user_id': UUID,
                'username': str,
                'account_active': bool,
            }
        """
        
    def verify_cpf(
        self, 
        cpf: str, 
        person_id: UUID = None
    ) -> dict:
        """
        Valida CPF contra serviço externo (se disponível).
        
        Returns:
            {
                'valid': bool,
                'person_id': UUID (se já existe),
                'status': str (válido/inválido/duplicado),
            }
        """
```

### Adaptador Padrão (Nulo)

```python
class NullIdentityPort(IdentityPort):
    """Adaptador que funciona sem serviço de identidade."""
    
    def get_or_create_global_identity(self, email, phone=None, name=None):
        return {
            'person_id': generate_uuid(),
            'email': normalize_email(email),
            'phone': normalize_phone(phone),
            'name': name,
        }
```

---

## 2. Learning Port (Cursos)

**Responsabilidade**: Criar assessments de recrutamento, receber resultados de testes/cursos.

**Arquivo**: `recruitment/integrations/learning.py`

### Interface

```python
class LearningPort:
    def request_assessment(
        self,
        candidate_id: UUID,
        assessment_type: str,  # 'quiz', 'course', 'test'
        external_id: str,
        title_snapshot: str,
        min_score: float = None,
    ) -> dict:
        """
        Solicita avaliação para candidato.
        
        Args:
            assessment_type: 'quiz' | 'course' | 'test'
            external_id: ID do quiz/course no sistema de cursos
            min_score: nota mínima para passar (0-100)
        
        Returns:
            {
                'assessment_id': UUID,
                'status': 'pending',  # pendente de conclusão
                'access_url': str,
            }
        """
        
    def get_assessment_result(self, assessment_id: UUID) -> dict:
        """
        Busca resultado de avaliação já completada.
        
        Returns:
            {
                'status': 'pending' | 'completed' | 'failed' | 'expired',
                'score': float (0-100),
                'passed': bool,
                'completed_at': datetime,
            }
        """
        
    def get_enrollments_by_candidate(self, candidate_id: UUID) -> list:
        """Busca todos os cursos/testes que candidato completou."""
```

### Adaptador Padrão (Nulo)

```python
class NullLearningPort(LearningPort):
    """Não executa nenhuma integração; candidatura continua sem avaliações."""
    
    def request_assessment(self, candidate_id, assessment_type, external_id, 
                          title_snapshot, min_score=None):
        return {
            'assessment_id': generate_uuid(),
            'status': 'pending',
            'access_url': None,  # Nenhuma avaliação real
        }
```

---

## 3. Notification Port (E-mail, SMS, WhatsApp)

**Responsabilidade**: Enviar notificações ao candidato, lojista, RH.

**Arquivo**: `recruitment/integrations/notifications.py`

### Interface

```python
class NotificationPort:
    def notify_candidate_new_application(
        self,
        candidate_email: str,
        position_title: str,
        store_name: str,
    ) -> dict:
        """Notifica candidato que sua candidatura foi recebida."""
        
    def notify_store_new_candidate(
        self,
        store_email: str,
        store_name: str,
        candidate_name: str,
        position_title: str,
        match_score: float,
    ) -> dict:
        """Notifica loja que novo candidato apareceu."""
        
    def notify_candidate_status_change(
        self,
        candidate_email: str,
        application_id: UUID,
        new_status: str,
        message: str = None,
    ) -> dict:
        """Candidato é notificado de mudança de etapa."""
        
    def send_otp(
        self,
        email_or_phone: str,
        code: str,
        method: str = 'email',  # 'email' | 'sms' | 'whatsapp'
    ) -> dict:
        """Envia código OTP para autenticação."""
```

### Adaptador Padrão (Nulo)

```python
class NullNotificationPort(NotificationPort):
    """Não envia notificações; apenas registra log."""
    
    def notify_candidate_new_application(self, candidate_email, 
                                        position_title, store_name):
        logger.info(f"Would notify {candidate_email} about {position_title}")
        return {'status': 'logged', 'sent': False}
```

---

## 4. File/Resume Port (Armazenamento)

**Responsabilidade**: Armazenar currículos, documentos, vídeos de forma segura.

**Arquivo**: `recruitment/integrations/files.py`

### Interface

```python
class FilePort:
    def store_resume(
        self,
        candidate_id: UUID,
        file_content: bytes,
        filename: str,
        content_type: str = 'application/pdf',
    ) -> dict:
        """
        Armazena currículo do candidato.
        
        Returns:
            {
                'file_id': UUID,
                'url': str (URL seguro, tempo limitado),
                'size_bytes': int,
            }
        """
        
    def get_resume_url(self, file_id: UUID, expires_in_hours: int = 24) -> str:
        """Retorna URL temporário para download."""
        
    def delete_resume(self, file_id: UUID) -> bool:
        """Deleta currículo conforme LGPD/consentimento."""
        
    def store_video(
        self,
        candidate_id: UUID,
        video_content: bytes,
        filename: str,
    ) -> dict:
        """Armazena vídeo de apresentação."""
```

### Adaptador Padrão (Nulo)

```python
class NullFilePort(FilePort):
    """Armazena em memória; não persiste após restart."""
    
    _storage = {}  # In-memory storage
    
    def store_resume(self, candidate_id, file_content, filename, 
                    content_type='application/pdf'):
        file_id = generate_uuid()
        self._storage[file_id] = file_content
        return {
            'file_id': file_id,
            'url': f'/recruitment/resume/{file_id}/',
            'size_bytes': len(file_content),
        }
```

---

## 5. AI Matching Port (Inteligência Artificial)

**Responsabilidade**: Sugerir matches, extrair informações de currículos, resumir perfis.

**Arquivo**: `recruitment/integrations/ai.py`

### Interface

```python
class AIMatchingPort:
    def suggest_matches(
        self,
        position_id: UUID,
        candidate_ids: list,
        limit: int = 10,
    ) -> list:
        """
        Ordena candidatos por similaridade à vaga (além do score).
        
        Returns:
            [
                {
                    'candidate_id': UUID,
                    'ai_score': float (0-100),
                    'reasoning': str,  # Por que este candidato
                    'missing_skills': [str],  # O que falta
                }
            ]
        """
        
    def extract_resume_skills(self, resume_text: str) -> dict:
        """
        Extrai habilidades de um currículo via IA.
        
        Returns:
            {
                'skills': [str],
                'experience_level': str,
                'years_of_experience': int,
            }
        """
        
    def summarize_candidate(self, candidate_profile: dict) -> str:
        """Gera resumo legível de perfil do candidato."""
        
    def detect_bias(
        self,
        candidate_data: dict,
        position_requirements: dict,
    ) -> dict:
        """
        Detecta possíveis vieses no ranking.
        
        Returns:
            {
                'has_bias': bool,
                'indicators': [str],  # Atributos potencialmente discriminatórios
            }
        """
```

### Adaptador Padrão (Nulo)

```python
class NullAIMatchingPort(AIMatchingPort):
    """Sem IA; usa apenas score de regras."""
    
    def suggest_matches(self, position_id, candidate_ids, limit=10):
        # Retorna ordem aleatória ou sem IA
        return []
    
    def extract_resume_skills(self, resume_text):
        return {'skills': [], 'experience_level': 'unknown', 
                'years_of_experience': 0}
```

---

## 6. Organization Port (Acesso a Lojas/Departamentos)

**Responsabilidade**: Consultar dados de organização (lojas, departamentos, funções).

**Arquivo**: `recruitment/integrations/organization.py`

### Interface

```python
class OrganizationPort:
    def get_stores(self, organization_id: UUID) -> list:
        """Retorna todas as lojas/departamentos da organização."""
        
    def get_store(self, store_id: UUID) -> dict:
        """Retorna dados de uma loja específica."""
        
    def get_job_functions(self, organization_id: UUID) -> list:
        """Retorna funções de trabalho disponíveis."""
        
    def user_has_access_to_store(
        self,
        user_id: UUID,
        store_id: UUID,
    ) -> bool:
        """Verifica se usuário pode acessar loja (permissões)."""
```

---

## Carregamento de Integrations

### Configuração

Em `settings.py`:

```python
RECRUITMENT_INTEGRATIONS = {
    'identity': 'recruitment.integrations.identity.IdentityPort',
    'learning': 'recruitment.integrations.learning.LearningPort',
    'notifications': 'recruitment.integrations.notifications.NotificationPort',
    'files': 'recruitment.integrations.files.FilePort',
    'ai': 'recruitment.integrations.ai.AIMatchingPort',
    'organization': 'recruitment.integrations.organization.OrganizationPort',
}
```

### Uso em Views/Services

```python
from recruitment.services import get_integration

# Em qualquer view/service:
identity_port = get_integration('identity')
learning_port = get_integration('learning')

# Se integração não está configurada:
person_id = identity_port.get_or_create_global_identity(
    email='candidate@example.com'
)
```

### Comportamento Seguro

Se uma integração retorna erro:

```python
try:
    assessment = learning_port.request_assessment(...)
except IntegrationUnavailable:
    # Continua sem avaliação; registra pendência para depois
    log_pending_assessment(candidate_id, assessment_type)
    return {'status': 'pending_assessment'}
```

---

## Princípios de Design

### 1. Independência
- Recruitment funciona **sem** qualquer integração
- Cada integração é **opcional**
- Falhas não bloqueiam o core

### 2. Versionamento
- Novas versões de ports não quebram old code
- Novas features em novas versões de interface
- Backward compatibility onde possível

### 3. Testabilidade
- Todos os adapters podem ser mockados
- Tests não dependem de serviços externos
- Fixtures de teste incluem null adapters

### 4. Auditoria
- Cada integração registra input/output
- Versão de adapter usada é registrada
- Falhas são loggadas com contexto

---

## Adicionando Nova Integração

1. **Criar arquivo**: `recruitment/integrations/new_service.py`
2. **Definir Port abstrato**:
   ```python
   class NewServicePort:
       def operation(self, params) -> dict:
           """Documentação clara do contrato."""
   ```

3. **Criar Null Adapter**:
   ```python
   class NullNewServicePort(NewServicePort):
       def operation(self, params):
           return {'status': 'no-op'}
   ```

4. **Registrar em settings**:
   ```python
   RECRUITMENT_INTEGRATIONS = {
       # ...
       'new_service': 'recruitment.integrations.new_service.NewServicePort',
   }
   ```

5. **Usar em views**:
   ```python
   port = get_integration('new_service')
   result = port.operation(params)
   ```

---

## Testando Integrations

```python
# Em tests:
from recruitment.integrations.identity import NullIdentityPort

def test_candidate_signup_without_identity_service():
    port = NullIdentityPort()
    person = port.get_or_create_global_identity('test@example.com')
    assert person['person_id'] is not None
```

---

**Última Atualização**: 2026-10-02  
**Referência**: `recruitment/integrations/` folder
