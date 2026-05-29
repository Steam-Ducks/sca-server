"""
Script para gerar a documentação em PDF da implementação dos
Indicadores de Orçamento e Saúde Financeira (SCA-317).
"""

from fpdf import FPDF
from fpdf.enums import XPos, YPos

FONT_PATH = "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"
FONT_B_PATH = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
FONT_I_PATH = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Oblique.ttf"
FONT_BI_PATH = "/usr/share/fonts/truetype/dejavu/DejaVuSans-BoldOblique.ttf"
MONO_PATH = "/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf"
MONO_B_PATH = "/usr/share/fonts/truetype/dejavu/DejaVuSansMono-Bold.ttf"


class PDF(FPDF):
    def header(self):
        self.set_font("DejaVu", "B", 9)
        self.set_text_color(100, 100, 100)
        self.cell(0, 8, "SCA · Indicadores de Orçamento e Saúde Financeira", align="L")
        self.ln(4)
        self.set_draw_color(200, 200, 200)
        self.line(10, self.get_y(), 200, self.get_y())
        self.ln(5)

    def footer(self):
        self.set_y(-15)
        self.set_font("DejaVu", "I", 8)
        self.set_text_color(150, 150, 150)
        self.cell(0, 10, f"Página {self.page_no()}", align="C")

    def section_title(self, title):
        self.set_font("DejaVu", "B", 13)
        self.set_text_color(30, 60, 120)
        self.ln(5)
        self.cell(0, 8, title, new_x=XPos.LMARGIN, new_y=YPos.NEXT)
        self.set_draw_color(30, 60, 120)
        self.line(10, self.get_y(), 200, self.get_y())
        self.ln(4)
        self.set_text_color(40, 40, 40)

    def subsection_title(self, title):
        self.set_font("DejaVu", "B", 11)
        self.set_text_color(50, 50, 50)
        self.ln(3)
        self.cell(0, 7, title, new_x=XPos.LMARGIN, new_y=YPos.NEXT)
        self.set_font("DejaVu", "", 10)
        self.set_text_color(40, 40, 40)

    def body_text(self, text):
        self.set_font("DejaVu", "", 10)
        self.set_text_color(40, 40, 40)
        self.multi_cell(0, 6, text)
        self.ln(2)

    def bullet(self, items):
        self.set_font("DejaVu", "", 10)
        self.set_text_color(40, 40, 40)
        for item in items:
            self.multi_cell(180, 6, f"  •  {item}")
        self.ln(2)

    def code_block(self, lines):
        self.set_fill_color(245, 245, 245)
        self.set_draw_color(210, 210, 210)
        self.set_font("Mono", "", 8)
        self.set_text_color(30, 30, 30)
        self.ln(2)
        for line in lines:
            self.cell(0, 5, line, fill=True, new_x=XPos.LMARGIN, new_y=YPos.NEXT)
        self.set_font("DejaVu", "", 10)
        self.set_text_color(40, 40, 40)
        self.ln(3)

    def table_row(self, cols, widths, header=False):
        if header:
            self.set_fill_color(30, 60, 120)
            self.set_text_color(255, 255, 255)
            self.set_font("DejaVu", "B", 9)
        else:
            self.set_fill_color(250, 250, 250)
            self.set_text_color(40, 40, 40)
            self.set_font("DejaVu", "", 9)
        self.set_draw_color(200, 200, 200)
        for col, w in zip(cols, widths):
            self.cell(w, 7, col, border=1, fill=True)
        self.ln()
        self.set_text_color(40, 40, 40)


