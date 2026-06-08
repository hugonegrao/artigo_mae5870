# Roteiro de Apresentacao - MAE5870

## Duracao sugerida

Roteiro pensado para uma apresentacao de 12 a 15 minutos.

Estrutura recomendada:

- 10 a 12 slides principais
- 1 slide reserva com diagnosticos dos residuos
- 1 slide reserva com detalhes dos modelos avaliados

---

## Slide 1 - Titulo

**Titulo sugerido**

Modelagem e Previsao da Carga Diaria de Energia do Sistema Interligado Nacional com Modelos ARIMA e Variaveis de Calendario

**O que mostrar**

- Titulo
- Disciplina: MAE5870 - Analise de Series Temporais
- Programa: IME-USP
- Base: ONS, carga diaria de energia, 2018-2025

**O que falar**

"Neste trabalho eu analiso a carga diaria de energia do Sistema Interligado Nacional brasileiro, usando dados do ONS entre 2018 e 2025. O objetivo e comparar modelos de series temporais para previsao de demanda, com enfase em modelos ARIMA e extensoes com variaveis exogenas de calendario."

**Mensagem-chave**

O problema e prever demanda diaria de energia com metodologia estatistica de series temporais.

---

## Slide 2 - Motivacao

**O que mostrar**

- Um esquema simples com tres pontos:
  - planejamento energetico
  - operacao do sistema
  - previsao de demanda

**O que falar**

"Prever carga eletrica e importante porque a energia precisa ser produzida e consumida praticamente em tempo real. Erros de previsao podem afetar a programacao da geracao, o despacho de recursos, o planejamento de manutencao e a seguranca operacional. Alem disso, a carga diaria tem componentes temporais claros: tendencia, sazonalidade anual, padrao semanal e efeitos de feriados."

**Mensagem-chave**

Previsao de carga nao e apenas exercicio estatistico; ela tem implicacao operacional direta.

---

## Slide 3 - Dados

**O que mostrar**

Tabela curta:

| Item | Valor |
|---|---:|
| Fonte | ONS |
| Periodo | 2018-01-01 a 2025-12-31 |
| Frequencia | diaria |
| Observacoes | 2.922 |
| Agregacao | soma dos subsistemas |
| Dados faltantes | 0 dias |

Arquivo de apoio:

`reports/tables/missing_values_summary.csv`

**O que falar**

"Os dados originais estavam separados por ano e por subsistema. O pipeline consolidou todos os arquivos, padronizou as colunas, identificou automaticamente data e carga, agregou os subsistemas por soma e criou uma serie diaria continua. Nao houve dias faltantes no periodo analisado."

**Mensagem-chave**

A base final e diaria, completa e cobre oito anos.

---

## Slide 4 - Serie temporal completa

**O que mostrar**

Figura:

`reports/figures/time_series.png`

**O que falar**

"Aqui vemos a serie completa. Existem tres caracteristicas importantes. Primeiro, ha uma tendencia geral de aumento ao longo do periodo, especialmente a partir de 2023. Segundo, ha sazonalidade anual, com periodos de maior carga no inicio do ano e recuperacao no fim do ano. Terceiro, ha uma oscilacao de alta frequencia, que esta relacionada ao ciclo semanal."

**Mensagem-chave**

A serie nao parece estacionaria em nivel e apresenta sazonalidades relevantes.

---

## Slide 5 - Sazonalidade semanal e mensal

**O que mostrar**

Figuras:

- `reports/figures/weekly_seasonality.png`
- `reports/figures/monthly_seasonality.png`

**O que falar**

"A sazonalidade semanal e muito forte. A carga media e mais alta nos dias uteis e cai bastante no sabado e principalmente no domingo. Isso justifica incluir variaveis de dia da semana e indicador de final de semana. Na sazonalidade mensal, ha carga mais alta no inicio do ano, queda entre maio e julho e recuperacao no fim do ano. Por isso tambem incluimos mes e termos harmonicos anuais."

**Mensagem-chave**

Calendario e parte essencial do processo gerador da carga.

