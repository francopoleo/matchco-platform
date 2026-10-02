from pathlib import Path

from docx import Document
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.shared import Inches, Pt

from build_course_spec import (
    BLUE, DARK_BLUE, INK, MUTED,
    add_bullet, add_callout, add_heading, add_number, add_para, add_table,
    add_header_footer, configure_styles,
)


OUT = Path(__file__).with_name('Recrutamento_Governanca_LGPD_Contratos_Categorias.docx')


def build():
    doc = Document()
    configure_styles(doc)
    section = doc.sections[0]
    section.page_width = Inches(8.5)
    section.page_height = Inches(11)
    section.top_margin = Inches(1)
    section.bottom_margin = Inches(1)
    section.left_margin = Inches(1)
    section.right_margin = Inches(1)
    add_header_footer(section)

    add_para(doc, 'DOCUMENTO GERENCIAL', after=5, color=BLUE, bold=True, size=10)
    add_para(doc, 'Recrutamento, LGPD e Governança de Identidade', after=4, color=INK, bold=True, size=24)
    add_para(doc, 'Contratos de aceite, ciclo de vida da pessoa, transferência de dados, exclusão e taxonomia padronizada para shoppings e empresas.', after=16, color=MUTED, size=13)
    for label, value in [
        ('Produto', 'Talk Recruitment'),
        ('Escopo', 'Administradoras, shoppings, lojas, supermercados, candidatos e funcionários'),
        ('Fase prioritária', 'Cadastro simples via QR Code e triagem estruturada'),
        ('Status', 'Documento gerencial para aprovação e implementação'),
    ]:
        p = doc.add_paragraph()
        p.paragraph_format.space_after = Pt(2)
        from build_course_spec import add_run_text
        add_run_text(p, f'{label}: ', size=10.5, color=INK, bold=True)
        add_run_text(p, value, size=10.5, color=INK)
    add_callout(doc, 'Decisão central', 'A identidade da pessoa é única na plataforma. Candidaturas, vínculos, permissões e históricos são separados por empresa e por período, sem criar uma nova pessoa quando o candidato muda de loja ou de e-mail.')

    add_heading(doc, '1. Visão executiva', 1)
    add_para(doc, 'A plataforma será oferecida à administradora de um shopping, a redes de lojas e a supermercados. O ponto de entrada é simples: uma pessoa vê um QR Code em uma loja, abre uma página com a marca, encontra uma vaga e envia seus dados básicos. A plataforma transforma esse cadastro em um perfil estruturado, gera um match explicável e entrega à loja uma fila curta de candidatos relevantes.')
    add_para(doc, 'Depois, o mesmo perfil poderá participar de testes, entrevistas, contratação, onboarding, cursos, feeds, wikis e documentos internos. O produto deve preservar a rastreabilidade da pessoa sem expor histórico de uma empresa para outra.', after=8)
    add_bullet(doc, 'Fase 1: QR, loja, vaga, cadastro e triagem básica.')
    add_bullet(doc, 'Fase 2: pipeline, prioridade de 48 horas e pool do shopping.')
    add_bullet(doc, 'Fase 3: matching, testes, vídeo e IA assistiva.')
    add_bullet(doc, 'Fase 4: contratação, funcionário, cursos e ciclo de vida.')

    add_heading(doc, '2. Papéis e responsabilidades', 1)
    add_table(doc, ['Papel', 'Responsabilidade no produto', 'Acesso'], [
        ('Plataforma Talk', 'Software, segurança, operação e serviços contratados.', 'Operador ou controlador conforme finalidade.'),
        ('Administradora', 'Configura shopping, lojas, políticas e governança.', 'Visão consolidada contratada.'),
        ('Empresa/loja', 'Publica vaga, analisa, contata e contrata.', 'Candidaturas e dados autorizados.'),
        ('RH do shopping', 'Opera pool, triagem central e compartilhamento.', 'Escopo de lojas autorizado.'),
        ('Candidato', 'Informa dados, escolhe escopo e acompanha processo.', 'Próprio perfil e candidaturas.'),
        ('Funcionário', 'Usa o Talk interno após contratação.', 'Conteúdos da empresa atual.'),
    ], [1800, 4300, 3260])
    add_callout(doc, 'LGPD', 'O papel da plataforma muda conforme a finalidade. Quando trata dados sob instrução da empresa, atua como operadora; quando administra identidade global, pool e recomendações próprias, pode ser controladora ou controladora conjunta. O contrato deve refletir essa diferença.')

    add_heading(doc, '3. Identidade única e ciclo de vida', 1)
    add_para(doc, 'O CPF será o identificador civil de reconciliação no Brasil quando coletado e validado, mas a chave técnica será um UUID interno. E-mail e telefone são canais verificados; não são a identidade permanente.')
    add_table(doc, ['Objeto', 'Função', 'Regra'], [
        ('PersonIdentity', 'Pessoa única na plataforma.', 'UUID permanente; CPF protegido para reconciliação.'),
        ('CandidateProfile', 'Perfil profissional.', 'Experiências, preferências e dados de triagem.'),
        ('Application', 'Candidatura a vaga.', 'Loja, vaga, etapa, score e histórico.'),
        ('EmploymentRecord', 'Vínculo profissional.', 'Empresa, loja, cargo, turno e datas.'),
        ('UserAccount', 'Acesso ao Talk.', 'Pode usar e-mail pessoal ou corporativo.'),
        ('LearningHistory', 'Cursos e certificados.', 'Contextualizado pelo vínculo vigente.'),
    ], [1800, 3000, 4560])
    add_bullet(doc, 'Trocar e-mail pessoal por e-mail corporativo não cria segunda pessoa.')
    add_bullet(doc, 'Desligar o e-mail corporativo não apaga a identidade ou certificados pessoais.')
    add_bullet(doc, 'Transferir de loja recalcula permissões sem apagar o histórico.')
    add_bullet(doc, 'Recontratar cria novo vínculo, preservando vínculos anteriores.')

    add_heading(doc, '4. Contratos de aceite na plataforma', 1)
    add_para(doc, 'Os contratos devem ser versionados e aceitos dentro do sistema por empresas, candidatos e funcionários. O aceite precisa ser específico, rastreável e separado por finalidade.')
    add_table(doc, ['Documento', 'Quem aceita', 'Momento'], [
        ('Termos da empresa', 'Administradora/empresa', 'Ativação da conta empresarial.'),
        ('Termos da loja', 'Gestor/recrutador', 'Primeiro acesso à operação da loja.'),
        ('Aviso de privacidade', 'Candidato', 'Antes do primeiro envio de dados.'),
        ('Banco de talentos', 'Candidato', 'Opt-in separado e revogável.'),
        ('Compartilhamento', 'Candidato', 'Antes de aparecer a outras lojas/empresas.'),
        ('Vídeo/voz/IA', 'Candidato', 'Antes de gravar ou analisar.'),
        ('Acesso interno', 'Funcionário', 'Ativação após contratação.'),
    ], [2200, 2500, 4660])
    add_bullet(doc, 'Registrar versão, texto/identificador, data, hora, usuário, IP, origem e escopo.')
    add_bullet(doc, 'Permitir consulta posterior do termo aceito.')
    add_bullet(doc, 'Solicitar novo aceite quando a finalidade ou versão mudar.')
    add_bullet(doc, 'Não condicionar todos os serviços a consentimentos opcionais.')
    add_bullet(doc, 'Manter histórico de aceite mesmo quando o perfil for eliminado, sem conservar dados pessoais além do necessário.')

    add_heading(doc, '5. Fase 1 — cadastro simples via QR', 1)
    add_para(doc, 'A primeira fase deve ser extremamente simples e funcionar bem no celular. O objetivo é capturar dados suficientes para contato e triagem, sem exigir CPF, currículo ou vídeo no primeiro momento.')
    add_number(doc, 'Administrador cadastra o shopping e a loja.')
    add_number(doc, 'Sistema associa logo, endereço, categorias e vagas abertas.')
    add_number(doc, 'Sistema gera QR persistente com origem e campanha.')
    add_number(doc, 'Pessoa escaneia e vê a página pública da loja.')
    add_number(doc, 'Pessoa escolhe uma vaga ou deixa o perfil no banco de talentos.')
    add_number(doc, 'Pessoa informa nome, e-mail, telefone, localização e experiências.')
    add_number(doc, 'Pessoa responde perguntas comuns e específicas da vaga.')
    add_number(doc, 'Sistema calcula match inicial e envia à fila da loja.')
    add_number(doc, 'Loja recebe alertas e tem prazo de análise.')
    add_bullet(doc, 'CPF entra depois, quando a finalidade exigir contratação ou validação formal.')
    add_bullet(doc, 'Currículo é complemento, não requisito da primeira conversão.')

    add_heading(doc, '6. Taxonomia padronizada de shoppings', 1)
    add_para(doc, 'O catálogo deve ser configurável por shopping, mas começar com categorias comuns. O guia público do Bourbon Shopping usa filtros por shopping e atividade; isso confirma a necessidade de uma taxonomia operacional para lojas e serviços. Referência: https://www.bourbonshopping.com.br/lojas')
    add_table(doc, ['Categoria principal', 'Exemplos de operações', 'Funções frequentes'], [
        ('Alimentação', 'Restaurante, café, fast food, lanchonete, sorveteria.', 'Atendente, caixa, cozinha, garçom, gerente.'),
        ('Moda', 'Moda feminina, masculina, infantil e íntimos.', 'Vendedor, caixa, estoque, visual merchandising.'),
        ('Calçados e acessórios', 'Calçados, bolsas, joias, relógios e ótica.', 'Vendedor, consultor, caixa, estoque.'),
        ('Beleza e cuidados', 'Cosméticos, perfumaria, cabelo, estética e farmácia.', 'Consultor, vendedor, manicure, caixa.'),
        ('Esporte e lazer', 'Artigos esportivos, academia e entretenimento.', 'Vendedor, instrutor, atendimento.'),
        ('Casa e decoração', 'Móveis, presentes, utilidades e decoração.', 'Vendedor, projetista, estoque.'),
        ('Tecnologia', 'Celulares, informática, acessórios e assistência.', 'Vendedor, técnico, atendimento.'),
        ('Âncoras', 'Supermercado, hipermercado e loja de departamentos.', 'Operador, caixa, repositor, estoque.'),
        ('Serviços', 'Banco, lavanderia, telefonia, câmbio e conveniência.', 'Atendimento, operador, consultor.'),
        ('Cultura e entretenimento', 'Cinema, teatro, eventos e atrações.', 'Bilheteria, recepção, operação.'),
        ('Operações', 'Segurança, limpeza, manutenção, estacionamento e apoio.', 'Agente, auxiliar, técnico, supervisor.'),
    ], [1800, 3900, 3460])
    add_callout(doc, 'Regra de produto', 'Categorias são dados administráveis. Um shopping pode criar subcategorias, sinônimos e pesos próprios, mas não deve quebrar a taxonomia comum usada no matching entre empresas.')

    add_heading(doc, '7. Prioridade comercial e compartilhamento', 1)
    add_table(doc, ['Janela', 'Quem vê', 'Regra'], [
        ('0–24 horas', 'Loja da candidatura', 'Fila prioritária e lembrete.'),
        ('24–48 horas', 'Loja da candidatura', 'Ação válida ou alerta de vencimento.'),
        ('48 h–7 dias', 'Pool do shopping', 'RH e lojas elegíveis veem match autorizado.'),
        ('Após 7 dias', 'Pool regional/plataforma', 'Somente conforme consentimento.'),
        ('Entrevista/oferta', 'Participantes do processo', 'Evitar contato duplicado.'),
    ], [1600, 2900, 4660])
    add_para(doc, 'A prioridade é uma janela de análise, não propriedade sobre a pessoa. Visualizar um perfil não renova a exclusividade; é necessário contato, entrevista, teste, recusa ou outra ação registrada.', before=6)

    add_heading(doc, '8. LGPD, confidencialidade e eliminação', 1)
    add_bullet(doc, 'Minimização: coletar somente o necessário para a etapa.')
    add_bullet(doc, 'Transparência: informar quem recebe os dados e para qual finalidade.')
    add_bullet(doc, 'Confidencialidade: loja vê somente o escopo autorizado.')
    add_bullet(doc, 'CPF: cifrado, mascarado, auditado e nunca usado em URL ou QR.')
    add_bullet(doc, 'Exclusão: permitir descadastro e eliminação quando não houver retenção válida.')
    add_bullet(doc, 'Retenção: manter somente o mínimo exigido por obrigação legal, trabalhista ou defesa.')
    add_bullet(doc, 'IA: não usar dados sensíveis para eliminar ou ranquear pessoas.')
    add_bullet(doc, 'Titular: permitir acesso, correção, revogação, oposição e contestação.')
    add_para(doc, 'A ANPD define o operador como quem trata dados em nome do controlador e reconhece o CPF como dado pessoal. O contrato deve definir o papel da plataforma em cada finalidade e prever canal para o titular.', before=6, italic=True, color=MUTED)

    add_heading(doc, '9. Transferência e destruição de dados', 1)
    add_para(doc, 'Quando a empresa responsável precisar receber os dados e a plataforma deixar de manter a cópia operacional, o processo será formalizado por protocolo.')
    add_number(doc, 'Titular solicita transferência/eliminação.')
    add_number(doc, 'Plataforma confirma identidade e escopo.')
    add_number(doc, 'Identifica controlador destinatário.')
    add_number(doc, 'Monta pacote mínimo criptografado.')
    add_number(doc, 'Empresa confirma recebimento e integridade.')
    add_number(doc, 'Plataforma bloqueia novos usos e destrói cópias operacionais.')
    add_number(doc, 'Sistema emite manifesto e certificado de destruição.')
    add_bullet(doc, 'Destruir filas, índices, thumbnails, embeddings e cópias temporárias.')
    add_bullet(doc, 'Manter somente protocolo mínimo de auditoria, quando permitido.')
    add_bullet(doc, 'A empresa receptora responde pela retenção e exclusão dos dados que recebeu.')

    add_heading(doc, '10. Evolução após a fase 1', 1)
    add_table(doc, ['Fase', 'Entrega', 'Quando'], [
        ('1', 'QR, cadastro simples, categorias e perguntas.', 'Primeiro lançamento.'),
        ('2', 'Candidatura, pipeline e janela de prioridade.', 'Após validar conversão.'),
        ('3', 'Matching, pool e filtros avançados.', 'Quando houver volume.'),
        ('4', 'Testes, cursos e onboarding.', 'Após contratar primeiros usuários.'),
        ('5', 'Vídeo e IA assistiva.', 'Após governança e consentimento.'),
        ('6', 'Funcionário, transferências e desligamento.', 'Com integração operacional.'),
    ], [1000, 5000, 4160])

    add_heading(doc, '11. Arquitetura desacoplada', 1)
    add_para(doc, 'Recrutamento será um bounded context próprio. Ele poderá integrar-se ao Talk, mas não dependerá da implementação interna de cursos, learning, estudantes ou console. Isso permite evolução independente, testes isolados e eventual comercialização como produto separado.')
    add_table(doc, ['Camada', 'Responsabilidade', 'Contrato'], [
        ('Recruitment Core', 'Candidatos, vagas, candidaturas, pipeline, match e contratação.', 'Não importa views ou regras internas de outros apps.'),
        ('Identity Port', 'Identidade global, contas, e-mails e funcionário.', 'DTOs de pessoa, conta, vínculo e eventos.'),
        ('Learning Port', 'Testes, cursos e onboarding.', 'ID externo, título, versão, status e resultado.'),
        ('Notification Port', 'E-mail, SMS, WhatsApp e alertas.', 'Comando assíncrono e status de entrega.'),
        ('AI Matching Port', 'Extração, resumo e recomendação.', 'Entrada minimizada, modelo, versão e explicação.'),
    ], [1800, 3500, 4060])
    add_bullet(doc, 'O cadastro e a candidatura funcionam mesmo com cursos, IA ou notificações indisponíveis.')
    add_bullet(doc, 'Avaliações de curso usam IDs externos e snapshots, não ForeignKeys frágeis.')
    add_bullet(doc, 'Contratação emite eventos para o módulo de identidade, sem conhecer memberships internos.')
    add_bullet(doc, 'Desligamento emite evento para revogação, sem apagar o histórico de recrutamento.')
    add_bullet(doc, 'Cada integração possui adapter, DTO versionado, retry e teste de contrato.')
    add_bullet(doc, 'O núcleo de recrutamento não importa views de courses, learning, students ou console.')
    add_callout(doc, 'Regra de independência', 'Se o app de cursos for desligado, o recrutamento ainda deve cadastrar, receber candidaturas, ranquear, contatar e contratar. A integração com cursos é um serviço adicional, não um requisito para o fluxo básico.')

    add_heading(doc, '12. Critérios de aceite gerencial', 1)
    for item in [
        'Uma administradora consegue cadastrar shopping, loja, categoria e vaga sem suporte técnico.',
        'O QR abre a marca correta e registra a origem.',
        'O candidato conclui o cadastro inicial em poucos minutos.',
        'A loja recebe candidatos estruturados e priorizados, não uma lista infinita.',
        'O RH consegue encontrar matches em outras lojas conforme consentimento.',
        'A troca de e-mail não duplica a pessoa.',
        'A contratação transforma candidato em funcionário sem perder histórico.',
        'O funcionário recebe cursos, feeds, wikis e documentos da empresa correta.',
        'O desligamento revoga acesso interno sem destruir histórico que precise ser retido.',
        'O titular consegue consultar, revogar e solicitar eliminação dos dados.',
        'Toda versão de contrato aceito é auditável.',
        'O sistema demonstra isolamento entre shoppings, empresas e lojas.',
    ]:
        add_bullet(doc, item)

    add_heading(doc, '13. Fontes e premissas', 1)
    add_bullet(doc, 'Bourbon Shopping — Guia de lojas: https://www.bourbonshopping.com.br/lojas')
    add_bullet(doc, 'ANPD — Titular de dados e agentes de tratamento: https://www.gov.br/anpd/pt-br/assuntos/titular-de-dados')
    add_bullet(doc, 'ANPD — Perguntas frequentes sobre direitos e eliminação: https://www.gov.br/anpd/pt-br/acesso-a-informacao/perguntas-frequentes')
    add_callout(doc, 'Próxima decisão', 'Aprovar a Fase 1 como escopo inicial: QR por loja, página pública, cadastro simples, categorias padronizadas, perguntas comuns, consentimentos e fila inicial de candidatos.')

    doc.core_properties.title = 'Recrutamento — Governança, LGPD, Contratos e Categorias'
    doc.core_properties.subject = 'Documento gerencial do produto Talk Recruitment'
    doc.core_properties.author = 'Talk'
    doc.core_properties.keywords = 'recrutamento, LGPD, contratos, shopping, candidato, funcionário'
    doc.save(OUT)
    print(OUT)


if __name__ == '__main__':
    build()
