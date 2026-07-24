**Talk - Cep Wagtail**

**Instruções para inicializar o ambiente em modo desenvolvimento**

O ambiente de desenvolvimento assim como de produção é baseado em um container. A diferença para produção é que o conteúdo dos módulos de código é mapeado como volume para dentro do container, efetivamente substituindo o conteúdo existente na imagem com o presente na pasta.

O repositório conta com um arquivo docker-compose.yml, que realiza o _build_ da imagem a partir do próprio diretório. O arquivo compose também conta com um container postgres, necessário para operação da aplicação.

**Passos para inicializar em desenvolvimento**

1. Após clonar este repositório, é necessário criar um arquivo de ambiente (_.env_) que será utilizado para o mapeamento das configurações do banco de dados, serviço de email e outras configurações. Na raiz deste repositório existe um arquivo de exemplo com todos os parametros, _.env.example_, utilize-o para compor seu arquivo.

2. Inicialize os containeres após com o comando _docker-compose up_ . O sistema deve ser incializado com um banco novo.

3. Após a inicialização é necessário aplicar as _migrations_ ao banco, e realizar a coleta dos arquivos estáticos. No repositório, na pasta talk há um arquivo _setup.sh_ que realiza as operações _makemigrations_, _migrate_, _import_ (para importar os parametros iniciais do sistema a partir do db.json) e _collectstatic_. Você pode executar pelo comando _docker exec talk-app setup.sh_ ou executar o shell do container com _docker exec -it talk-app /bin/bash_ e executar o setup com ./setup.sh.

4. O resultado deve ser a aplicação rodando local na porta 8000, caso não tenha sido alterado o padrão de porta do composte. O site pode ser acessado no http://localhost:8000