---

## Slide 6 - Efeito de feriados

**O que mostrar**

Tabela baseada em:

`reports/tables/calendar_descriptive_statistics.csv`

Sugestao de tabela no slide:

| Feriado | Final de semana | Media MWmed |
|---|---|---:|
| Nao | Nao | 72.717,67 |
| Nao | Sim | 64.218,72 |
| Sim | Nao | 63.096,50 |
| Sim | Sim | 62.725,34 |

**O que falar**

"A diferenca entre dias uteis comuns e finais de semana e muito clara. Tambem vemos que feriados em dias uteis reduzem fortemente a carga media. Isso reforca a decisao de usar variaveis exogenas de calendario, especialmente feriado, vespera de feriado e pos-feriado."

**Mensagem-chave**

Feriados e finais de semana reduzem a carga de forma sistematica.

---

## Slide 7 - Estacionariedade

**O que mostrar**

Tabela baseada em:

`reports/tables/stationarity_test_results.csv`

Sugestao de tabela:

| Serie | ADF p-valor | KPSS p-valor | Conclusao |
|---|---:|---:|---|
| Original | 0,2337 | 0,0100 | nao estacionaria |
| Log | 0,2289 | 0,0100 | nao estacionaria |
| Primeira diferenca | 3,79e-21 | 0,1000 | estacionaria |
| Diferenca sazonal | 1,49e-24 | 0,1000 | estacionaria |

**O que falar**

"Usei dois testes complementares. O ADF tem como hipotese nula a existencia de raiz unitaria; o KPSS tem como hipotese nula a estacionariedade. Para a serie original, os dois testes apontam para nao estacionariedade. Depois da primeira diferenca, o ADF rejeita raiz unitaria e o KPSS nao rejeita estacionariedade. Isso justifica trabalhar com modelos integrados, com d igual a 1."

**Mensagem-chave**

A primeira diferenciacao e estatisticamente justificada.

---

## Slide 8 - Modelos avaliados

**O que mostrar**

Lista organizada:

- Naive
- Seasonal Naive, s = 7
- ARIMA
- ARIMAX
- SARIMA
- SARIMAX
- GARMA
- GARMAX

Depois destacar:

Modelo final: **ARIMAX(2,1,2)**

**O que falar**

"Foram comparados modelos de referencia, modelos ARIMA e SARIMA, e versoes com regressoras exogenas. A sazonalidade primaria considerada foi semanal, com periodo 7. Para os modelos com exogenas, usei variaveis de calendario conhecidas antecipadamente. A selecao nao foi feita apenas por AIC e BIC; a decisao final considerou desempenho no teste de 2025."

**Mensagem-chave**

A comparacao foi feita respeitando a ordem temporal e usando 2025 apenas como teste.

---

## Slide 9 - Selecao ARIMAX

**O que mostrar**

Tabela curta baseada em:

`reports/tables/arimax_candidate_results.csv`

| Modelo | AIC | BIC |
|---|---:|---:|
| ARIMAX(2,1,2) | 44.315,69 | 44.537,80 |
| ARIMAX(1,1,2) | 44.322,79 | 44.539,05 |
| ARIMAX(2,1,1) | 44.374,70 | 44.590,98 |

**O que falar**

"Entre os candidatos ARIMAX, o melhor por AIC foi o ARIMAX(2,1,2). A diferenca para o segundo colocado e pequena, mas o modelo selecionado manteve o melhor equilibrio dentro dessa classe. A escolha final, no entanto, vem da avaliacao fora da amostra, nao apenas do AIC."

**Mensagem-chave**

O ARIMAX(2,1,2) foi selecionado entre os candidatos ARIMAX e depois validado no teste.

---

## Slide 10 - Comparacao de desempenho

**O que mostrar**

Tabela baseada em:

`reports/tables/forecast_accuracy_table.csv`

