# Relatório Final
## Mercado de Trabalho e Remessas da Diáspora em Cabo Verde (1980–2025)

Projeto de portfólio em análise de dados — Excel · SQL · Python 

---

## 1. Objetivo

Analisar a evolução do mercado de trabalho em Cabo Verde e a sua relação com as remessas da diáspora, respondendo a 5 perguntas de negócio definidas no início do projeto.

## 2. Fontes de dados

| Fonte | Indicadores | Período |
|---|---|---|
| World Bank Open Data (World Bank Combined Indicators for Cabo Verde) | Desemprego (`SL.UEM.TOTL.ZS`), Remessas % PIB (`BX.TRF.PWKR.DT.GD.ZS`), PIB per capita (`NY.GDP.PCAP.CD`), Inflação (`FP.CPI.TOTL.ZG`) | 1980–2025 |

O ficheiro original tinha 62.983 linhas (2758 indicadores, todos os países); depois de filtrar os 4 indicadores e remover duplicados (um erro do próprio ficheiro, não da recolha), ficaram **169 linhas tidy**.

## 3. Metodologia

| Fase | Ferramenta | O que foi feito |
|---|---|---|
| 1 | Excel (Power Query) | Filtragem dos 4 indicadores, remoção de duplicados, tabela tidy `Ano \| Indicador \| Valor`, Tabela Dinâmica e 2 gráficos |
| 2 | SQL (SQLite) | Schema normalizado (`indicadores` + `dados_anuais`), populado por `INSERT...SELECT` com `JOIN`; queries de evolução, variação homóloga (`LAG`) e comparação entre séries |
| 3 | Python (pandas, statsmodels, scikit-learn) | Análise exploratória, correlação entre indicadores, **backtest** de 2 modelos de previsão (treino até 2022, teste em 2023-2025) |
| 4 | Streamlit (Dashboard) | Dashboard de 3 páginas (Visão Geral, Evolução Temporal, Insights), medidas DAX de variação anual e média móvel |

## 4. Resultados principais

### 4.1 Evolução do desemprego (2000–2025)
O desemprego manteve-se estável à volta de **13%** durante toda a década de 2000. Em **2010** caiu de forma acentuada (10,67%), um efeito desfasado da crise financeira global de 2008-09. Desceu gradualmente até um mínimo pré-pandemia de **12,1%** em 2019, disparou para **14,65%** em 2020 (COVID-19), e recuperou desde então para **11,9%** em 2025 — o nível mais baixo da série, a par de 1994-1996.

![Taxa de Desemprego em Cabo Verde, 1991-2025, com anotações da crise de 2008 e da COVID-19 em 2020](Excel/Outputs/01_desemprego.png)

### 4.2 Relação entre remessas e desemprego
A correlação entre as duas séries é **positiva e fraca (+0,45)** — contraria a intuição de que mais remessas aliviam o desemprego local. As remessas parecem reagir sobretudo a choques económicos nos países de origem da diáspora (sobretudo Europa), não ao mercado de trabalho interno. A correlação entre desemprego e **PIB per capita** é mais forte e no sentido esperado: **-0,54**.

### 4.3 Disparidade por género e território
**Não respondido.** Esta pergunta exigia a desagregação do INE por sexo e meio (urbano/rural), que não chegou a ser recolhida durante o projeto. Fica registado como limitação, não como falha de análise — a recolha desses dados é o passo natural para uma segunda iteração deste projeto.

### 4.4 Tendência e estimativa para 2026-2028
Foram testados dois modelos: **Regressão Linear** e **ARIMA(1,1,1)**. Em vez de escolher pelo "nome", foi feito um **backtest**: treino com dados até 2022, previsão para 2023-2025 (anos já conhecidos), comparação com a realidade.

| Modelo | MAE | MAPE | Acurácia |
|---|---|---|---|
| Regressão Linear | **0,293** | 2,46% | 97,54% |
| ARIMA(1,1,1) | 0,620 | 5,21% | 94,79% |

A Regressão Linear teve menor erro — o ARIMA, ao dar mais peso ao choque recente de 2020-2022, sobrestimou a continuação da queda. Usando a Regressão Linear, a estimativa para 2026-2028 é de desemprego estável entre **11,9% e 12,1%**.

### 4.5 Recomendação
Como a relação remessas-desemprego é fraca e por vezes contraintuitiva, **as remessas não devem ser usadas como alavanca de política de emprego jovem**. O PIB per capita mostra uma correlação negativa mais forte e mais acionável — políticas de crescimento e investimento direto têm uma ligação mais clara com a redução do desemprego do que a dependência da diáspora.

## 5. Visualizações produzidas

- Gráfico de linha: desemprego 1991-2025 (Excel e Python)
- Gráfico de duplo eixo: desemprego vs. remessas 1980-2025 (Excel e Python)
- Gráfico de backtest: histórico + previsão ARIMA + previsão Regressão Linear, com linha de corte em 2022
- Dashboard Power BI: 3 páginas (Visão Geral, Evolução Temporal com slicer de anos, Insights)

## 6. Limitações

- Série curta (35-46 pontos anuais) — qualquer modelo de previsão tem margem de erro considerável.
- Correlação não implica causalidade; os números de 4.1-4.2 descrevem padrões, não mecanismos.
- O desemprego do World Bank é uma **estimativa modelada da OIT**, que pode divergir do valor oficial do INE para o mesmo ano.
- Sem a desagregação por género/território (objetivo 3), a análise fica limitada ao nível nacional agregado.

## 7. Conclusão

O projeto respondeu a 4 das 5 perguntas definidas no início, com evidência quantitativa para cada resposta (consultas SQL, testes de correlação em Python, backtest de modelos de previsão). O resultado mais relevante — e mais honesto — foi descobrir que o modelo mais "avançado" (ARIMA) não foi o mais preciso neste caso: a validação por backtest mostrou que a Regressão Linear simples teve menos de metade do erro do ARIMA para este conjunto de dados. Esta é, talvez, a conclusão mais importante do projeto a nível metodológico: **escolher o modelo pelo que se testa, não pelo que parece mais sofisticado**.

## 8. Como reproduzir este projeto

```
cabo-verde-mercado-trabalho/
├── README.md
├── dados/
│   ├── raw/indicators_cpv.csv
│   └── processed/cabo_verde_indicadores_limpo.csv
├── excel/cabo_verde_indicadores.xlsx
├── sql/schema.sql, queries.sql, cabo_verde.db
├── python/analise_exploratoria.ipynb
├── powerbi/dashboard.pbix, tema_cabo_verde.json
└── relatorio_final.md   ← este ficheiro
```

---
*Autor: [o teu nome] · [link LinkedIn] · [link GitHub]*