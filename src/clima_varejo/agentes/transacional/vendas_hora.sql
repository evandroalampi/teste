-- Agregação de movimentos (lakehouse, Hudi) para contrato.vendas_hora. Seção 17.
-- Filtrar por idvarejista e anomesconsumo lê só as partições do piloto.
-- Pendente: confirmar que dataconsumo está em hora local (amostra real da Rede TOP).
SELECT
    m.idvarejista,
    m.idloja,
    date_trunc('hour', m.dataconsumo)                              AS data_hora_local,
    m.idproduto,
    sum(m.quantidade)                                             AS quantidade,
    sum(m.valortotal)                                             AS valor_bruto,
    sum(coalesce(m.valordescontoitem, 0))                         AS valor_desconto,
    count(DISTINCT concat(m.numerocupom, '|', m.identificacaopdv)) AS n_cupons
FROM movimentos m
WHERE m.idvarejista IN (%(varejistas)s)
  AND m.anomesconsumo BETWEEN %(anomes_inicio)s AND %(anomes_fim)s
GROUP BY 1, 2, 3, 4;