| Modelo | RMSE | MAPE |
|---|---:|---:|
| ARIMAX | 3.788,66 | 3,41% |
| GARMAX | 4.081,56 | 4,17% |
| ARIMA | 7.152,51 | 7,11% |
| SARIMA | 7.898,50 | 7,71% |
| Seasonal Naive | 9.910,79 | 9,44% |
| Naive | 10.456,25 | 10,70% |
| SARIMAX | 16.558,52 | 19,50% |

**O que falar**

"O ARIMAX foi o melhor modelo em todas as metricas principais: MAE, RMSE e MAPE. O ganho em relacao ao ARIMA mostra a importancia das variaveis de calendario. O ganho em relacao ao naive e ao seasonal naive mostra que o modelo realmente agrega capacidade preditiva. Um resultado interessante e que o SARIMAX teve AIC menor dentro da amostra, mas desempenho muito pior no teste. Isso mostra por que nao devemos escolher modelo apenas por criterio de informacao."

**Mensagem-chave**

O melhor modelo preditivo foi o ARIMAX, nao o SARIMAX com menor AIC.

---

## Slide 11 - Previsao ARIMAX em 2025

**O que mostrar**

Figuras:

- `reports/figures/forecast_comparison_best_arimax_full.png`
- `reports/figures/forecast_comparison_best_arimax_zoom.png`

Sugestao:

Use a figura full primeiro, depois a zoom.

**O que falar**

"Na figura completa, a serie observada aparece desde 2018 e o forecast aparece apenas em 2025. No zoom de 2025, vemos que o ARIMAX captura bem o ciclo semanal e acompanha a trajetoria geral da carga. Ele subestima alguns picos no inicio do ano, o que indica uma limitacao do modelo para capturar eventos extremos ou variacoes de nivel nao explicadas apenas por calendario."

**Mensagem-chave**

O ARIMAX acerta bem o padrao geral e semanal, mas ainda tem dificuldade em picos.

---

## Slide 12 - Interpretacao das variaveis exogenas

**O que mostrar**

Tabela baseada em:

`reports/tables/arimax_coefficients.csv`

| Variavel | Estimativa | Interpretacao |
|---|---:|---|
| is_holiday | -7.604,15 | queda em feriados |
| is_weekend | -4.584,75 | queda em finais de semana |
| is_holiday_eve | -1.718,01 | queda em vespera de feriado |
| is_post_holiday | -1.688,89 | queda no dia posterior |
| annual_cos_1 | 3.687,76 | componente sazonal anual |

**O que falar**

"Os coeficientes confirmam a intuicao da analise exploratoria. Feriados e finais de semana reduzem fortemente a carga. A vespera e o dia posterior ao feriado tambem sao relevantes. Isso mostra que a demanda eletrica nao depende apenas da sua propria historia, mas tambem do calendario civil e do comportamento economico associado a ele."

**Mensagem-chave**

As variaveis de calendario sao estatisticamente relevantes e interpretaveis.

---

## Slide 13 - Diagnostico dos residuos

**O que mostrar**

Figura:

`reports/figures/best_arimax_residual_diagnostics.png`

Tabela baseada em:

`reports/tables/best_arimax_ljung_box.csv`

| Lag | p-valor |
|---:|---:|
| 7 | 6,38e-10 |
| 14 | 1,22e-07 |
| 21 | 2,65e-06 |
| 28 | 5,28e-05 |

**O que falar**

"Apesar do bom desempenho preditivo, o teste de Ljung-Box rejeita a hipotese de residuos nao autocorrelacionados. Ou seja, ainda existe estrutura temporal nao capturada. Isso e uma limitacao importante. O modelo e o melhor em previsao fora da amostra, mas nao e perfeito do ponto de vista diagnostico."

**Mensagem-chave**

O ARIMAX e o melhor preditor, mas os residuos indicam espaco para extensoes futuras.

---

## Slide 14 - Discussao e limitacoes

**O que mostrar**

Lista com 4 pontos:

- calendario melhora previsao
- AIC/BIC nao bastam
- residuos ainda autocorrelacionados
- faltam variaveis meteorologicas

**O que falar**

