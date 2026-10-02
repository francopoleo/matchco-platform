from datetime import date
from pathlib import Path

from docx import Document
from docx.enum.section import WD_SECTION
from docx.enum.table import WD_CELL_VERTICAL_ALIGNMENT, WD_TABLE_ALIGNMENT
from docx.enum.text import WD_ALIGN_PARAGRAPH, WD_BREAK
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Inches, Pt, RGBColor


OUT = Path(__file__).with_name('Plano_Implementacao_Cursos_Enterprise.docx')
BLUE = RGBColor(46, 116, 181)
DARK_BLUE = RGBColor(31, 77, 120)
INK = RGBColor(11, 37, 69)
MUTED = RGBColor(92, 105, 120)
LIGHT_BLUE = 'E8EEF5'
LIGHT_GRAY = 'F2F4F7'
PALE_BLUE = 'F4F6F9'
WHITE = RGBColor(255, 255, 255)


def set_font(run, name='Calibri', size=11, color=None, bold=None, italic=None):
    run.font.name = name
    run._element.get_or_add_rPr().rFonts.set(qn('w:ascii'), name)
    run._element.get_or_add_rPr().rFonts.set(qn('w:hAnsi'), name)
    run.font.size = Pt(size)
    if color is not None:
        run.font.color.rgb = color
    if bold is not None:
        run.bold = bold
    if italic is not None:
        run.italic = italic


def shade(cell, fill):
    tc_pr = cell._tc.get_or_add_tcPr()
    shd = tc_pr.find(qn('w:shd'))
    if shd is None:
        shd = OxmlElement('w:shd')
        tc_pr.append(shd)
    shd.set(qn('w:fill'), fill)


def cell_margins(cell, top=80, start=120, bottom=80, end=120):
    tc = cell._tc
    tc_pr = tc.get_or_add_tcPr()
    tc_mar = tc_pr.first_child_found_in('w:tcMar')
    if tc_mar is None:
        tc_mar = OxmlElement('w:tcMar')
        tc_pr.append(tc_mar)
    for side, value in [('top', top), ('start', start), ('bottom', bottom), ('end', end)]:
        node = tc_mar.find(qn(f'w:{side}'))
        if node is None:
            node = OxmlElement(f'w:{side}')
            tc_mar.append(node)
        node.set(qn('w:w'), str(value))
        node.set(qn('w:type'), 'dxa')


def set_cell_width(cell, width_dxa):
    cell.width = Inches(width_dxa / 1440)
    tc_pr = cell._tc.get_or_add_tcPr()
    tc_w = tc_pr.find(qn('w:tcW'))
    if tc_w is None:
        tc_w = OxmlElement('w:tcW')
        tc_pr.append(tc_w)
    tc_w.set(qn('w:w'), str(width_dxa))
    tc_w.set(qn('w:type'), 'dxa')


def set_table_geometry(table, widths):
    table.alignment = WD_TABLE_ALIGNMENT.LEFT
    table.autofit = False
    tbl_pr = table._tbl.tblPr
    tbl_w = tbl_pr.find(qn('w:tblW'))
    if tbl_w is None:
        tbl_w = OxmlElement('w:tblW')
        tbl_pr.append(tbl_w)
    tbl_w.set(qn('w:w'), str(sum(widths)))
    tbl_w.set(qn('w:type'), 'dxa')
    tbl_ind = tbl_pr.find(qn('w:tblInd'))
    if tbl_ind is None:
        tbl_ind = OxmlElement('w:tblInd')
        tbl_pr.append(tbl_ind)
    tbl_ind.set(qn('w:w'), '120')
    tbl_ind.set(qn('w:type'), 'dxa')
    grid = table._tbl.tblGrid
    for child in list(grid):
        grid.remove(child)
    for width in widths:
        col = OxmlElement('w:gridCol')
        col.set(qn('w:w'), str(width))
        grid.append(col)
    for row in table.rows:
        for cell, width in zip(row.cells, widths):
            set_cell_width(cell, width)
            cell_margins(cell)
            cell.vertical_alignment = WD_CELL_VERTICAL_ALIGNMENT.CENTER


