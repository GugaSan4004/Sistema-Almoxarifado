# Almox-System

Aplicação web para controle de almoxarifado com **gerenciamento de correspondências** e **empréstimo de ferramentas**.

## 🧩 Visão Geral
O Almox-System permite:
- Registrar e gerenciar correspondências com código de rastreio (Correios).
- Controlar status de correspondências (recebido, almox, devolução, etc.).
- Extrair texto de comprovantes via OCR (Azure Vision).
- Registrar saídas (comprovantes) e armazenar fotos.
- Gerenciar empréstimo de ferramentas com check-out/check-in e histórico.

## 🚀 Tecnologias Usadas
- **Backend**: Python + Flask
- **Banco**: SQLite
- **Real-time**: Flask-SocketIO + Eventlet
- **OCR**: Azure Vision (cliente `azure-ai-vision-imageanalysis` + `azure-ai-textanalytics`)
- **Frontend**: HTML + CSS + JavaScript
- **Outras libs**: `rapidfuzz`, `pdf2image`, `Pillow`, `psutil`, `pyautogui` etc.

## 🧰 Requisitos e Configuração
### 1) Dependências
```bash
python -m pip install -r requirements.txt
```

### 2) Variáveis de ambiente (para OCR)
O OCR usa o Azure Vision; configure estas variáveis:
- `VISION_ENDPOINT`: Endpoint para o ComputerVision
- `TEXT_ENDPOINT`: Endpoin para o TextAnalytics
- `VISION_KEY`: Key privada para o ComputerVision
- `TEXT_KEY`: Key privada para o TextAnalytics

### 3) Banco de dados
O arquivo `db.sqlite` já é utilizado por padrão e fica na raiz do projeto.
Caso deseja alterar o local do mesmo, mude o arquivo sqlite_code.py para aceitar as alterções

## ▶️ Como Rodar
```bash
python server.py
```
O servidor roda em `http://localhost` (porta 80).

## 🧭 Navegação / Funcionalidades Principais
### Correspondências (mails)
- Busca por código (ex: `AA123456789BR`) e atualização do status.
- Cadastro de novos itens.
- Registro de saída (com comprovante/image) via botão “Registrar Saída”.
- Captura de imagem + OCR para preencher código automaticamente (função `extract-image`).

## 🗂 Estrutura do Projeto
- `server.py` — app Flask principal (rotas, autorização, lógica).
- `templates/` — templates Jinja2 (ui das abas, formulários).
- `static/js/` — frontend JS (ajax, navegação entre abas).
- `static/css/` — estilos.
- `static/py/` — módulos Python compartilhados (DB, OCR, etc.).
- `pictures/` — imagens capturadas/armazenadas.
- `requirements.txt` — dependências Python.

## 📝 Notas Adicionais
- O servidor adiciona automaticamente módulos ausentes do `requirements.txt` na inicialização (se o ambiente permitir).
- O fluxo de “listar / buscar” usa rota `/api/render-body/<tab_id>` e atualiza a aba via AJAX.

## 📄 Licença
Licenciado sob [MIT](LICENSE).

## 📬 Contato
Para dúvidas ou melhorias, abra uma issue ou entre em contato com o autor do projeto.
