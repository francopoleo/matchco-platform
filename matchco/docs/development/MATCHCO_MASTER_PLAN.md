# MatchCo — plano mestre consolidado

Este documento transforma o mapa documental em uma visão única de produto e
desenvolvimento. O contrato detalhado e os checkboxes de execução continuam em
[`MATCHCO_VALIDATION_PLAN.md`](MATCHCO_VALIDATION_PLAN.md); este arquivo organiza a decisão arquitetural e a ordem de implementação.

## Princípio do produto

O MatchCo é um SaaS multiempresa. A base é sempre:

```text
Organização
  └── Empresa / rede / parceiro
        └── Unidade ou loja
              └── Área operacional
                    └── Cargo e função
                          └── Pessoas, Memberships e audiências
```

Conteúdo, Talk, Treinamento, Certificação, Recrutamento Match, Operação e
Indicadores são serviços sobre essa estrutura. Nenhum serviço cria uma segunda
organização, empresa, unidade ou identidade de pessoa.

A organização define o padrão do pacote de serviços. Uma empresa pode receber
uma exceção explícita sem copiar usuários, conteúdos, Memberships ou audiências.

## Autonomia por interface e empresa

- **Console** é a administração: quem tem escopo organizacional governa o
  catálogo e pode selecionar uma empresa; quem tem Membership de empresa fica
  fixado nela. Publicações, cursos, documentos, mídia e trilhas podem ser da
  organização (compartilhados conforme audiência) ou de uma empresa específica.
- **Portal** é a operação das unidades autorizadas. Ele não cria um segundo
  cadastro de conteúdo nem substitui o Console como governança editorial.
- **App autenticado (`/app/`)** é o consumo de cursos, Feed, Wiki e documentos
  depois que a pessoa tem Membership/aprovação e atende à audiência. Conteúdo
  empresarial não se torna público por estar publicado; compartilhamento externo
  exige um link controlado, com escopo e validade próprios.

O escopo de empresa é aplicado no servidor, não apenas pelo menu ou filtro:
listas, detalhes, ações em lote, arquivos, eventos e sincronização móvel devem
respeitar organização + empresa + audiência. Um papel `staff` ou grupo editorial
isolado não concede acesso transversal a empresas; somente superadmin ou
Membership organizacional de proprietário/administrador pode atravessar empresas.

## Idiomas e localização

A interface usa Português do Brasil (`pt-br`) como idioma padrão, mesmo quando
o navegador prefere outra língua. A pessoa pode escolher `en` ou `es`; a escolha
 fica salva no cookie e é aplicada nas próximas páginas. A ativação do idioma já
está preparada, mas Inglês ainda não tem catálogo de produto completo e Espanhol
tem cobertura parcial. A escolha altera apenas as mensagens traduzidas nos
catálogos gettext. Ela não traduz conteúdo autoral (cursos, Feed, Wiki,
documentos, nomes de empresas ou textos de oportunidades) nem deve alterar
dados, permissões, tenant ou audiência. A interface de origem deve permanecer
em Português do Brasil e cada texto fixo precisa ser preparado para tradução;
idioma selecionável sem catálogo completo não representa tradução concluída.
Novos idiomas exigem catálogo, revisão humana, fallback explícito e verificação
das jornadas públicas e autenticadas.

Os literais fixos dos templates e contextos comuns de formulários, escolhas e
mensagens Python estão marcados para gettext. Os catálogos centrais `en`, `es`
e `pt_BR` foram extraídos em `matchco/locale/`. A tela Serviços da organização
está revisada nos três idiomas. O menu lateral (grupos, itens e atalhos) também
tem traduções preparadas em inglês e espanhol para validar a troca de idioma;
as demais telas permanecem em português e ainda exigem preenchimento e revisão
de `msgstr`. Em pt-BR, mensagens-base em português podem usar o próprio
texto de origem, mas textos-base ingleses visíveis precisam de tradução. HTML
montado dinamicamente em JavaScript e outros contextos também serão auditados
por jornada.

## Fases consolidadas