def set_borders(table, color='C7D2E0', size='6'):
    tbl_pr = table._tbl.tblPr
    borders = tbl_pr.first_child_found_in('w:tblBorders')
    if borders is None:
        borders = OxmlElement('w:tblBorders')
        tbl_pr.append(borders)
    for edge in ('top', 'left', 'bottom', 'right', 'insideH', 'insideV'):
        tag = 'w:' + edge
        el = borders.find(qn(tag))
        if el is None:
            el = OxmlElement(tag)
            borders.append(el)
        el.set(qn('w:val'), 'single')
        el.set(qn('w:sz'), size)
        el.set(qn('w:space'), '0')
        el.set(qn('w:color'), color)


def add_run_text(paragraph, text, **kwargs):
    run = paragraph.add_run(text)
    set_font(run, **kwargs)
    return run


def add_para(doc, text='', style=None, before=0, after=6, line=1.10, color=None, bold=False, italic=False, size=11, align=None):
    p = doc.add_paragraph(style=style)
    p.paragraph_format.space_before = Pt(before)
    p.paragraph_format.space_after = Pt(after)
    p.paragraph_format.line_spacing = line
    if align is not None:
        p.alignment = align
    if text:
        add_run_text(p, text, size=size, color=color, bold=bold, italic=italic)
    return p


def add_bullet(doc, text, level=0):
    p = doc.add_paragraph(style='List Bullet' if level == 0 else 'List Bullet 2')
    p.paragraph_format.space_after = Pt(4)
    p.paragraph_format.line_spacing = 1.167
    add_run_text(p, text, size=11, color=INK)
    return p


def add_number(doc, text, level=0):
    p = doc.add_paragraph(style='List Number' if level == 0 else 'List Number 2')
    p.paragraph_format.space_after = Pt(4)
    p.paragraph_format.line_spacing = 1.167
    add_run_text(p, text, size=11, color=INK)
    return p


def add_heading(doc, text, level=1):
    p = doc.add_paragraph(style=f'Heading {level}')
    p.add_run(text)
    return p


def add_callout(doc, label, text, fill=PALE_BLUE):
    table = doc.add_table(rows=1, cols=1)
    set_table_geometry(table, [9360])
    set_borders(table, color='B8C8DA', size='8')
    cell = table.cell(0, 0)
    shade(cell, fill)
    p = cell.paragraphs[0]
    p.paragraph_format.space_after = Pt(2)
    add_run_text(p, label + '  ', size=10, color=DARK_BLUE, bold=True)
    add_run_text(p, text, size=10.5, color=INK)
    doc.add_paragraph().paragraph_format.space_after = Pt(2)


def add_table(doc, headers, rows, widths, header_fill=LIGHT_BLUE, font_size=9.5):
    table = doc.add_table(rows=1, cols=len(headers))
    set_table_geometry(table, widths)
    set_borders(table)
    for i, header in enumerate(headers):
        cell = table.rows[0].cells[i]
        shade(cell, header_fill)
        p = cell.paragraphs[0]
        p.paragraph_format.space_after = Pt(0)
        add_run_text(p, header, size=9.5, color=INK, bold=True)
    for row in rows:
        cells = table.add_row().cells
        for i, value in enumerate(row):
            cell = cells[i]
            p = cell.paragraphs[0]
            p.paragraph_format.space_after = Pt(0)
            add_run_text(p, str(value), size=font_size, color=INK)
    set_table_geometry(table, widths)
    return table


def add_page_break(doc):
    p = doc.add_paragraph()
    p.add_run().add_break(WD_BREAK.PAGE)


def configure_styles(doc):
    styles = doc.styles
    normal = styles['Normal']
    normal.font.name = 'Calibri'
    normal._element.rPr.rFonts.set(qn('w:ascii'), 'Calibri')
    normal._element.rPr.rFonts.set(qn('w:hAnsi'), 'Calibri')
    normal.font.size = Pt(11)
    normal.font.color.rgb = INK
    normal.paragraph_format.space_after = Pt(6)
    normal.paragraph_format.line_spacing = 1.10
    for name, size, color, before, after in [
        ('Heading 1', 16, BLUE, 16, 8),
        ('Heading 2', 13, BLUE, 12, 6),
        ('Heading 3', 12, DARK_BLUE, 8, 4),
    ]:
        style = styles[name]
        style.font.name = 'Calibri'
        style._element.rPr.rFonts.set(qn('w:ascii'), 'Calibri')
        style._element.rPr.rFonts.set(qn('w:hAnsi'), 'Calibri')
        style.font.size = Pt(size)
        style.font.bold = True
        style.font.color.rgb = color
        style.paragraph_format.space_before = Pt(before)
        style.paragraph_format.space_after = Pt(after)
        style.paragraph_format.keep_with_next = True
    for name in ('List Bullet', 'List Bullet 2', 'List Number', 'List Number 2'):
        style = styles[name]
        style.font.name = 'Calibri'
        style._element.rPr.rFonts.set(qn('w:ascii'), 'Calibri')
        style._element.rPr.rFonts.set(qn('w:hAnsi'), 'Calibri')
        style.font.size = Pt(11)
        style.paragraph_format.space_after = Pt(4)
        style.paragraph_format.line_spacing = 1.167