def build_pdf(output_path: str):
    pdf = PDF()
    pdf.add_font("DejaVu", "", FONT_PATH)
    pdf.add_font("DejaVu", "B", FONT_B_PATH)
    pdf.add_font("DejaVu", "I", FONT_I_PATH)
    pdf.add_font("DejaVu", "BI", FONT_BI_PATH)
    pdf.add_font("Mono", "", MONO_PATH)
    pdf.add_font("Mono", "B", MONO_B_PATH)
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.add_page()

    # ── Capa ────────────────────────────────────────────────────────────────
    pdf.set_font("DejaVu", "B", 20)
    pdf.set_text_color(30, 60, 120)
    pdf.ln(10)
    pdf.cell(
        0,
        12,
        "Indicadores de Orçamento e",
        align="C",
        new_x=XPos.LMARGIN,
        new_y=YPos.NEXT,
    )
    pdf.cell(0, 12, "Saúde Financeira", align="C", new_x=XPos.LMARGIN, new_y=YPos.NEXT)
    pdf.set_font("DejaVu", "", 12)
    pdf.set_text_color(80, 80, 80)
    pdf.cell(
        0,
        8,
        "SCA-317 · Documentação Técnica de Implementação",
        align="C",
        new_x=XPos.LMARGIN,
        new_y=YPos.NEXT,
    )
    pdf.ln(4)
    pdf.set_font("DejaVu", "I", 10)
    pdf.cell(
        0,
        6,
        "Projeto SCA — Supply Chain Analytics",
        align="C",
        new_x=XPos.LMARGIN,
        new_y=YPos.NEXT,
    )
    pdf.set_draw_color(30, 60, 120)
    pdf.ln(4)
    pdf.line(40, pdf.get_y(), 170, pdf.get_y())
    pdf.ln(14)

    # ── 1. Contexto ─────────────────────────────────────────────────────────
    pdf.section_title("1. Contexto e Motivação")
    pdf.body_text(
        "Como gerente, é necessário visualizar rapidamente os principais indicadores "
        "de orçamento e saúde financeira dos projetos dentro do contexto selecionado. "
        "Anteriormente, os cartões de KPIs da tela Orçamento e Saúde Financeira eram "
        "calculados inteiramente no navegador (client-side), exigindo que todos os "
        "registros de projetos fossem transferidos antes de qualquer valor ser exibido."
    )
    pdf.body_text(
        "Esta implementação criou um endpoint dedicado no backend que realiza a "
        "agregação server-side, retornando apenas os sete indicadores consolidados. "
        "Isso reduz o tempo até o primeiro dado visível e garante que os filtros "
        "sejam aplicados de forma consistente pelo servidor."
    )

    # ── 2. Escopo ────────────────────────────────────────────────────────────
    pdf.section_title("2. Escopo da Implementação")
    pdf.body_text("Foram realizadas mudanças nos dois repositórios do projeto:")

    pdf.subsection_title("2.1  Backend — sca-server")
    pdf.bullet(
        [
            "Novo selector get_budget_indicators(params) — caminho silver (live queries)",
            "Novo selector get_budget_indicators_gold(params) — caminho gold (tabela pré-computada)",
            "Novo serializer BudgetIndicatorsSerializer",
            "Nova view BudgetIndicatorsView (GET /api/budget/indicators/)",
            "Registro da nova rota em budget/urls.py",
            "21 testes unitários distribuídos em 3 novos arquivos de teste",
        ]
    )

    pdf.subsection_title("2.2  Frontend — sca-client")
    pdf.bullet(
        [
            "Novos tipos BudgetIndicators e BudgetIndicatorsSnapshot em src/types/api.ts",
            "Método fetchBudgetIndicators() em src/services/budgetService.ts",
            "Atualização de OrcamentoSaudeFinanceira.vue para consumir o novo endpoint",
            "Indicadores carregados em paralelo com a lista de projetos (Promise.all)",
            "Filtro 'saude' passa a disparar recarga de indicadores no servidor",
        ]
    )

    # ── 3. Indicadores retornados ────────────────────────────────────────────
    pdf.section_title("3. Indicadores Retornados pelo Endpoint")
    pdf.body_text(
        "O endpoint GET /api/budget/indicators/ retorna o seguinte envelope JSON:"
    )
    pdf.code_block(
        [
            "{",
            '  "data": {',
            '    "budgetTotal":        <float>  -- soma do budget estimado de todos os projetos,',
            '    "custoRealTotal":     <float>  -- soma do custo real (materiais + horas),',
            '    "desvioPercentMedio": <float>  -- media aritmetica do desvio % por projeto,',
            '    "projetosSaudaveis":  <int>    -- contagem de projetos classificados Saudavel,',
            '    "projetosAtencao":    <int>    -- contagem de projetos classificados Atencao,',
            '    "projetosCriticos":   <int>    -- contagem de projetos classificados Critico',
            "  },",
            '  "last_updated_at": "<ISO 8601>" | null',
            "}",
        ]
    )
    pdf.body_text(
        "Todos os sete critérios de aceitação da história de usuário são cobertos "
        "por campos deste envelope."
    )

    # ── 4. Regras de cálculo ─────────────────────────────────────────────────
    pdf.section_title("4. Regras de Cálculo dos Indicadores")

    pdf.subsection_title("4.1  Budget Total")
    pdf.body_text(
        "Soma dos campos budget de cada projeto. O budget de um projeto é a soma de "
        "(estimativa_horas × custo_hora) de todas as tarefas mais "
        "(quantidade × custo_estimado) de todas as solicitações de compra."
    )

    pdf.subsection_title("4.2  Custo Real Total")
    pdf.body_text(
        "Soma dos custos reais de todos os projetos. O custo real de um projeto é "
        "a soma do valor_alocado das compras-projeto mais "
        "(horas_trabalhadas × custo_hora) dos registros de tempo das tarefas."
    )

    pdf.subsection_title("4.3  Desvio % Médio")
    pdf.body_text(
        "Média aritmética dos desvios percentuais individuais de cada projeto, "
        "calculados como: (custo_real / budget) × 100. "
        "Quando budget = 0, o desvio do projeto é considerado 0%."
    )

    pdf.subsection_title("4.4  Classificação de Saúde Financeira")
    pdf.body_text("Regra de classificação por desvio percentual:")
    headers = ["Faixa de Desvio", "Classificação"]
    widths = [80, 80]
    pdf.table_row(headers, widths, header=True)
    pdf.table_row(["< 70%", "Saudável"], widths)
    pdf.table_row([">= 70% e < 90%", "Atenção"], widths)
    pdf.table_row([">= 90%", "Crítico"], widths)
    pdf.ln(4)
    pdf.body_text(
        "Os contadores projetosSaudaveis, projetosAtencao e projetosCriticos "
        "refletem a distribuição dos projetos filtrados nessas três categorias."
    )

    pdf.subsection_title("4.5  Última Atualização")
    pdf.body_text(
        "No caminho gold: max(gold_updated_at) da tabela gold.budget_snapshot. "
        "No caminho silver: max de todos os silver_ingested_at das tabelas relacionadas "
        "(projetos, programas, tarefas, tempos, solicitações, compras, pedidos)."
    )

    # ── 5. Arquitetura ───────────────────────────────────────────────────────
    pdf.add_page()
    pdf.section_title("5. Arquitetura — Fluxo de Dados")

    pdf.body_text(
        "O sistema mantém dois caminhos de leitura, seguindo o padrão já estabelecido "
        "no módulo de orçamento:"
    )
    pdf.bullet(
        [
            "Caminho Gold (prioritário): lê da tabela pré-computada "
            'gold."budget_snapshot" com agregações via SQL (Sum, Avg, Count). '
            "Mais rápido e recomendado para ambientes com carga de dados regular.",
            "Caminho Silver (fallback): executa as queries live sobre as tabelas silver "
            "chamando internamente get_budget_snapshot() e computando as agregações "
            "em Python. Utilizado quando a tabela gold está vazia.",
        ]
    )

    pdf.body_text(
        "O critério de seleção do caminho é idêntico ao de BudgetSnapshotView: "
        "se get_budget_indicators_gold() retornar None (gold vazio), o sistema "
        "recorre ao caminho silver automaticamente."
    )

    pdf.subsection_title("Diagrama simplificado")
    pdf.code_block(
        [
            "GET /api/budget/indicators/?<filtros>",
            "         |",
            "         v",
            "  BudgetIndicatorsView.get()",
            "         |",
            "         +---> get_budget_indicators_gold(params)",
            "         |           |",
            "         |       gold existe? --sim--> agrega SQL (Sum/Avg/Count)",
            "         |           |",
            "         |         nao",
            "         |           |",
            "         +---> get_budget_indicators(params)",
            "                     |",
            "               get_budget_snapshot(params)  [silver live]",
            "                     |",
            "               reduz rows em Python",
            "         |",
            "         v",
            "  BudgetIndicatorsSerializer  (snake_case -> camelCase)",
            "         |",
            "         v",
            '  { "data": {...}, "last_updated_at": "..." }',
        ]
    )

    # ── 6. Filtros aceitos ───────────────────────────────────────────────────
    pdf.section_title("6. Filtros Aceitos")
    pdf.body_text(
        "O endpoint aceita os mesmos query params que o endpoint existente "
        "GET /api/budget/:"
    )
    headers = ["Parâmetro", "Tipo", "Descrição"]
    widths = [40, 25, 115]
    pdf.table_row(headers, widths, header=True)
    rows = [
        ("periodo", "string", "Filtra por mês de início no formato YYYY-MM"),
        ("programa", "string", "Filtra por nome do programa (case-insensitive)"),
        ("projeto", "string", "Filtra por nome do projeto (case-insensitive)"),
        ("saude", "string", "Filtra por classificação: Saudável, Atenção ou Crítico"),
    ]
    for r in rows:
        pdf.table_row(list(r), widths)
    pdf.ln(4)

    # ── 7. Arquivos modificados ──────────────────────────────────────────────
    pdf.section_title("7. Arquivos Criados / Modificados")

    pdf.subsection_title("Backend — sca-server")
    headers = ["Arquivo", "Tipo", "O que mudou"]
    widths = [85, 15, 80]
    pdf.table_row(headers, widths, header=True)
    bfiles = [
        (
            "budget/selectors.py",
            "MOD",
            "Adicionou get_budget_indicators e get_budget_indicators_gold",
        ),
        ("budget/serializers.py", "MOD", "Adicionou BudgetIndicatorsSerializer"),
        ("budget/views.py", "MOD", "Adicionou BudgetIndicatorsView"),
        ("budget/urls.py", "MOD", "Registrou rota budget/indicators/"),
        ("budget/tests/test_urls.py", "MOD", "Adicionou teste da nova rota"),
        ("budget/tests/test_indicators_view.py", "NEW", "12 testes de view/integração"),
        ("budget/tests/test_indicators_selectors.py", "NEW", "8 testes de seletores"),
        (
            "budget/tests/test_indicators_serializers.py",
            "NEW",
            "4 testes de serializer",
        ),
    ]
    for r in bfiles:
        pdf.table_row(list(r), widths)
    pdf.ln(4)

    pdf.subsection_title("Frontend — sca-client")
    headers = ["Arquivo", "Tipo", "O que mudou"]
    widths = [85, 15, 80]
    pdf.table_row(headers, widths, header=True)
    ffiles = [
        (
            "src/types/api.ts",
            "MOD",
            "Adicionou BudgetIndicators e BudgetIndicatorsSnapshot",
        ),
        ("src/services/budgetService.ts", "MOD", "Adicionou fetchBudgetIndicators()"),
        (
            "src/views/OrcamentoSaudeFinanceira.vue",
            "MOD",
            "KPIs via endpoint; saude recarrega indicadores",
        ),
    ]
    for r in ffiles:
        pdf.table_row(list(r), widths)
    pdf.ln(4)

    # ── 8. Testes ────────────────────────────────────────────────────────────
    pdf.section_title("8. Cobertura de Testes")
    pdf.body_text(
        "21 novos testes unitários foram escritos para o backend. "
        "Todos os 41 testes do módulo budget (incluindo os existentes) passam."
    )

    pdf.subsection_title("test_indicators_view.py  (12 testes)")
    pdf.bullet(
        [
            "CT-V01: retorna HTTP 200 com dados gold",
            "CT-V02: retorna HTTP 200 com fallback silver",
            "CT-V03: resposta gold contém todos os campos com valores corretos",
            "CT-V04: resposta silver fallback contém todos os campos com valores corretos",
            "CT-V05: last_updated_at é null quando não há dados",
            "CT-V06: gold tem prioridade sobre silver",
            "CT-V07: cai no silver quando gold retorna None",
            "CT-V08 a CT-V12: query params repassados corretamente aos seletores",
        ]
    )

    pdf.subsection_title("test_indicators_selectors.py  (8 testes)")
    pdf.bullet(
        [
            "CT-S01: retorna zeros quando não há projetos",
            "CT-S02: soma correta de budget e custo_real",
            "CT-S03: contagem correta por saúde (Saudável/Atenção/Crítico)",
            "CT-S04: cálculo correto do desvio % médio",
            "CT-S05: params repassados ao get_budget_snapshot",
            "CT-S06: gold retorna None quando tabela vazia",
            "CT-S07: gold retorna agregados quando há dados",
            "CT-S08: filtros aplicados antes do aggregate no caminho gold",
        ]
    )

    pdf.subsection_title("test_indicators_serializers.py  (4 testes)")
    pdf.bullet(
        [
            "CT-SR01: campos snake_case mapeados para camelCase",
            "CT-SR02: valores corretos na serialização padrão",
            "CT-SR03: valores zero serializados corretamente",
            "CT-SR04: precisão de float preservada",
        ]
    )

    # ── 9. Rastreabilidade ───────────────────────────────────────────────────
    pdf.section_title("9. Rastreabilidade com Critérios de Aceitação")
    headers = ["Critério da Estória", "Campo no Endpoint", "Teste(s)"]
    widths = [80, 55, 45]
    pdf.table_row(headers, widths, header=True)
    mapping = [
        ("Exibir orçamento total", "budgetTotal", "CT-V03, CT-S02"),
        ("Exibir custo real total", "custoRealTotal", "CT-V03, CT-S02"),
        ("Exibir variação % média", "desvioPercentMedio", "CT-V03, CT-S04"),
        ("Exibir projetos Saudáveis", "projetosSaudaveis", "CT-V03, CT-S03"),
        ("Exibir projetos Atenção", "projetosAtencao", "CT-V04, CT-S03"),
        ("Exibir projetos Críticos", "projetosCriticos", "CT-V04, CT-S03"),
        ("Exibir última atualização", "last_updated_at", "CT-V03, CT-V05"),
        ("Respeitar filtros aplicados", "query params aceitos", "CT-V08 a CT-V12"),
        ("Estado sem dados", "zeros + null", "CT-V05, CT-S01"),
    ]
    for r in mapping:
        pdf.table_row(list(r), widths)
    pdf.ln(4)

    # ── 10. Decisões Técnicas ────────────────────────────────────────────────
    pdf.section_title("10. Decisões Técnicas Relevantes")

    pdf.subsection_title("10.1  Por que um endpoint separado?")
    pdf.body_text(
        "O endpoint GET /api/budget/ retorna uma linha por projeto com todos os "
        "campos detalhados. Para exibir apenas os sete KPIs de topo de página, "
        "transferir todas as linhas é desnecessário. O novo endpoint retorna "
        "somente os agregados, reduzindo o payload e o tempo de renderização dos "
        "cartões de indicadores."
    )

    pdf.subsection_title("10.2  Média aritmética vs. desvio consolidado")
    pdf.body_text(
        "O desvio percentual exibido é a média aritmética dos desvios individuais "
        "(consistente com o comportamento anterior do frontend). Uma alternativa "
        "seria (custo_real_total / budget_total - 1) × 100, que daria mais peso "
        "a projetos maiores. A média aritmética foi mantida para não alterar o "
        "comportamento visível ao usuário."
    )

    pdf.subsection_title("10.3  Carregamento paralelo no frontend")
    pdf.body_text(
        "O Vue chama fetchBudgetIndicators() e fetchBudgetSnapshot() em paralelo "
        "via Promise.all(). Os cartões de KPIs aparecem assim que o endpoint de "
        "indicadores responde, independentemente do tempo de carga da tabela completa."
    )

    pdf.subsection_title("10.4  Filtro 'saude' agora recarrega indicadores")
    pdf.body_text(
        "Anteriormente o filtro por saúde era aplicado apenas client-side em "
        "filteredData. Com o novo endpoint, o filtro saude é enviado ao backend e "
        "os indicadores refletem exatamente o subconjunto selecionado. A tabela e "
        "os gráficos continuam com filtragem client-side para o filtro de saúde, "
        "pois o endpoint /budget/ silver não aplica esse filtro server-side."
    )

    # ── 11. Como executar ────────────────────────────────────────────────────
    pdf.section_title("11. Como Executar os Testes")
    pdf.code_block(
        [
            "# A partir da raiz do repositório sca-server:",
            "pytest budget/tests/ -v",
            "",
            "# Resultado esperado:",
            "41 passed in < 1s",
        ]
    )

    pdf.output(output_path)
    print(f"PDF gerado: {output_path}")


if __name__ == "__main__":
    build_pdf("/home/ahlesk/sca-server/docs_indicadores_orcamento_saude.pdf")