"O principal resultado e que variaveis de calendario melhoram muito a previsao. Ao mesmo tempo, o trabalho mostra um ponto metodologico importante: menor AIC nao garantiu melhor previsao. A maior limitacao e que nao incluimos variaveis meteorologicas, que provavelmente explicariam parte dos picos de carga. Outra limitacao e usar a serie agregada nacional, sem explorar diferencas regionais."

**Mensagem-chave**

O estudo e estatisticamente consistente, mas pode ser expandido com clima, subsistemas e validacao temporal mais ampla.

---

## Slide 15 - Conclusao

**O que mostrar**

Tres conclusoes:

1. A serie e nao estacionaria em nivel e tem sazonalidade semanal/anual.
2. Variaveis de calendario sao fundamentais.
3. ARIMAX(2,1,2) foi o melhor modelo preditivo.

**O que falar**

"Concluindo, a carga diaria de energia do SIN apresenta tendencia, sazonalidade e forte efeito de calendario. A primeira diferenciacao foi necessaria para estacionarizar a serie. Entre os modelos avaliados, o ARIMAX(2,1,2) com variaveis de calendario foi o melhor no teste de 2025, com MAPE de 3,41%. O modelo e interpretavel e util para previsao, embora os residuos indiquem que ainda ha estrutura temporal a ser explorada."

**Mensagem-chave**

O ARIMAX e a melhor escolha para o artigo porque combina precisao, interpretabilidade e fundamentacao estatistica.

---

# Perguntas que podem aparecer

## Por que usar ARIMAX e nao SARIMAX?

Resposta sugerida:

"O SARIMAX teve AIC menor dentro da amostra, mas desempenho muito pior no teste de 2025. Como o objetivo e previsao, a escolha final considerou a acuracia fora da amostra. O ARIMAX apresentou menor RMSE, menor MAE e menor MAPE."

## O forecast usa dados de 2025?

Resposta sugerida:

"Nao para estimacao. O modelo foi treinado ate 2024-12-31. O ano de 2025 foi usado apenas para avaliar a previsao. As variaveis exogenas de 2025 sao de calendario, entao sao conhecidas antecipadamente e nao representam vazamento."

## Por que os residuos ainda tem autocorrelacao?

Resposta sugerida:

"Isso indica que o modelo ainda nao capturou toda a dependencia temporal. Mesmo assim, ele foi o melhor em previsao fora da amostra. Para trabalhos futuros, eu incluiria clima, modelos com multiplas sazonalidades e validacao com multiplas origens."

## Por que nao usar modelos de machine learning?

Resposta sugerida:

"Poderia ser uma extensao. Mas a proposta da disciplina era enfatizar metodologia de series temporais, incluindo estacionariedade, identificacao, estimacao, diagnostico e comparacao de modelos. O ARIMAX tem a vantagem de ser interpretavel."

## O que significa MAPE de 3,41%?

Resposta sugerida:

"Significa que, em media, o erro absoluto da previsao correspondeu a cerca de 3,41% da carga observada no periodo de teste. Para uma serie diaria agregada nacional, e um resultado bastante competitivo entre os modelos avaliados."

---

# Ordem dos arquivos a abrir durante a apresentacao

1. `reports/figures/time_series.png`
2. `reports/figures/weekly_seasonality.png`
3. `reports/figures/monthly_seasonality.png`
4. `reports/tables/stationarity_test_results.csv`
5. `reports/tables/forecast_accuracy_table.csv`
6. `reports/figures/forecast_comparison_best_arimax_full.png`
7. `reports/figures/forecast_comparison_best_arimax_zoom.png`
8. `reports/tables/arimax_coefficients.csv`
9. `reports/figures/best_arimax_residual_diagnostics.png`
10. `reports/tables/best_arimax_ljung_box.csv`

---

# Fechamento em uma frase

"O resultado central do trabalho e que a modelagem ARIMAX com variaveis de calendario melhora substancialmente a previsao da carga diaria de energia, superando os modelos de referencia e mantendo uma interpretacao estatistica clara dos efeitos de finais de semana e feriados."