def add_header_footer(section):
    section.header_distance = Inches(0.492)
    section.footer_distance = Inches(0.492)
    hp = section.header.paragraphs[0]
    hp.alignment = WD_ALIGN_PARAGRAPH.LEFT
    hp.paragraph_format.space_after = Pt(0)
    add_run_text(hp, 'TALK  |  ESPECIFICAÇÃO DE IMPLEMENTAÇÃO', size=8.5, color=MUTED, bold=True)
    fp = section.footer.paragraphs[0]
    fp.alignment = WD_ALIGN_PARAGRAPH.RIGHT
    fp.paragraph_format.space_before = Pt(0)
    add_run_text(fp, 'Uso interno · Ambiente de desenvolvimento', size=8.5, color=MUTED)
    fp.add_run('    ·    ')
    field = OxmlElement('w:fldSimple')
    field.set(qn('w:instr'), 'PAGE')
    fp._p.append(field)


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

    # Masthead
    add_para(doc, 'ESPECIFICAÇÃO DE IMPLEMENTAÇÃO', after=5, color=BLUE, bold=True, size=10)
    add_para(doc, 'Cursos Enterprise e Motor de Progresso', after=4, color=INK, bold=True, size=24)
    add_para(doc, 'Plano funcional, técnico e de aceite para transformar o módulo de cursos em uma experiência profissional de aprendizagem corporativa.', after=16, color=MUTED, size=13)
    for label, value in [
        ('Produto', 'Talk Learning / Console multiempresa'),
        ('Escopo', 'Cursos, módulos, conteúdos, avaliações, trilhas, certificados e auditoria'),
        ('Status', 'Documento-base para implementação e aceite incremental'),
        ('Data', date.today().strftime('%d/%m/%Y')),
        ('Premissa', 'Ambiente de desenvolvimento pode ser refeito; não há legado produtivo a preservar'),
    ]:
        p = doc.add_paragraph()
        p.paragraph_format.space_after = Pt(2)
        add_run_text(p, f'{label}: ', size=10.5, color=INK, bold=True)
        add_run_text(p, value, size=10.5, color=INK)
    add_callout(doc, 'Decisão de produto', 'Implementaremos um motor único de acesso, progresso e conclusão. As telas, APIs, player, certificados e relatórios não poderão criar regras próprias fora desse motor.')
    add_para(doc, 'Este documento será o contrato de implementação: cada requisito possui uma definição verificável e cada fase termina com critérios objetivos de aceite.', after=8)

    add_heading(doc, '1. Objetivo e resultado esperado', 1)
    add_para(doc, 'Entregar um sistema de cursos corporativo, multiempresa e auditável, com navegação livre ou controlada, pré-requisitos, progressão linear, consumo mensurável de conteúdos, avaliações, certificados e relatórios confiáveis por empresa, organização, unidade e usuário.')
    add_para(doc, 'A experiência deverá funcionar para dois extremos sem duplicar arquitetura:', after=4, bold=True)
    add_bullet(doc, 'Experiência simples: o colaborador clica em “Continuar”, acompanha o progresso e conclui conteúdos sem fricção.')
    add_bullet(doc, 'Experiência enterprise: a empresa exige ordem, tempo, percentual de vídeo, leitura de documentos, aprovação, evidências, certificados e auditoria.')
    add_callout(doc, 'Princípio', 'Flexibilidade deve ser configuração do curso, não código diferente por página. Um curso pode ser livre; outro, linear e obrigatório; ambos usam o mesmo modelo e o mesmo motor.')

    add_heading(doc, '2. Base existente e lacunas', 1)
    add_para(doc, 'O código atual já possui elementos que serão reaproveitados: Course, Module, Content, tipos Text/Video/File/Quiz, CourseEnroll, ContentEnroll, ContentEvent, ContentTrail, TrailStep, CourseCertificate e registro de tentativas de quiz.')
    add_table(doc, ['Capacidade atual', 'Situação', 'Direção'], [
        ('Matrícula', 'Existe e já usa TenantUser', 'Centralizar regras de acesso e validade'),
        ('Progresso', 'Conta conteúdos concluídos', 'Evoluir para estado, percentual, tempo e evidência'),
        ('Eventos', 'Registra abertura, atividade e vídeo', 'Padronizar heartbeat, idempotência e auditoria'),
        ('Quiz', 'Nota mínima e tentativas existentes', 'Vincular aprovação à liberação e conclusão'),
        ('Trilhas', 'Possui passos e pré-requisito', 'Integrar ao motor de cursos'),
        ('Certificado', 'Modelo existente', 'Condicionar a regras explícitas e publicar evidência'),
        ('Multiempresa', 'Schemas tenant e filtros de organização', 'Manter isolamento em todas as consultas'),
    ], [2100, 3000, 4260])

    add_heading(doc, '3. Modos de experiência do curso', 1)
    add_table(doc, ['Modo', 'Comportamento', 'Uso recomendado', 'Aceite principal'], [
        ('Livre', 'Qualquer conteúdo disponível após matrícula.', 'Biblioteca e consulta.', 'Aluno acessa qualquer item permitido.'),
        ('Linear', 'Próximo item bloqueado até conclusão do anterior.', 'Compliance e onboarding.', 'Tentativa de pular é bloqueada com motivo.'),
        ('Pré-requisito', 'Item depende de conteúdo, módulo ou curso.', 'Formação por níveis.', 'Dependência aparece e é validada no servidor.'),
        ('Liberação programada', 'Item abre por data ou dias após matrícula.', 'Turmas e jornadas.', 'Antes da data, acesso é negado e explicado.'),
        ('Domínio', 'Quiz, nota mínima e tentativas controlam avanço.', 'Certificações internas.', 'Aprovação libera etapa e reprovação mantém bloqueio.'),
        ('Compliance', 'Exige combinação de consumo, confirmação e evidência.', 'Treinamento regulatório.', 'Auditoria mostra condições cumpridas e timestamps.'),
    ], [1250, 3000, 2200, 2910])
    add_para(doc, 'Configuração inicial recomendada:', before=6, bold=True)
    add_bullet(doc, 'Cursos comuns: Livre ou Linear, com conclusão manual.')
    add_bullet(doc, 'Cursos obrigatórios: Linear + quiz obrigatório.')
    add_bullet(doc, 'Cursos regulatórios: Linear + consumo mínimo + quiz + evidência.')

    add_heading(doc, '4. Estados e regras de acesso', 1)
    add_table(doc, ['Estado', 'Significado', 'Pode abrir?', 'Próxima ação'], [
        ('Pendente', 'Ainda não iniciado.', 'Conforme regras.', 'Iniciar conteúdo.'),
        ('Disponível', 'Todas as condições foram atendidas.', 'Sim.', 'Continuar ou concluir.'),
        ('Em andamento', 'Há evento ou posição salva.', 'Sim.', 'Retomar de onde parou.'),
        ('Bloqueado', 'Há regra pendente.', 'Não.', 'Mostrar requisito faltante.'),
        ('Concluído', 'Todas as condições do item foram cumpridas.', 'Sim, para revisão.', 'Avançar ou revisar.'),
        ('Reprovado', 'Avaliação abaixo da nota mínima.', 'Conforme tentativas.', 'Refazer conforme política.'),
        ('Expirado', 'Janela de acesso terminou.', 'Não.', 'Solicitar renovação ao gestor.'),
    ], [1500, 2850, 1500, 3510])
    add_callout(doc, 'Regra de segurança', 'A interface pode antecipar o estado, mas somente o backend decide acesso, conclusão, certificado e relatório. Nunca confiar em botão, URL, JavaScript ou evento isolado enviado pelo navegador.')

    add_heading(doc, '5. Regras por tipo de conteúdo', 1)
    add_table(doc, ['Tipo', 'Regra básica', 'Regra enterprise', 'Dados registrados'], [
        ('Texto', 'Abrir + “Concluir”.', 'Tempo mínimo + rolagem + confirmação.', 'Abertura, tempo, conclusão, confirmação.'),
        ('Vídeo', 'Assistir até percentual configurado.', '90–95% + heartbeat + proteção contra salto.', 'Posição, segundos ativos, percentual, sessões.'),
        ('PDF', 'Abrir + “Concluir”.', 'Visualizar páginas mínimas + confirmação ou quiz.', 'Páginas, última posição, tempo, download.'),
        ('Apresentação', 'Percorrer slides + “Concluir”.', 'Cobertura mínima + tempo ativo.', 'Slides vistos, posição e tempo.'),
        ('Quiz', 'Responder e obter resultado.', 'Nota mínima, tentativas, prazo e pré-requisito.', 'Tentativas, respostas, nota, aprovação.'),
        ('Externo/presencial', 'Conclusão manual.', 'Aprovação do gestor + anexo/evidência.', 'Responsável, data, anexo e justificativa.'),
    ], [1250, 2600, 3000, 2510])
    add_para(doc, 'Não é possível provar atenção humana apenas com telemetria. Para auditoria, a plataforma deve declarar “evidência técnica de consumo”, combinando tempo, percentual e avaliação quando necessário.', before=6, italic=True, color=MUTED)

    add_heading(doc, '6. Modelo de dados proposto', 1)
    add_para(doc, 'A evolução deve preservar o isolamento tenant. Toda entidade de aprendizagem deve apontar para TenantUser e para TenantOrganization quando aplicável. O usuário público jamais será gravado diretamente em ForeignKey tenant.')
    add_table(doc, ['Entidade', 'Responsabilidade', 'Campos essenciais'], [
        ('CourseProgressPolicy', 'Configuração de progressão do curso.', 'mode, completion_mode, certificate_required, access_window.'),
        ('ContentCompletionPolicy', 'Regra por item.', 'rule, minimum_seconds, minimum_percent, required_quiz, required_score.'),
        ('LearningProgress', 'Estado atual do aluno por conteúdo.', 'user, course, module, content, status, started_at, completed_at.'),
        ('LearningEvidence', 'Evidência de conclusão.', 'progress, source, active_seconds, percent, payload, recorded_at.'),
        ('ContentPrerequisite', 'Dependências entre itens.', 'source, target, condition, minimum_score.'),
        ('CourseAccessGrant', 'Matrícula e janela de acesso.', 'user, course, source, starts_at, ends_at, status.'),
        ('LearningEvent', 'Linha do tempo auditável.', 'user, event, object, session, timestamp, metadata.'),
    ], [1850, 2900, 4610])
    add_para(doc, 'Compatibilidade de desenvolvimento: como não há legado produtivo, podemos recriar as tabelas e os dados de teste em vez de carregar modelos antigos indefinidamente. O reset demo deverá gerar todas as configurações e cenários necessários.', before=6)

    add_heading(doc, '7. Motor central de regras', 1)
    add_para(doc, 'Criar um serviço único, por exemplo learning/progress.py ou learning/services/progression.py, com contratos estáveis:')
    add_bullet(doc, 'can_access_course(user, course)')
    add_bullet(doc, 'can_access_content(user, content)')
    add_bullet(doc, 'get_progress(user, course)')
    add_bullet(doc, 'get_content_status(user, content)')
    add_bullet(doc, 'record_consumption(user, content, event_data)')
    add_bullet(doc, 'evaluate_completion(user, content)')
    add_bullet(doc, 'complete_content(user, content, source)')
    add_bullet(doc, 'get_next_available_content(user, course)')
    add_bullet(doc, 'issue_certificate_if_eligible(user, course)')
    add_para(doc, 'Todos os endpoints, views, player, API e relatórios devem chamar esses serviços. Nenhuma tela poderá implementar uma versão simplificada da regra.', before=6, bold=True)

    add_heading(doc, '8. Telemetria, tempo e evidência', 1)
    add_para(doc, 'O player deve enviar eventos idempotentes, com session_id, timestamp do cliente, timestamp do servidor, posição e duração. O servidor deve limitar valores, rejeitar saltos impossíveis e consolidar o progresso sem duplicar segundos.')
    add_table(doc, ['Métrica', 'Como medir', 'Limite/controle'], [
        ('Tempo ativo', 'Heartbeat enquanto aba/player está ativo.', 'Ignorar eventos duplicados e intervalos absurdos.'),
        ('Vídeo', 'currentTime/duration em intervalos curtos.', 'Limitar avanço artificial e aceitar retomada.'),
        ('PDF', 'Página alcançada e tempo ativo.', 'Não contar somente download como leitura.'),
        ('Apresentação', 'Slide visto e permanência mínima.', 'Registrar cobertura e última posição.'),
        ('Quiz', 'Tentativa persistida no servidor.', 'Sem confiar na nota enviada pelo cliente.'),
    ], [1800, 3600, 3960])

    add_heading(doc, '9. Fluxos de usuário', 1)
    add_heading(doc, '9.1 Continuar curso', 2)
    add_number(doc, 'Usuário abre o curso.')
    add_number(doc, 'Servidor calcula o primeiro item disponível.')
    add_number(doc, 'Interface mostra “Continuar curso”.')
    add_number(doc, 'Usuário retoma a posição salva ou inicia o item.')
    add_number(doc, 'Ao concluir, o motor recalcula o próximo item.')
    add_number(doc, 'Se o curso inteiro estiver elegível, emite certificado conforme política.')
    add_heading(doc, '9.2 Bloqueio por requisito', 2)
    add_number(doc, 'Usuário tenta abrir item bloqueado.')
    add_number(doc, 'Backend retorna 403 funcional com código de motivo.')
    add_number(doc, 'UI mostra o requisito: “Conclua X”, “Aguarde data”, “Atinga 70%”.')
    add_number(doc, 'Após cumprir, o mesmo item passa a disponível sem ajuste manual.')
    add_heading(doc, '9.3 Reprovação', 2)
    add_number(doc, 'Quiz é enviado e corrigido no servidor.')
    add_number(doc, 'Tentativa, respostas e nota são persistidas.')
    add_number(doc, 'Se aprovado, libera o próximo requisito.')
    add_number(doc, 'Se reprovado, aplica política de tentativas e intervalo.')

    add_heading(doc, '10. Experiência do player e do console', 1)
    add_bullet(doc, 'Player com barra de progresso do curso, módulo e conteúdo.')
    add_bullet(doc, 'Lista lateral com estados visualmente distintos: disponível, bloqueado, em andamento e concluído.')
    add_bullet(doc, 'Botão “Continuar” sempre apontando para o próximo item válido.')
    add_bullet(doc, 'Mensagem explícita para qualquer bloqueio.')
    add_bullet(doc, 'Indicador de tempo e percentual quando a regra exigir consumo mensurável.')
    add_bullet(doc, 'Resumo final antes do certificado: condições cumpridas e pendências.')
    add_bullet(doc, 'Console com editor visual da ordem e das regras do curso.')
    add_bullet(doc, 'Pré-visualização como aluno antes de publicar.')

    add_heading(doc, '11. Relatórios enterprise', 1)
    add_table(doc, ['Relatório', 'Filtros', 'Indicadores'], [
        ('Progresso por curso', 'Empresa, organização, curso, período.', 'Inscritos, iniciados, ativos, concluídos, média.'),
        ('Progresso por usuário', 'Usuário, empresa, curso.', 'Percentual, tempo, última atividade, pendência.'),
        ('Compliance', 'Curso obrigatório, empresa, período.', 'Aprovados, vencidos, evidência, certificado.'),
        ('Conteúdo', 'Tipo, curso, módulo.', 'Abandono, tempo, conclusão, tentativas.'),
        ('Auditoria', 'Usuário, evento, objeto, data.', 'Linha do tempo e origem técnica.'),
    ], [1900, 3000, 4460])
    add_para(doc, 'Todos os relatórios devem respeitar organização/empresa selecionada no topo do console. O superadmin pode escolher uma empresa ou visão consolidada, sem misturar dados na visão de uma empresa individual.', before=6)

    add_heading(doc, '12. Certificados e validade', 1)
    add_bullet(doc, 'Certificado somente após todas as condições do curso.')
    add_bullet(doc, 'Número único, usuário, curso, empresa, data e versão do curso.')
    add_bullet(doc, 'Possibilidade de validade e data de expiração.')
    add_bullet(doc, 'Revalidação por nova versão ou novo quiz.')
    add_bullet(doc, 'Página pública/privada de validação por código.')
    add_bullet(doc, 'Revogação com motivo e histórico imutável.')

    add_heading(doc, '13. Segurança e consistência multiempresa', 1)
    add_bullet(doc, 'Converter usuário público para TenantUser na entrada dos serviços.')
    add_bullet(doc, 'Nunca aceitar organization, company ou user apenas pelo payload do navegador.')
    add_bullet(doc, 'Filtrar sempre pelo schema tenant e, quando aplicável, pela organização ativa.')
    add_bullet(doc, 'Validar pré-requisitos e conclusão no servidor.')
    add_bullet(doc, 'Usar transações para conclusão, aprovação e emissão de certificado.')
    add_bullet(doc, 'Garantir idempotência para eventos e cliques repetidos.')
    add_bullet(doc, 'Não permitir que URL de conteúdo bloqueado contorne o player.')
    add_callout(doc, 'Critério de isolamento', 'Um usuário matriculado em duas empresas terá progresso, evidências, matrículas e certificados separados por tenant/empresa conforme o modelo de negócio. A mesma conta não pode misturar o histórico de uma empresa na outra.')

    add_heading(doc, '14. Plano de implementação por fases', 1)
    add_table(doc, ['Fase', 'Entrega', 'Resultado verificável'], [
        ('0. Contrato', 'Modelos finais, enums, permissões e seed.', 'Banco de desenvolvimento recriável.'),
        ('1. Motor', 'Acesso, status, conclusão e próximo item.', 'Todas as telas usam uma regra única.'),
        ('2. Navegação', 'Livre, linear e pré-requisitos.', 'Curso bloqueia/desbloqueia corretamente.'),
        ('3. Consumo', 'Vídeo, tempo, PDF e apresentação.', 'Progresso técnico e retomada confiáveis.'),
        ('4. Avaliação', 'Quiz, nota, tentativas e domínio.', 'Aprovação controla avanço.'),
        ('5. Drip', 'Datas, dias após matrícula e coortes.', 'Conteúdo abre conforme agenda.'),
        ('6. Evidência', 'Compliance, aprovação e anexos.', 'Auditoria explica a conclusão.'),
        ('7. Console', 'Editor, preview e relatórios.', 'Admin configura sem suporte técnico.'),
        ('8. Certificação', 'Certificados, validade e revogação.', 'Emissão auditável e verificável.'),
    ], [1250, 4000, 4110])
    add_para(doc, 'Ordem recomendada: Fases 0–2 primeiro, pois todas as funcionalidades posteriores dependem do motor central.', before=6, bold=True)

    add_heading(doc, '15. Estratégia de desenvolvimento e dados de teste', 1)
    add_para(doc, 'Como o ambiente é exclusivamente de teste/desenvolvimento e não há legado produtivo, o banco pode ser recriado de forma controlada. O reset deve ser determinístico e gerar cenários que cubram todos os modos.')
    add_bullet(doc, 'Criar cursos Livre, Linear, Pré-requisito, Drip, Domínio e Compliance.')
    add_bullet(doc, 'Criar conteúdos Text, Video, PDF, Apresentação, Quiz e Externo.')
    add_bullet(doc, 'Criar usuários com progresso zero, em andamento, concluído, reprovado e expirado.')
    add_bullet(doc, 'Criar empresas Bourbon Shopping, Shopping XYZ, Hospital ABC e Seguradora XYZ.')
    add_bullet(doc, 'Criar superadmin e memberships coerentes em todos os tenants.')
    add_bullet(doc, 'Permitir reset-only e reset + seed, sempre preservando domínios de desenvolvimento.')
    add_bullet(doc, 'Testar visão individual da empresa e visão consolidada do superadmin.')

    add_heading(doc, '16. Critérios de aceite', 1)
    add_table(doc, ['ID', 'Critério', 'Evidência de aceite'], [
        ('A-01', 'Curso Livre permite acessar qualquer conteúdo autorizado.', 'Teste de acesso fora de ordem passa.'),
        ('A-02', 'Curso Linear bloqueia o próximo item.', 'Servidor retorna motivo de bloqueio.'),
        ('A-03', 'Pré-requisito é validado no servidor.', 'Alterar URL não libera conteúdo.'),
        ('A-04', 'Vídeo calcula percentual e retoma posição.', 'Sessão interrompida continua corretamente.'),
        ('A-05', 'PDF/apresentação registram consumo configurado.', 'Páginas/slides aparecem na evidência.'),
        ('A-06', 'Quiz controla nota e tentativas.', 'Reprovação não libera próxima etapa.'),
        ('A-07', 'Drip respeita data e dias após matrícula.', 'Antes da data, item permanece bloqueado.'),
        ('A-08', 'Certificado só é emitido com todas as regras.', 'Curso incompleto não gera certificado.'),
        ('A-09', 'Relatórios respeitam empresa selecionada.', 'XYZ não exibe Bourbon.'),
        ('A-10', 'Superadmin pode consolidar sem misturar visão individual.', 'Alternância de empresa preserva a página.'),
        ('A-11', 'Reset recria dados e configurações.', 'Seed deixa ambiente completo e reproduzível.'),
        ('A-12', 'Fluxo funciona por web e API.', 'Mesmas regras em ambos os canais.'),
    ], [850, 4750, 3760])

    add_heading(doc, '17. Estratégia de testes', 1)
    add_bullet(doc, 'Testes unitários para cada modo de acesso e conclusão.')
    add_bullet(doc, 'Testes de integração para matrícula, progresso, quiz e certificado.')
    add_bullet(doc, 'Testes de tenant: usuário e curso de uma empresa não aparecem em outra.')
    add_bullet(doc, 'Testes de idempotência: repetir evento ou clique não duplica tempo, pontos ou certificado.')
    add_bullet(doc, 'Testes de segurança: bloquear URL direta, payload adulterado e troca de organização.')
    add_bullet(doc, 'Testes de interface: player, estados, mensagens e botão continuar.')
    add_bullet(doc, 'Testes de carga para eventos de vídeo e relatórios.')

    add_heading(doc, '18. Decisões que ficam registradas', 1)
    add_bullet(doc, 'O progresso é configurável por curso e por conteúdo.')
    add_bullet(doc, 'O backend é a autoridade de acesso e conclusão.')
    add_bullet(doc, 'Tempo e visualização são evidências técnicas, não prova absoluta de atenção humana.')
    add_bullet(doc, 'O padrão enterprise é Linear + avaliação quando o curso for obrigatório.')
    add_bullet(doc, 'O reset de desenvolvimento pode recriar banco e dados de teste.')
    add_bullet(doc, 'Não serão preservadas soluções antigas que conflitem com o motor novo.')

    add_heading(doc, '19. Referências comparativas', 1)
    add_para(doc, 'A modelagem considera padrões documentados pelo LearnDash para progressão linear/livre, matrícula, pré-requisitos, timer, vídeo, materiais e certificados. A implementação será nativa do Talk e respeitará o isolamento multiempresa, em vez de copiar limitações de WordPress.')
    add_bullet(doc, 'LearnDash — Course Progression: https://learndash.com/support/kb/add-ons/courses/course-progression/')
    add_bullet(doc, 'LearnDash — Course Enrollment Mode: https://learndash.com/support/kb/core/courses/course-enrollment-mode/')
    add_bullet(doc, 'LearnDash — Lesson Display and Content Settings: https://learndash.com/support/kb/add-ons/lessons/lesson-display-content/')
    add_bullet(doc, 'LearnDash — Course Display and Content Settings: https://learndash.com/support/kb/add-ons/courses/course-display-content-settings/')

    add_callout(doc, 'Pronto para implementação', 'O próximo passo técnico é implementar a Fase 0: fechar os modelos, criar o motor de regras e atualizar o reset demo para gerar todos os cenários. Cada fase seguinte deverá ser validada pelos critérios de aceite deste documento antes de avançar.')

    doc.core_properties.title = 'Plano de Implementação — Cursos Enterprise e Motor de Progresso'
    doc.core_properties.subject = 'Especificação funcional e técnica do sistema de cursos'
    doc.core_properties.author = 'Talk'
    doc.core_properties.keywords = 'cursos, aprendizagem, progresso, enterprise, compliance, multiempresa'
    doc.save(OUT)
    print(OUT)


if __name__ == '__main__':
    build()