| Fase | Resultado | Situação |
|---|---|---|
| A | Catálogo de serviços e ativação por organização e empresa | Em execução |
| B | Núcleo organizacional: empresa, unidade, áreas, funções e Membership | Em execução |
| C | Local físico compartilhado e contexto isolado entre shopping e rede | Em execução |
| D | Convites, acessos, audiências, validade, aprovação e auditoria | Em execução |
| E | Serviços modulares sobre o núcleo, sem telas de serviço inativo | Em execução |
| F | Recrutamento sem CV para vagas de alto giro | Em execução |
| G | Conteúdo, treinamento, certificações, campanhas e operação | Próxima expansão |
| H | Observabilidade, segurança, LGPD e escala empresarial | Contínua |

## Cadastro canônico de unidade

Toda unidade ou loja, seja de rua ou dentro de shopping, usa `BusinessUnit`.
O cadastro contempla identidade, nome comercial, código, referência externa,
tipo da unidade, tipo de localização, canal, local físico, shopping,
endereço completo, CEP, coordenadas, responsável, contatos, website, horário,
CNPJ, inscrição estadual e status.

`PhysicalLocation` representa o local real e pode ser reutilizado por mais de
uma representação contextual. Assim, a Drogasil do Bourbon pode aparecer na
organização Bourbon Shopping e na organização Rede Drogasil. O local físico é
compartilhado; usuários, Memberships, conteúdos, audiências, serviços e
permissões não são.

## Recrutamento como extensão opcional

Quando Recrutamento está ativo, a unidade configura o cargo local e seu de-para
para funções canônicas. A necessidade declara os critérios; o motor filtra o
Perfil; convites são distribuídos em rodadas; a pessoa aceita ou recusa; a
unidade demonstra interesse; o Match libera o contato conforme autoridade.

Quando a organização usa somente Talk, Conteúdo ou Treinamento, telas, colunas,
QRs e menus de Recrutamento não devem aparecer.

Cada unidade possui um único QR Match ativo e reutilizável; ele registra a
origem, não a propriedade do Perfil. A prévia de elegibilidade e as rodadas de
convite consultam a mesma população, incluindo candidatos de outras
organizações somente quando a autorização para a organização da oportunidade
está ativa. Cada autorização é ligada ao QR de origem: loja exige a mesma
unidade física, shopping exige a localização canônica compartilhada, rede
exige a organização indicada ou vínculo de rede ativo, e raio exige coordenadas
geográficas e distância dentro do limite configurado. Sem consentimento
verificável ou geocodificação, a distribuição falha fechado.

O servidor aplica a ativação de serviços nas rotas operacionais mapeadas; o
menu não é a barreira de autorização. Membership, permissão por objeto,
consentimento e audiência continuam obrigatórios independentemente do pacote.

## Dados, privacidade e segurança

- dados fiscais e administrativos da unidade não são expostos ao candidato;
- CEP e coordenadas são usados apenas para territorialidade e proximidade
  controlada;
- toda consulta deve respeitar a organização selecionada e o Membership;
- local compartilhado não significa audiência compartilhada;
- convites, aprovações, consentimentos, contatos e alterações são auditáveis;
- o Perfil do candidato é único, mas seus contextos de entrada e autorizações
  permanecem separados.

## Critério para novas funcionalidades

Antes de criar uma entidade ou menu novo, verificar nesta ordem:

1. a necessidade já cabe em Organização, Empresa, Unidade, Área, Função,
   Membership, Audiência ou Serviço?
2. o serviço pode ser ativado sem duplicar a estrutura?
3. o dado tem finalidade, retenção, escopo e auditoria claros?
4. a tela aparece apenas para quem tem organização, serviço e permissão?
5. o Help, o contexto, os testes e o seed foram atualizados?

Se a resposta for não, a implementação deve parar no plano até o contrato ser
ajustado.

## Documentação obrigatória por mudança

Toda alteração atualiza, quando aplicável:

- o plano detalhado de execução;
- o HTML da Central em `matchco/docs/help/html/`;
- a matriz de URLs;
- o Help contextual em `matchco/console/contextual_docs.py`;
- testes, migrations e seeds;
- o Cartographer se a autoridade documental mudar.

## Validação mínima

```bash
./.venv312/bin/python matchco/manage.py check
./.venv312/bin/python matchco/manage.py makemigrations --check
./.venv312/bin/python matchco/manage.py test recruitment console --keepdb
```

O resultado da validação deve ser registrado no plano detalhado, não em um novo
documento paralelo.

Última revisão: 2026-10-09.
