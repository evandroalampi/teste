-- Fluxo por loja e hora: cupons distintos da loja (não somáveis a partir de vendas_hora).
SELECT
    m.idvarejista,
    m.idloja,
    date_trunc('hour', m.dataconsumo)                              AS data_hora_local,
    count(DISTINCT concat(m.numerocupom, '|', m.identificacaopdv)) AS n_cupons,
    sum(m.valortotal)                                             AS valor_bruto,
    sum(coalesce(m.valordescontoitem, 0))                         AS valor_desconto
FROM movimentos m
WHERE m.idvarejista IN (%(varejistas)s)
  AND m.anomesconsumo BETWEEN %(anomes_inicio)s AND %(anomes_fim)s
GROUP BY 1, 2, 3;
